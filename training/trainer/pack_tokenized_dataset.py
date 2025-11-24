"""
Pack tokenized JSONL paragraphs thành fixed-length sequence tensors (.pt).

Sử dụng khi chuẩn bị dữ liệu cho training loop trên Kaggle (hoặc môi trường GPU).

Ví dụ:
    python -m training.trainer.pack_tokenized_dataset \
        --input training/dataset/tokenized/train_tokens.jsonl \
        --output training/dataset/tokenized/train_1024.pt \
        --seq-len 1024 \
        --stride 1024 \
        --show-progress
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import torch
from tqdm import tqdm

try:
    import sentencepiece as spm  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    spm = None

from .utils import ensure_dir, setup_encoding


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Pack tokenized JSONL vào fixed-length tensor (.pt)."
    )
    parser.add_argument(
        "--input",
        type=Path,
        required=True,
        help="Đường dẫn JSONL chứa token IDs (từ tokenize_dataset.py).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Đường dẫn file .pt sẽ lưu tensor packed sequences.",
    )
    parser.add_argument(
        "--seq-len",
        type=int,
        default=1024,
        help="Chiều dài sequence cố định (mặc định: 1024).",
    )
    parser.add_argument(
        "--stride",
        type=int,
        default=1024,
        help="Số token dịch mỗi lần cắt (mặc định = seq_len, tức là không overlap).",
    )
    parser.add_argument(
        "--drop-remainder",
        action="store_true",
        help="Bỏ phần dư cuối cùng nếu chưa đủ seq_len (mặc định: giữ và padding).",
    )
    parser.add_argument(
        "--pad-token-id",
        type=int,
        default=None,
        help="Token ID dùng để padding nếu giữ remainder. Nếu không cung cấp sẽ "
        "cố gắng đọc từ tokenizer SentencePiece (nếu chỉ định).",
    )
    parser.add_argument(
        "--tokenizer-model",
        type=Path,
        default=None,
        help="Đường dẫn SentencePiece .model (nếu muốn auto lấy pad_id).",
    )
    parser.add_argument(
        "--show-progress",
        action="store_true",
        help="Hiển thị progress bar khi đọc file JSONL.",
    )
    return parser.parse_args()


def pack_sequences(
    input_path: Path,
    seq_len: int,
    stride: int,
    drop_remainder: bool,
    pad_token_id: int,
    show_progress: bool,
) -> Tuple[torch.Tensor, Dict[str, int]]:
    """Đọc JSONL token IDs và pack thành tensor cố định."""
    if stride <= 0:
        print(f"⚠️ stride={stride} không hợp lệ. Auto set = seq_len ({seq_len}).")
        stride = seq_len
    if stride > seq_len:
        stride = seq_len
    elif stride < seq_len:
        print(
            f"⚠️ stride ({stride}) < seq_len ({seq_len}). "
            "Bạn đang bật chế độ sliding window (overlap)."
        )

    stats = {
        "total_input_tokens": 0,
        "total_output_sequences": 0,
        "invalid_records": 0,
        "empty_records": 0,
        "padded_sequences": 0,
        "dropped_tokens": 0,
    }

    sequences: List[List[int]] = []
    buffer: List[int] = []

    open_kwargs = {"encoding": "utf-8"}

    def iter_lines():
        with open(input_path, "r", **open_kwargs) as f:
            for line in f:
                yield line

    iterator = iter_lines()
    if show_progress:
        with open(input_path, "r", **open_kwargs) as f:
            line_count = sum(1 for _ in f)
        iterator = tqdm(iter_lines(), total=line_count, desc=f"Packing {input_path.name}")

    for line in iterator:
        if not line.strip():
            continue
        record = json.loads(line)
        token_ids = record.get("input_ids")
        if token_ids is None:
            stats["invalid_records"] += 1
            continue
        if not isinstance(token_ids, list):
            stats["invalid_records"] += 1
            continue
        if not token_ids:
            stats["empty_records"] += 1
            continue
        if not all(isinstance(tid, int) for tid in token_ids):
            stats["invalid_records"] += 1
            continue

        stats["total_input_tokens"] += len(token_ids)
        buffer.extend(token_ids)
        while len(buffer) >= seq_len:
            chunk = buffer[:seq_len]
            sequences.append(chunk)
            buffer = buffer[stride:]

    if buffer and not drop_remainder:
        if len(buffer) < max(8, seq_len // 8):
            print(
                f"⚠️ Remainder nhỏ ({len(buffer)} tokens). Padding gần full sequence có thể gây nhiễu."
            )
        padded = buffer + [pad_token_id] * (seq_len - len(buffer))
        sequences.append(padded[:seq_len])
        stats["padded_sequences"] += 1
    elif buffer and drop_remainder:
        stats["dropped_tokens"] += len(buffer)

    if not sequences:
        raise ValueError("Không tạo được sequence nào. Kiểm tra seq_len/stride hoặc dữ liệu đầu vào.")

    tensor = torch.tensor(sequences, dtype=torch.long)
    stats["total_output_sequences"] = tensor.size(0)
    return tensor, stats


def main() -> None:
    setup_encoding()
    args = parse_args()

    if not args.input.exists():
        raise FileNotFoundError(f"Không tìm thấy file input: {args.input}")

    ensure_dir(args.output.parent)

    pad_token_id: Optional[int] = args.pad_token_id
    tokenizer_meta: Dict[str, str] = {}

    if pad_token_id is None and args.tokenizer_model:
        if spm is None:
            print(
                "⚠️ Không tìm thấy sentencepiece. Cài sentencepiece hoặc truyền --pad-token-id."
            )
        else:
            sp = spm.SentencePieceProcessor(model_file=str(args.tokenizer_model))
            pad_id = sp.pad_id()
            unk_id = sp.unk_id()
            if pad_id >= 0:
                pad_token_id = pad_id
                tokenizer_meta["pad_id_source"] = "sentencepiece_pad"
            else:
                pad_token_id = unk_id
                tokenizer_meta["pad_id_source"] = "sentencepiece_unk"
                print("⚠️ Tokenizer không có pad_id. Đang dùng tạm unk_id để padding.")
            if pad_token_id == unk_id:
                print(
                    f"⚠️ pad_token_id={pad_token_id} trùng unk_id. "
                    "Hãy cân nhắc bổ sung <pad> khi train tokenizer."
                )

    if pad_token_id is None:
        pad_token_id = 0
        tokenizer_meta["pad_id_source"] = "default_zero"
        print(
            "⚠️ pad_token_id không được cung cấp. Đang fallback về 0 (thường là <unk>). "
            "Nên truyền giá trị rõ ràng để tránh nhiễu."
        )

    print(f"🔁 Packing {args.input} → {args.output}")

    tensor, stats = pack_sequences(
        input_path=args.input,
        seq_len=args.seq_len,
        stride=args.stride,
        drop_remainder=args.drop_remainder,
        pad_token_id=pad_token_id,
        show_progress=args.show_progress,
    )

    meta = {
        "num_sequences": tensor.size(0),
        "seq_len": tensor.size(1),
        "stride": args.stride,
        "drop_remainder": args.drop_remainder,
        "pad_token_id": pad_token_id,
        "source": str(args.input),
        **stats,
        **tokenizer_meta,
    }

    torch.save({"input_ids": tensor, "meta": meta}, args.output)
    print(
        f"✅ Done. Saved {tensor.size(0):,} sequences of length {tensor.size(1)} "
        f"→ {args.output}"
    )


if __name__ == "__main__":
    main()

