"""
Script làm sạch noise (URL, website, HTML residue) và ký tự ngoại lai
trong file JSONL paragraph sau preprocessing.

Usage:
    python clean_noise.py \
        --input training/dataset/preprocessed/all_novels_preprocessed.jsonl \
        --output training/dataset/preprocessed/all_novels_preprocessed_clean.jsonl \
        --report training/dataset/preprocessed/clean_noise_report.json
"""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from pathlib import Path
from typing import Dict, Tuple

from .config import Paths, CleanNoiseConfig
from .utils import read_jsonl, write_jsonl, save_json, setup_encoding

# Setup encoding for Windows
setup_encoding()


URL_PATTERN = re.compile(r'https?://\S+', re.IGNORECASE)
BARE_HTTP_PATTERN = re.compile(r'\bhttps?\b', re.IGNORECASE)
WEBSITE_PATTERN = re.compile(r'\bwebsite\b', re.IGNORECASE)
NGUON_PATTERN = re.compile(r'nguồn[:：]\s*[^\n]+', re.IGNORECASE)
NGUON_PATTERN_ASCII = re.compile(r'nguon[:：]\s*[^\n]+', re.IGNORECASE)
WHITESPACE_PATTERN = re.compile(r'[ \t]+')

HTML_TAG_PATTERN = re.compile(r'<[^>]+>')
HTML_ENTITY_MAP = {
    '&nbsp;': ' ',
    '&amp;': '&'
}

# Các block unicode cần loại bỏ
FOREIGN_KEYWORDS = ("CJK", "HIRAGANA", "KATAKANA")
UNICODE_NAME_CACHE: Dict[str, str] = {}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Clean noise/foreign chars khỏi JSONL")
    parser.add_argument(
        "--input",
        type=Path,
        default=Paths.ALL_NOVELS_PREPROCESSED_JSONL,
        help="File JSONL đầu vào"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Paths.ALL_NOVELS_PREPROCESSED_CLEAN_JSONL,
        help="File JSONL sau khi làm sạch"
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=Paths.CLEAN_NOISE_REPORT_JSON,
        help="File JSON report thống kê"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Chỉ thống kê, không ghi file output"
    )
    return parser.parse_args()


def remove_foreign_chars(text: str) -> Tuple[str, int]:
    """Loại bỏ ký tự thuộc block CJK/Hiragana/Katakana."""
    removed = 0
    result_chars = []
    for ch in text:
        if ord(ch) <= 127:
            result_chars.append(ch)
            continue
        if ch not in UNICODE_NAME_CACHE:
            UNICODE_NAME_CACHE[ch] = unicodedata.name(ch, "")
        name = UNICODE_NAME_CACHE[ch]
        if name and any(key in name for key in FOREIGN_KEYWORDS):
            removed += 1
            continue
        result_chars.append(ch)
    return "".join(result_chars), removed


def normalize_whitespace_preserve_newlines(text: str) -> str:
    """Chuẩn hóa space/tab nhưng giữ nguyên cấu trúc xuống dòng."""
    lines = text.splitlines()
    normalized = []
    for line in lines:
        # Giữ nguyên thứ tự, chỉ gộp nhiều space/tab liên tiếp
        normalized_line = WHITESPACE_PATTERN.sub(' ', line.strip())
        normalized.append(normalized_line)
    return "\n".join(normalized).strip()


def clean_text(text: str, stats: Dict[str, int]) -> Tuple[str, bool]:
    """
    Làm sạch 1 paragraph.
    Returns: (clean_text, changed_flag)
    """
    original = text
    changed = False

    # Entities
    for src, dst in HTML_ENTITY_MAP.items():
        if src in text:
            stats['html_entities'] += text.count(src)
            text = text.replace(src, dst)
            changed = True

    # Remove URLs
    if URL_PATTERN.search(text):
        count = len(URL_PATTERN.findall(text))
        text = URL_PATTERN.sub('', text)
        stats['urls_removed'] += count
        changed = True
    # Remove từ khóa http/https còn sót lại
    if BARE_HTTP_PATTERN.search(text):
        count = len(BARE_HTTP_PATTERN.findall(text))
        text = BARE_HTTP_PATTERN.sub('', text)
        stats['bare_http_removed'] += count
        changed = True

    # Remove "Nguồn: ..." patterns
    if NGUON_PATTERN.search(text):
        count = len(NGUON_PATTERN.findall(text))
        text = NGUON_PATTERN.sub('', text)
        stats['nguon_removed'] += count
        changed = True
    elif NGUON_PATTERN_ASCII.search(text):
        count = len(NGUON_PATTERN_ASCII.findall(text))
        text = NGUON_PATTERN_ASCII.sub('', text)
        stats['nguon_removed'] += count
        changed = True

    # Remove literal "website"
    if WEBSITE_PATTERN.search(text):
        count = len(WEBSITE_PATTERN.findall(text))
        text = WEBSITE_PATTERN.sub('', text)
        stats['website_removed'] += count
        changed = True

    # Remove HTML tags
    if HTML_TAG_PATTERN.search(text):
        count = len(HTML_TAG_PATTERN.findall(text))
        text = HTML_TAG_PATTERN.sub('', text)
        stats['html_tags_removed'] += count
        changed = True

    # Remove stray angle brackets
    if '<' in text or '>' in text:
        stats['angle_brackets_removed'] += text.count('<') + text.count('>')
        text = text.replace('<', '').replace('>', '')
        changed = True

    # Remove foreign chars
    text, removed_foreign = remove_foreign_chars(text)
    if removed_foreign:
        stats['foreign_chars_removed'] += removed_foreign
        changed = True

    # Normalize whitespace
    cleaned = normalize_whitespace_preserve_newlines(text)
    if cleaned != text:
        stats['whitespace_normalized'] += 1
        text = cleaned
        changed = True

    # Track paragraphs touched
    if changed:
        stats['paragraphs_modified'] += 1

    return text.strip(), changed


def main() -> None:
    args = parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)
    report_path = Path(args.report)

    if not input_path.exists():
        raise FileNotFoundError(f"Không tìm thấy input: {input_path}")

    stats = {
        'total_paragraphs': 0,
        'paragraphs_modified': 0,
        'urls_removed': 0,
        'bare_http_removed': 0,
        'website_removed': 0,
        'nguon_removed': 0,
        'html_tags_removed': 0,
        'html_entities': 0,
        'angle_brackets_removed': 0,
        'foreign_chars_removed': 0,
        'whitespace_normalized': 0
    }

    affected_samples = []
    cleaned_records = []

    # Read and process JSONL
    for data in read_jsonl(input_path):
        text = data.get("text", "")
        stats['total_paragraphs'] += 1
        cleaned_text, changed = clean_text(text, stats)
        
        if changed and len(affected_samples) < 20:
            affected_samples.append({
                "novel_name": data.get("novel_name"),
                "paragraph_index": data.get("paragraph_index"),
                "original": text[:200],
                "cleaned": cleaned_text[:200]
            })
        
        data["text"] = cleaned_text
        if not args.dry_run:
            cleaned_records.append(data)

    # Write output if not dry-run
    if not args.dry_run:
        write_jsonl(output_path, iter(cleaned_records))

    # Save report
    report = {
        "input": str(input_path),
        "output": str(output_path) if not args.dry_run else None,
        "stats": stats,
        "samples": affected_samples
    }
    save_json(report_path, report)

    print("=== CLEAN NOISE REPORT ===")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

