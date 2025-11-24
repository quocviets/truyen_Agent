"""
Kaggle runner: pack tokenized JSONL → .pt rồi gọi train_lm.run_training trong một script.

Mặc định kỳ vọng bạn đã upload gói dữ liệu (tạo bằng prepare_kaggle_bundle.py) lên Kaggle.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List, Optional

import torch

try:
    import sentencepiece as spm  # type: ignore
except ImportError:  # pragma: no cover - optional
    spm = None

from .pack_tokenized_dataset import pack_sequences
from .train_lm import run_training
from .utils import ensure_dir, setup_encoding


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="One-click Kaggle training runner.")
    parser.add_argument(
        "--dataset-root",
        type=Path,
        default=Path("/kaggle/input/novel-lm-dataset"),
        help="Thư mục Kaggle dataset đã upload (bundle).",
    )
    parser.add_argument(
        "--config",
        type=Path,
        help="Đường dẫn training_config.json (mặc định: <dataset-root>/config/training_config.json).",
    )
    parser.add_argument(
        "--tokens-dir",
        type=Path,
        help="Thư mục chứa *_tokens.jsonl (mặc định: <dataset-root>/dataset/tokenized).",
    )
    parser.add_argument(
        "--tokenizer-model",
        type=Path,
        help="Đường dẫn SentencePiece .model để xác định pad_id (mặc định: <dataset-root>/tokenizer/sp_model.model).",
    )
    parser.add_argument(
        "--work-dir",
        type=Path,
        default=Path("/kaggle/working"),
        help="Thư mục làm việc trên Kaggle.",
    )
    parser.add_argument(
        "--pack-dir",
        type=Path,
        help="Thư mục lưu .pt (mặc định: <work-dir>/packed_seq_<seq_len>).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Thư mục lưu checkpoint (mặc định: <work-dir>/model_output).",
    )
    parser.add_argument("--seq-len", type=int, default=1024)
    parser.add_argument("--stride", type=int, default=1024)
    parser.add_argument("--drop-remainder", action="store_true")
    parser.add_argument("--include-test", action="store_true", help="Pack thêm test split.")
    parser.add_argument("--skip-pack", action="store_true", help="Bỏ qua bước pack (dùng sẵn .pt).")
    parser.add_argument("--skip-train", action="store_true", help="Chỉ pack, không train.")
    parser.add_argument("--train-bin", type=Path, help="Đường dẫn train .pt nếu skip-pack.")
    parser.add_argument("--val-bin", type=Path, help="Đường dẫn val .pt nếu skip-pack.")
    parser.add_argument("--pad-token-id", type=int, help="Override pad token ID.")
    parser.add_argument("--resume", type=Path, help="Checkpoint để resume training.")
    parser.add_argument("--device", type=str, help="Thiết bị ('cuda', 'cpu', ...).")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--show-progress", action="store_true")
    return parser.parse_args()


def load_training_config(config_path: Path) -> Dict:
    if not config_path.exists():
        raise FileNotFoundError(f"Không tìm thấy config: {config_path}")
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def resolve_pad_id(explicit: Optional[int], cfg: Dict, tokenizer_model: Optional[Path]) -> int:
    if explicit is not None:
        return explicit
    pad_from_cfg = cfg.get("training", {}).get("pad_token_id")
    if pad_from_cfg is not None:
        return pad_from_cfg
    model_path = tokenizer_model
    if model_path and model_path.exists() and spm is not None:
        sp = spm.SentencePieceProcessor(model_file=str(model_path))
        pad_id = sp.pad_id()
        if pad_id >= 0:
            return pad_id
        return sp.unk_id()
    print("⚠️ Không tìm thấy pad_token_id trong config. Dùng mặc định 0.")
    return 0


def pack_if_needed(
    split_names: List[str],
    token_files: Dict[str, Path],
    pack_dir: Path,
    seq_len: int,
    stride: int,
    drop_remainder: bool,
    pad_token_id: int,
    show_progress: bool,
) -> Dict[str, Path]:
    ensure_dir(pack_dir)
    produced: Dict[str, Path] = {}
    for split in split_names:
        input_path = token_files[split]
        if not input_path.exists():
            raise FileNotFoundError(f"Không tìm thấy tokenized JSONL cho split '{split}': {input_path}")
        output_path = pack_dir / f"{split}_{seq_len}.pt"
        print(f"🔁 Packing {split}: {input_path} → {output_path}")
        tensor, stats = pack_sequences(
            input_path=input_path,
            seq_len=seq_len,
            stride=stride,
            drop_remainder=drop_remainder,
            pad_token_id=pad_token_id,
            show_progress=show_progress,
        )
        meta = {
            "num_sequences": tensor.size(0),
            "seq_len": tensor.size(1),
            "split": split,
            "pad_token_id": pad_token_id,
            "stride": stride,
            "drop_remainder": drop_remainder,
            **stats,
        }
        torch.save({"input_ids": tensor, "meta": meta}, output_path)
        produced[split] = output_path
        print(
            f"✅ {split}: {tensor.size(0):,} sequences | total_tokens={stats['total_input_tokens']:,} "
            f"| pad_seq={stats['padded_sequences']}"
        )
    return produced


def main() -> None:
    setup_encoding()
    args = parse_args()

    dataset_root = args.dataset_root
    config_path = args.config or (dataset_root / "config" / "training_config.json")
    cfg = load_training_config(config_path)

    tokens_dir = args.tokens_dir or (dataset_root / "dataset" / "tokenized")
    token_files = {
        "train": tokens_dir / "train_tokens.jsonl",
        "val": tokens_dir / "val_tokens.jsonl",
        "test": tokens_dir / "test_tokens.jsonl",
    }
    tokenizer_model = args.tokenizer_model or (dataset_root / "tokenizer" / "sp_model.model")

    pack_dir = args.pack_dir or (args.work_dir / f"packed_seq_{args.seq_len}")
    output_dir = args.output_dir or (args.work_dir / "model_output")

    pad_token_id = resolve_pad_id(args.pad_token_id, cfg, tokenizer_model)
    print(f"ℹ️ pad_token_id = {pad_token_id}")

    split_names = ["train", "val"]
    if args.include_test:
        split_names.append("test")

    packed_paths: Dict[str, Path] = {}
    if not args.skip_pack:
        packed_paths = pack_if_needed(
            split_names=split_names,
            token_files=token_files,
            pack_dir=pack_dir,
            seq_len=args.seq_len,
            stride=args.stride,
            drop_remainder=args.drop_remainder,
            pad_token_id=pad_token_id,
            show_progress=args.show_progress,
        )
    else:
        print("⚠️ Skip pack enabled. Sẽ dùng đường dẫn .pt do bạn cung cấp.")

    train_bin = args.train_bin or packed_paths.get("train")
    val_bin = args.val_bin or packed_paths.get("val")
    if not train_bin or not val_bin:
        raise ValueError("Thiếu train_bin/val_bin. Cần pack hoặc truyền --train-bin / --val-bin.")

    if args.skip_train:
        print("⏭️ Đã skip training, chỉ thực hiện pack.")
        return

    run_training(
        config_path=config_path,
        train_bin_override=train_bin,
        val_bin_override=val_bin,
        output_dir_override=output_dir,
        resume=args.resume,
        seed=args.seed,
        device_str=args.device,
    )


if __name__ == "__main__":
    main()

