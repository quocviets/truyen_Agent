"""
Script phân tích chất lượng dataset sau bước preprocessing cho pipeline LLM.

Thực hiện 8 bước QA theo yêu cầu:
1. Sanity check số liệu tổng
2. Phân bố độ dài paragraph
3. Phân tích theo từng truyện
4. Kiểm tra noise/hard patterns
5. Phát hiện ký tự không hợp lệ
6. Kiểm tra duplicate paragraphs
7. Spot-check chất lượng nội dung
8. Ước lượng số token

Usage:
    python data_quality_analysis.py \
        --summary-file training/dataset/preprocessed/preprocessing_summary.json \
        --jsonl-file training/dataset/preprocessed/all_novels_preprocessed.jsonl
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import statistics
import unicodedata
from collections import Counter, OrderedDict
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

from .config import Paths
from .utils import read_jsonl, load_json, setup_encoding

# Setup encoding for Windows
setup_encoding()


NOISE_PATTERNS = OrderedDict({
    "http": "http",
    "https": "https",
    "website": "website",
    "nguồn:": "nguồn:",
    "<": "<",
    ">": ">",
    "&nbsp": "&nbsp",
    "&amp": "&amp"
})

BUCKETS = OrderedDict({
    "<50": (0, 50),
    "50-200": (50, 200),
    "200-500": (200, 500),
    "500-1000": (500, 1000),
    "1000-2000": (1000, 2000),
    ">2000": (2000, math.inf)
})

SAMPLE_CONFIG = {
    "short": {"max_len": 200, "size": 6},
    "medium": {"min_len": 200, "max_len": 800, "size": 7},
    "long": {"min_len": 800, "size": 7}
}

# Cache tên Unicode cho ký tự ngoài ASCII để giảm chi phí lookup
UNICODE_NAME_CACHE: Dict[str, str] = {}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="QA dataset sau preprocessing cho training LLM"
    )
    parser.add_argument(
        "--summary-file",
        type=Path,
        default=Paths.PREPROCESSING_SUMMARY_JSON,
        help="Đường dẫn preprocessing_summary.json"
    )
    parser.add_argument(
        "--jsonl-file",
        type=Path,
        default=Paths.ALL_NOVELS_PREPROCESSED_JSONL,
        help="Đường dẫn all_novels_preprocessed.jsonl"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Seed cho random sampling"
    )
    return parser.parse_args()


def load_summary(path: Path) -> Dict:
    """Load preprocessing summary JSON file."""
    return load_json(path)


def percentile(values: List[int], q: float) -> float:
    if not values:
        return 0.0
    k = (len(values) - 1) * q
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return float(values[int(k)])
    d0 = values[int(f)] * (c - k)
    d1 = values[int(c)] * (k - f)
    return float(d0 + d1)


def reservoir_sample(
    storage: List[Tuple[int, str]],
    item: Tuple[int, str],
    capacity: int,
    seen_before: int
) -> None:
    """
    Reservoir sampling đúng chuẩn:
        - seen_before = số phần tử đã thấy trước item hiện tại (i-1)
        - Với phần tử thứ i, random j ∈ [0, i-1]; nếu j < k thì thay
    """
    if len(storage) < capacity:
        storage.append(item)
        return
    idx = random.randint(0, seen_before)
    if idx < capacity:
        storage[idx] = item


def analyze_jsonl(path: Path, seed: int = 42) -> Dict:
    random.seed(seed)
    lengths: List[int] = []
    bucket_counts = Counter()
    noise_counts = Counter()
    control_chars = Counter()
    foreign_chars = Counter()
    duplicate_hashes = set()
    duplicate_count = 0

    samples = {
        "short": [],
        "medium": [],
        "long": []
    }
    sample_seen = {
        "short": 0,
        "medium": 0,
        "long": 0
    }

    for line_idx, data in enumerate(read_jsonl(path), start=1):
        text = data.get("text", "")
            length = len(text)
            lengths.append(length)

            # Bucket
            for bucket_name, (low, high) in BUCKETS.items():
                if low <= length < high:
                    bucket_counts[bucket_name] += 1
                    break

            # Noise patterns
            lower = text.lower()
            for key, pattern in NOISE_PATTERNS.items():
                if pattern in {"<", ">"}:
                    noise_counts[key] += text.count(pattern)
                else:
                    noise_counts[key] += lower.count(pattern)

            # Invalid characters
            for ch in text:
                category = unicodedata.category(ch)
                if category.startswith("C") and ch not in {"\n", "\t", "\r"}:
                    control_chars[ch] += 1
                # Chỉ lookup tên Unicode nếu ký tự ngoài ASCII
                if ord(ch) > 127:
                    if ch not in UNICODE_NAME_CACHE:
                        UNICODE_NAME_CACHE[ch] = unicodedata.name(ch, "")
                    name = UNICODE_NAME_CACHE[ch]
                else:
                    name = ""
                if name and ("CJK" in name or "HIRAGANA" in name or "KATAKANA" in name):
                    foreign_chars[ch] += 1

            # Duplicate detection
            digest = hashlib.sha1(text.encode("utf-8")).hexdigest()
            if digest in duplicate_hashes:
                duplicate_count += 1
            else:
                duplicate_hashes.add(digest)

            # Spot-check samples
            if length < SAMPLE_CONFIG["short"]["max_len"]:
                sample_seen["short"] += 1
                reservoir_sample(
                    samples["short"],
                    (length, text),
                    SAMPLE_CONFIG["short"]["size"],
                    sample_seen["short"] - 1
                )
            elif SAMPLE_CONFIG["medium"]["min_len"] <= length < SAMPLE_CONFIG["medium"]["max_len"]:
                sample_seen["medium"] += 1
                reservoir_sample(
                    samples["medium"],
                    (length, text),
                    SAMPLE_CONFIG["medium"]["size"],
                    sample_seen["medium"] - 1
                )
            else:
                sample_seen["long"] += 1
                reservoir_sample(
                    samples["long"],
                    (length, text),
                    SAMPLE_CONFIG["long"]["size"],
                    sample_seen["long"] - 1
                )

    lengths.sort()
    return {
        "lengths": lengths,
        "bucket_counts": bucket_counts,
        "noise_counts": noise_counts,
        "control_chars": control_chars,
        "foreign_chars": foreign_chars,
        "duplicate_count": duplicate_count,
        "total_paragraphs": len(lengths),
        "samples": samples
    }


def format_bucket_table(bucket_counts: Counter, total: int) -> str:
    lines = ["Bucket độ dài | Số đoạn | Tỷ lệ (%)", "-" * 40]
    for name, (low, high) in BUCKETS.items():
        count = bucket_counts.get(name, 0)
        ratio = (count / total * 100) if total else 0
        lines.append(f"{name:<12} | {count:>7} | {ratio:>6.2f}")
    return "\n".join(lines)


def format_noise_table(noise_counts: Counter, total: int) -> str:
    lines = ["Pattern | Số lần | Tần suất /1k đoạn", "-" * 45]
    for key in NOISE_PATTERNS.keys():
        count = noise_counts.get(key, 0)
        freq = (count / total * 1000) if total else 0
        lines.append(f"{key:<8} | {count:>7} | {freq:>8.2f}")
    return "\n".join(lines)


def describe_samples(samples: Dict[str, List[Tuple[int, str]]]) -> str:
    lines = []
    for label, group in samples.items():
        lines.append(f"- Mẫu {label} ({len(group)} đoạn):")
        for length, text in group:
            preview = text.replace("\n", " ")[:160]
            lines.append(f"    • {length} ký tự → {preview}")
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    summary_path = Path(args.summary_file)
    jsonl_path = Path(args.jsonl_file)

    if not summary_path.exists():
        raise FileNotFoundError(f"Không tìm thấy summary file: {summary_path}")
    if not jsonl_path.exists():
        raise FileNotFoundError(f"Không tìm thấy jsonl file: {jsonl_path}")

    summary = load_summary(summary_path)
    jsonl_stats = analyze_jsonl(jsonl_path, seed=args.seed)

    total_chapters = summary["statistics"]["total_chapters"]
    processed_chapters = summary["statistics"]["processed_chapters"]
    filtered_chapters = summary["statistics"]["filtered_chapters"]
    total_paragraphs = summary["statistics"]["total_paragraphs"]
    total_chars = summary["statistics"]["total_chars"]

    chapter_filter_ratio = (filtered_chapters / total_chapters) * 100 if total_chapters else 0

    lengths = jsonl_stats["lengths"]
    mean_len = statistics.mean(lengths) if lengths else 0
    median_len = statistics.median(lengths) if lengths else 0
    std_len = statistics.pstdev(lengths) if lengths else 0
    min_len = lengths[0] if lengths else 0
    max_len = lengths[-1] if lengths else 0

    percentiles = {
        "P10": percentile(lengths, 0.10),
        "P25": percentile(lengths, 0.25),
        "P50": percentile(lengths, 0.50),
        "P75": percentile(lengths, 0.75),
        "P90": percentile(lengths, 0.90),
        "P95": percentile(lengths, 0.95),
        "P99": percentile(lengths, 0.99),
    }

    duplicate_ratio = (jsonl_stats["duplicate_count"] / total_paragraphs * 100) if total_paragraphs else 0
    estimated_tokens = total_chars / 3.5 if total_chars else 0

    print("=" * 80)
    print("BẢNG TỔNG HỢP CHẤT LƯỢNG DATASET")
    print("=" * 80)
    print(f"- Tổng truyện: {summary['statistics']['total_novels']}")
    print(f"- Tổng chương: {total_chapters} (processed {processed_chapters}, filtered {filtered_chapters} → {chapter_filter_ratio:.3f}%)")
    print(f"- Tổng đoạn: {total_paragraphs}")
    print(f"- Tổng ký tự: {total_chars:,}")
    print(f"- Ước lượng tokens: {estimated_tokens:,.0f}")
    print()

    print("1) SANITY CHECK SỐ LIỆU TỔNG")
    print(f"   • Filter ratio: {chapter_filter_ratio:.3f}%")
    print(f"   • Có mất dữ liệu? {'Không' if processed_chapters == total_chapters - filtered_chapters else 'Cần kiểm tra thêm'}")
    print()

    print("2) PHÂN PHỐ ĐỘ DÀI PARAGRAPH")
    print(f"   • Min/Max: {min_len} / {max_len}")
    print(f"   • Mean/Median/Std: {mean_len:.2f} / {median_len:.2f} / {std_len:.2f}")
    percents_desc = ", ".join(f"{k}={v:.0f}" for k, v in percentiles.items())
    print(f"   • Percentiles: {percents_desc}")
    print(format_bucket_table(jsonl_stats["bucket_counts"], total_paragraphs))
    print("   (Bucket >2000 dự kiến ≈0 vì preprocessing đã clamp 2,000 ký tự)")
    print()

    print("3) PHÂN TÍCH THEO TỪNG TRUYỆN")
    print("   novel | total_chapters | processed | filtered | avg_chars_per_chapter")
    for name, stats in summary["novels"].items():
        print(f"   {name:<45} {stats['total_chapters']:>6} {stats['processed_chapters']:>10} {stats['filtered_chapters']:>8} {stats['avg_chars_per_chapter']:>12.0f}")
    summary_total = summary["statistics"]["total_paragraphs"]
    jsonl_total = jsonl_stats["total_paragraphs"]
    if summary_total != jsonl_total:
        print(f"   ⚠️  Sai lệch total_paragraphs: summary={summary_total}, jsonl={jsonl_total}")
    else:
        print("   ✓ Tổng số đoạn khớp giữa summary và JSONL")
    print()

    print("4) KIỂM TRA NOISE / HARD PATTERNS")
    print(format_noise_table(jsonl_stats["noise_counts"], total_paragraphs))
    print()

    print("5) KÝ TỰ KHÔNG HỢP LỆ")
    control_total = sum(jsonl_stats["control_chars"].values())
    foreign_total = sum(jsonl_stats["foreign_chars"].values())
    print(f"   • Control chars: {control_total} (ví dụ: {list(jsonl_stats['control_chars'].items())[:5]})")
    print(f"   • Foreign chars: {foreign_total} (ví dụ: {list(jsonl_stats['foreign_chars'].items())[:5]})")
    print()

    print("6) DUPLICATE PARAGRAPHS")
    print(f"   • Số đoạn trùng: {jsonl_stats['duplicate_count']} ({duplicate_ratio:.2f}%)")
    print()

    print("7) SPOT-CHECK NỘI DUNG (20 đoạn)")
    print(describe_samples(jsonl_stats["samples"]))
    print()

    print("8) ƯỚC LƯỢNG TOKENS & PHÙ HỢP MODEL")
    print(f"   • Ước lượng tổng tokens: {estimated_tokens:,.0f}")
    print("   • Phù hợp để train model cỡ 1-3B (fine-tune) hoặc dùng làm tập bổ sung cho 7B tùy mục tiêu.")
    print()

    warnings = []
    if chapter_filter_ratio > 1:
        warnings.append("Tỷ lệ chương bị lọc >1%")
    if jsonl_stats["noise_counts"].get("http", 0) > 0:
        warnings.append("Có xuất hiện pattern 'http' → cần kiểm tra nguồn")
    if duplicate_ratio > 5:
        warnings.append("Tỷ lệ duplicate >5%")
    if sum(jsonl_stats["foreign_chars"].values()) > 0:
        warnings.append("Xuất hiện ký tự ngoài bộ chữ Latin (CJK/Hiragana/Katakana)")

    print("DANH SÁCH CẢNH BÁO")
    if warnings:
        for idx, warn in enumerate(warnings, 1):
            print(f"   {idx}. {warn}")
    else:
        print("   • Không có cảnh báo nghiêm trọng")
    print()

    if not warnings:
        conclusion = "Dataset đạt chuẩn để train LLM (ở mức fine-tune)."
    else:
        conclusion = "Dataset cần kiểm tra thêm trước khi train LLM."
    print("KẾT LUẬN CUỐI CÙNG")
    print(f"   {conclusion}")
    if warnings:
        print("   Lý do:", "; ".join(warnings))
    print()

    print("GỢI Ý CẢI THIỆN")
    print("   • Bổ sung bước kiểm tra noise tự động (regex) trước khi tokenize.")
    print("   • Lưu danh sách chương bị filter để review thủ công.")
    print("   • Kiểm tra thêm các ký tự nước ngoài (nếu có) và quyết định giữ hoặc loại.")


if __name__ == "__main__":
    main()

