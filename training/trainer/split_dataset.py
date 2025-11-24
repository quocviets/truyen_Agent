"""
Chia dataset per-chapter 90/5/5 cho train/val/test dựa trên dữ liệu đã sạch.

Chiến lược:
    1. Đọc all_novels_preprocessed_clean.jsonl (đã QA + clean noise).
    2. Duyệt từng novel trong thư mục raw, chạy lại pipeline cleaning để biết
       số paragraph hợp lệ của từng chapter (không ghi file mới).
    3. Ánh xạ các paragraph đã clean sang chapter tương ứng bằng cách chia theo counts.
    4. Với mỗi novel, shuffle danh sách chapter bằng seed cố định rồi chia
       90/5/5 (train/val/test).
    5. Ghi ra 3 file JSONL + summary cho từng split + tổng hợp chung.

Yêu cầu:
    python training/trainer/split_dataset.py \
        --input-jsonl training/dataset/preprocessed/all_novels_preprocessed_clean.jsonl \
        --raw-dir training/dataset/raw/truyenmoiii_output \
        --output-dir training/dataset/splits
"""

from __future__ import annotations

import argparse
import json
import math
import random
import re
from collections import defaultdict, OrderedDict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

from .preprocessing import Preprocessor
from .config import Paths, SplitConfig, CleaningLevel
from .utils import read_jsonl as read_jsonl_util, write_jsonl as write_jsonl_util, save_json, setup_encoding

# Setup encoding for Windows
setup_encoding()


@dataclass
class ChapterInfo:
    chapter_index: int
    paragraph_count: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Split dataset per chapter 90/5/5")
    parser.add_argument(
        "--input-jsonl",
        type=Path,
        default=Paths.ALL_NOVELS_PREPROCESSED_CLEAN_JSONL,
        help="File JSONL đã clean"
    )
    parser.add_argument(
        "--raw-dir",
        type=Path,
        default=Paths.RAW_DIR,
        help="Thư mục raw chứa chapter_*.txt"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Paths.SPLITS_DIR,
        help="Thư mục ghi train/val/test JSONL"
    )
    parser.add_argument(
        "--train-ratio",
        type=float,
        default=0.9,
        help="Tỷ lệ chapter cho train"
    )
    parser.add_argument(
        "--val-ratio",
        type=float,
        default=0.05,
        help="Tỷ lệ chapter cho validation"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Seed shuffle chapter"
    )
    return parser.parse_args()


CHAPTER_PATTERN = re.compile(r'chapter_(\d+)', re.IGNORECASE)


def extract_chapter_number(path: Path) -> int:
    match = CHAPTER_PATTERN.search(path.name)
    if not match:
        raise ValueError(f"Không tìm thấy chapter index trong {path}")
    return int(match.group(1))


def compute_chapter_counts(
    preprocessor: Preprocessor,
    novel_dir: Path
) -> List[ChapterInfo]:
    chapter_files = list(novel_dir.glob("chapter_*.txt"))
    if not chapter_files:
        return []
    chapter_files.sort(key=lambda p: extract_chapter_number(p))

    # Tính avg size giống process_novel
    sizes = []
    for cf in chapter_files:
        try:
            sizes.append(cf.stat().st_size)
        except OSError:
            continue
    avg_size = sum(sizes) / len(sizes) if sizes else 0

    chapter_counts: List[ChapterInfo] = []
    for cf in chapter_files:
        chapter_idx = extract_chapter_number(cf)
        try:
            raw_content = cf.read_text(encoding="utf-8")
        except Exception:
            continue

        cleaned = preprocessor.clean_text(raw_content)
        paragraphs = preprocessor.split_into_paragraphs(cleaned)
        valid_paragraphs = preprocessor.filter_valid_paragraphs(paragraphs)
        if not valid_paragraphs:
            continue

        should_filter, _ = preprocessor.should_filter_chapter(
            cleaned, valid_paragraphs, avg_size
        )
        if should_filter:
            continue

        chapter_counts.append(
            ChapterInfo(chapter_index=chapter_idx, paragraph_count=len(valid_paragraphs))
        )

    return chapter_counts


def load_clean_records(jsonl_path: Path) -> Dict[str, List[Dict]]:
    data: Dict[str, List[Dict]] = OrderedDict()
    with jsonl_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            novel = obj["novel_name"]
            data.setdefault(novel, []).append(obj)
    return data


