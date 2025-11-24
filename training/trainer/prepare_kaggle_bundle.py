"""
Tạo gói dữ liệu chuẩn để upload lên Kaggle (config + tokenizer + splits + tokenized).

Script này gom các file cần thiết vào một thư mục duy nhất, kèm manifest,
và (tuỳ chọn) nén thành .zip để tải lên Kaggle dataset.
"""

from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

from .config import Paths
from .utils import ensure_dir, setup_encoding


CORE_ITEMS: Dict[str, Path] = {
    "config/training_config.json": Paths.ROOT / "training" / "configs" / "training_config.json",
    "tokenizer/sp_model.model": Paths.TOKENIZER_MODEL,
    "tokenizer/sp_model.vocab": Paths.TOKENIZER_VOCAB,
    "tokenizer/tokenizer_info.json": Paths.TOKENIZER_INFO_JSON,
    "dataset/splits/train.jsonl": Paths.TRAIN_JSONL,
    "dataset/splits/val.jsonl": Paths.VAL_JSONL,
    "dataset/splits/test.jsonl": Paths.TEST_JSONL,
    "dataset/tokenized/train_tokens.jsonl": Paths.TOKENIZED_DIR / "train_tokens.jsonl",
    "dataset/tokenized/val_tokens.jsonl": Paths.TOKENIZED_DIR / "val_tokens.jsonl",
    "dataset/tokenized/test_tokens.jsonl": Paths.TOKENIZED_DIR / "test_tokens.jsonl",
}

REPORT_ITEMS: Dict[str, Path] = {
    "reports/preprocessing_summary.json": Paths.PREPROCESSING_SUMMARY_JSON,
    "reports/clean_noise_report.json": Paths.CLEAN_NOISE_REPORT_JSON,
    "reports/train_summary.json": Paths.TRAIN_SUMMARY_JSON,
    "reports/val_summary.json": Paths.VAL_SUMMARY_JSON,
    "reports/test_summary.json": Paths.TEST_SUMMARY_JSON,
    "reports/splits_summary.json": Paths.SPLITS_SUMMARY_JSON,
}

PREPROCESSED_ITEMS: Dict[str, Path] = {
    "dataset/preprocessed/all_novels_preprocessed_clean.jsonl": Paths.ALL_NOVELS_PREPROCESSED_CLEAN_JSONL,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Gom dữ liệu thành gói upload Kaggle.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Paths.ROOT / "training" / "kaggle_bundle",
        help="Thư mục đích (sẽ được tạo nếu chưa tồn tại).",
    )
    parser.add_argument(
        "--include-reports",
        action="store_true",
        help="Thêm các file thống kê QA (preprocessing_summary, splits_summary...).",
    )
    parser.add_argument(
        "--include-preprocessed",
        action="store_true",
        help="Thêm file all_novels_preprocessed_clean.jsonl (dự phòng).",
    )
    parser.add_argument(
        "--include-extra",
        action="append",
        type=Path,
        help="Thêm các file/path tuỳ chọn khác (repeat flag nhiều lần).",
    )
    parser.add_argument(
        "--zip",
        action="store_true",
        help="Nén toàn bộ output-dir thành .zip sau khi copy xong.",
    )
    parser.add_argument(
        "--manifest-name",
        type=str,
        default="bundle_manifest.json",
        help="Tên file manifest (JSON) ghi lại các file đã copy.",
    )
    return parser.parse_args()


def copy_items(pairs: Dict[str, Path], output_dir: Path) -> Tuple[Dict[str, str], List[str]]:
    copied: Dict[str, str] = {}
    missing: List[str] = []
    for rel_path, src in pairs.items():
        if not src.exists():
            print(f"⚠️ Bỏ qua (không tìm thấy) {src}")
            missing.append(rel_path)
            continue
        dest = output_dir / rel_path
        ensure_dir(dest.parent)
        shutil.copy2(src, dest)
        copied[rel_path] = str(src)
        print(f"✅ Copied {src} → {dest}")
    return copied, missing


def write_manifest(output_dir: Path, manifest_name: str, copied: Dict[str, str], missing: List[str]) -> None:
    manifest_path = output_dir / manifest_name
    payload = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "root": str(output_dir),
        "copied": copied,
        "missing": missing,
    }
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"📝 Manifest saved to {manifest_path}")


def maybe_zip(output_dir: Path) -> Path:
    archive_path = shutil.make_archive(str(output_dir), "zip", root_dir=output_dir)
    print(f"📦 Created archive: {archive_path}")
    return Path(archive_path)


def main() -> None:
    setup_encoding()
    args = parse_args()
    ensure_dir(args.output_dir)

    copied: Dict[str, str] = {}
    missing: List[str] = []

    core_copied, core_missing = copy_items(CORE_ITEMS, args.output_dir)
    copied.update(core_copied)
    missing.extend(core_missing)

    if args.include_reports:
        report_copied, report_missing = copy_items(REPORT_ITEMS, args.output_dir)
        copied.update(report_copied)
        missing.extend(report_missing)

    if args.include_preprocessed:
        preproc_copied, preproc_missing = copy_items(PREPROCESSED_ITEMS, args.output_dir)
        copied.update(preproc_copied)
        missing.extend(preproc_missing)

    if args.include_extra:
        for extra in args.include_extra:
            if not extra.exists():
                print(f"⚠️ Extra path not found: {extra}")
                missing.append(f"extra::{extra}")
                continue
            rel = extra.name if extra.is_file() else extra.name + "/"
            dest = args.output_dir / "extra" / rel
            if extra.is_file():
                ensure_dir(dest.parent)
                shutil.copy2(extra, dest)
            else:
                shutil.copytree(extra, dest, dirs_exist_ok=True)
            copied[f"extra/{rel}"] = str(extra)
            print(f"➕ Added extra {extra} → {dest}")

    write_manifest(args.output_dir, args.manifest_name, copied, missing)

    if args.zip:
        maybe_zip(args.output_dir)


if __name__ == "__main__":
    main()