def determine_split_counts(num: int, train_ratio: float, val_ratio: float) -> Tuple[int, int, int]:
    if num <= 0:
        return 0, 0, 0
    train = max(1, int(num * train_ratio))
    val = max(1, int(num * val_ratio))
    if train + val >= num:
        val = max(1, min(val, num - 1))
        train = max(1, num - val - 1)
    test = num - train - val
    if test <= 0:
        # Lấy lại từ các split khác
        if train > val and train > 1:
            train -= 1
        elif val > 1:
            val -= 1
        else:
            train = max(1, train)
        test = num - train - val
    return train, val, test


def write_jsonl(path: Path, records: List[Dict]) -> None:
    """Ghi records vào file JSONL (wrapper cho utils.write_jsonl)."""
    write_jsonl_util(path, iter(records))


def build_split_summary(split_name: str, stats: Dict) -> Dict:
    total_chapters = stats["total_chapters"]
    total_paragraphs = stats["total_paragraphs"]
    total_chars = stats["total_chars"]
    total_bytes = stats["total_bytes"]
    processed = total_chapters
    filtered = 0

    novel_entries = {}
    for novel, info in stats["novels"].items():
        chapters = info["chapters"]
        paragraphs = info["paragraphs"]
        chars = info["chars"]
        bytes_len = info["bytes"]
        novel_entries[novel] = {
            "novel_name": novel,
            "total_chapters": chapters,
            "processed_chapters": chapters,
            "filtered_chapters": 0,
            "total_paragraphs": paragraphs,
            "total_chars": chars,
            "total_bytes": bytes_len,
            "avg_chars_per_chapter": (chars / chapters) if chapters else 0,
            "avg_chars_per_paragraph": (chars / paragraphs) if paragraphs else 0
        }

    summary = {
        "split": split_name,
        "statistics": {
            "total_novels": len(stats["novels"]),
            "total_chapters": total_chapters,
            "processed_chapters": processed,
            "filtered_chapters": filtered,
            "total_paragraphs": total_paragraphs,
            "total_chars": total_chars,
            "total_bytes": total_bytes
        },
        "novels": novel_entries
    }
    return summary


def main() -> None:
    args = parse_args()
    input_path = Path(args.input_jsonl)
    raw_dir = Path(args.raw_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    clean_records = load_clean_records(input_path)

    preprocessor = Preprocessor(
        raw_dir=str(raw_dir),
        output_dir="training/dataset/preprocessed",
        cleaning_level=CleaningLevel.BALANCED,
    )

    rng = random.Random(args.seed)

    splits_payload = {"train": [], "val": [], "test": []}
    split_stats = {
        "train": {"total_chapters": 0, "total_paragraphs": 0, "total_chars": 0, "total_bytes": 0, "novels": defaultdict(lambda: {"chapters": 0, "paragraphs": 0, "chars": 0, "bytes": 0})},
        "val": {"total_chapters": 0, "total_paragraphs": 0, "total_chars": 0, "total_bytes": 0, "novels": defaultdict(lambda: {"chapters": 0, "paragraphs": 0, "chars": 0, "bytes": 0})},
        "test": {"total_chapters": 0, "total_paragraphs": 0, "total_chars": 0, "total_bytes": 0, "novels": defaultdict(lambda: {"chapters": 0, "paragraphs": 0, "chars": 0, "bytes": 0})},
    }

    for novel_name, paragraphs in clean_records.items():
        novel_dir = raw_dir / novel_name
        if not novel_dir.exists():
            raise FileNotFoundError(f"Không tìm thấy thư mục raw cho {novel_name}")

        chapter_counts = compute_chapter_counts(preprocessor, novel_dir)
        if not chapter_counts:
            continue

        total_expected = sum(ci.paragraph_count for ci in chapter_counts)
        if total_expected != len(paragraphs):
            raise ValueError(
                f"Số paragraph không khớp cho {novel_name}: expected {total_expected}, actual {len(paragraphs)}"
            )

        chapters_payload = []
        cursor = 0
        for ci in chapter_counts:
            chunk = paragraphs[cursor:cursor + ci.paragraph_count]
            cursor += ci.paragraph_count
            chapters_payload.append({
                "chapter_index": ci.chapter_index,
                "paragraphs": chunk
            })

        rng.shuffle(chapters_payload)

        train_ct, val_ct, test_ct = determine_split_counts(
            len(chapters_payload), args.train_ratio, args.val_ratio
        )
        splits = {
            "train": chapters_payload[:train_ct],
            "val": chapters_payload[train_ct:train_ct + val_ct],
            "test": chapters_payload[train_ct + val_ct:]
        }

        for split_name, chapter_list in splits.items():
            if not chapter_list:
                continue
            payload = splits_payload[split_name]
            stats_bucket = split_stats[split_name]
            novel_bucket = stats_bucket["novels"][novel_name]
            for chapter in chapter_list:
                stats_bucket["total_chapters"] += 1
                novel_bucket["chapters"] += 1
                paragraphs_in_chapter = chapter["paragraphs"]
                for idx, rec in enumerate(paragraphs_in_chapter):
                    new_rec = {
                        "text": rec["text"],
                        "novel_name": novel_name,
                        "chapter_index": chapter["chapter_index"],
                        "paragraph_index_in_chapter": idx,
                        "original_paragraph_index": rec.get("paragraph_index"),
                        "global_paragraph_index": rec.get("global_paragraph_index")
                    }
                    payload.append(new_rec)
                    stats_bucket["total_paragraphs"] += 1
                    stats_bucket["total_chars"] += len(rec["text"])
                    stats_bucket["total_bytes"] += len(rec["text"].encode("utf-8"))
                    novel_bucket["paragraphs"] += 1
                    novel_bucket["chars"] += len(rec["text"])
                    novel_bucket["bytes"] += len(rec["text"].encode("utf-8"))

    # Write outputs
    train_path = output_dir / "train.jsonl"
    val_path = output_dir / "val.jsonl"
    test_path = output_dir / "test.jsonl"
    write_jsonl(train_path, splits_payload["train"])
    write_jsonl(val_path, splits_payload["val"])
    write_jsonl(test_path, splits_payload["test"])

    # Summary files
    summaries = {}
    for split_name in ("train", "val", "test"):
        summary_dict = build_split_summary(split_name, split_stats[split_name])
        summaries[split_name] = summary_dict
        with (output_dir / f"{split_name}_summary.json").open("w", encoding="utf-8") as f:
            json.dump(summary_dict, f, ensure_ascii=False, indent=2)

    # Global summary
    global_summary = {
        "splits": summaries,
        "notes": {
            "method": "per-chapter split 90/5/5",
            "seed": args.seed,
            "train_ratio": args.train_ratio,
            "val_ratio": args.val_ratio
        }
    }
    with (output_dir / "splits_summary.json").open("w", encoding="utf-8") as f:
        json.dump(global_summary, f, ensure_ascii=False, indent=2)

    total_input = sum(len(v) for v in clean_records.values())
    total_output = sum(
        split_stats[split]["total_paragraphs"] for split in ("train", "val", "test")
    )
    if total_input != total_output:
        raise ValueError(f"Mismatch total paragraphs: input={total_input}, output={total_output}")

    novels_without_val = []
    novels_without_test = []
    for novel, chapter_counts in clean_records.items():
        # Check per novel splits
        train_ch = split_stats["train"]["novels"][novel]["chapters"] if novel in split_stats["train"]["novels"] else 0
        val_ch = split_stats["val"]["novels"][novel]["chapters"] if novel in split_stats["val"]["novels"] else 0
        test_ch = split_stats["test"]["novels"][novel]["chapters"] if novel in split_stats["test"]["novels"] else 0
        if val_ch == 0:
            novels_without_val.append(novel)
        if test_ch == 0:
            novels_without_test.append(novel)

    print("✅ Đã chia xong dataset:")
    for split_name in ("train", "val", "test"):
        stats = split_stats[split_name]
        print(
            f"  [{split_name}] chapters={stats['total_chapters']:,} | paragraphs={stats['total_paragraphs']:,} | chars={stats['total_chars']:,}"
        )
    if novels_without_val:
        print(f"  ⚠️ Novels không có val chapter: {', '.join(novels_without_val)}")
    if novels_without_test:
        print(f"  ⚠️ Novels không có test chapter: {', '.join(novels_without_test)}")


if __name__ == "__main__":
    main()

