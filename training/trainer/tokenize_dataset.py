"""
Convert cleaned dataset splits into token IDs using SentencePiece.

The script reads JSONL splits (`train/val/test.jsonl`) and produces
JSONL files that contain SentencePiece token IDs plus basic metadata.
It does NOT run any training by itself.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Sequence

import sentencepiece as spm

from .config import Paths
from .utils import ensure_dir, read_jsonl, setup_encoding


AVAILABLE_SPLITS = {
    "train": Paths.TRAIN_JSONL,
    "val": Paths.VAL_JSONL,
    "test": Paths.TEST_JSONL,
}

DEFAULT_OUTPUT_FILES = {
    "train": Paths.TOKENIZED_DIR / "train_tokens.jsonl",
    "val": Paths.TOKENIZED_DIR / "val_tokens.jsonl",
    "test": Paths.TOKENIZED_DIR / "test_tokens.jsonl",
}

METADATA_FIELDS: Sequence[str] = (
    "novel_name",
    "chapter_index",
    "paragraph_index_in_chapter",
    "original_paragraph_index",
    "global_paragraph_index",
)


@dataclass
class TokenizationStats:
    total_records: int = 0
    total_tokens: int = 0
    max_tokens: int = 0

    def update(self, token_count: int) -> None:
        self.total_records += 1
        self.total_tokens += token_count
        if token_count > self.max_tokens:
            self.max_tokens = token_count

    @property
    def avg_tokens(self) -> float:
        if self.total_records == 0:
            return 0.0
        return self.total_tokens / self.total_records


class DatasetTokenizer:
    """Tokenize JSONL dataset splits into SentencePiece token IDs."""

    def __init__(self, model_path: Path):
        if not model_path.exists():
            raise FileNotFoundError(f"Tokenizer model not found: {model_path}")
        self.processor = spm.SentencePieceProcessor(model_file=str(model_path))

    def tokenize_text(self, text: str) -> List[int]:
        """Return SentencePiece token IDs for the provided text."""
        return self.processor.encode(text, out_type=int)

    def tokenize_split(
        self,
        split_name: str,
        input_path: Path,
        output_path: Path,
        include_metadata: bool = True,
        show_progress: bool = False,
    ) -> TokenizationStats:
        """Tokenize one dataset split and write tokens to JSONL."""
        ensure_dir(output_path.parent)
        stats = TokenizationStats()

        iterator: Iterable[Dict] = read_jsonl(input_path, show_progress=show_progress)

        with open(output_path, "w", encoding="utf-8") as output_file:
            for index, record in enumerate(iterator):
                text = record.get("text", "")
                if not text:
                    continue

                token_ids = self.tokenize_text(text)
                token_count = len(token_ids)
                stats.update(token_count)

                output_record: Dict = {
                    "input_ids": token_ids,
                    "token_count": token_count,
                    "split": split_name,
                }

                if include_metadata:
                    for field in METADATA_FIELDS:
                        if field in record:
                            output_record[field] = record[field]

                output_file.write(json.dumps(output_record, ensure_ascii=False) + "\n")

        return stats


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Tokenize dataset splits using SentencePiece tokenizer."
    )
    parser.add_argument(
        "--splits",
        nargs="+",
        choices=list(AVAILABLE_SPLITS.keys()),
        default=["train", "val", "test"],
        help="Danh sách split cần tokenize (mặc định: train val test).",
    )
    parser.add_argument(
        "--tokenizer-model",
        type=Path,
        default=Paths.TOKENIZER_MODEL,
        help="Đường dẫn file SentencePiece model (.model).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Paths.TOKENIZED_DIR,
        help="Thư mục lưu JSONL tokenized.",
    )
    parser.add_argument(
        "--include-metadata",
        action="store_true",
        help="Ghi kèm metadata (novel_name, chapter_index, ...).",
    )
    parser.add_argument(
        "--show-progress",
        action="store_true",
        help="Hiển thị progress bar khi đọc JSONL.",
    )
    return parser.parse_args()


def main() -> None:
    setup_encoding()
    args = parse_args()
    tokenizer = DatasetTokenizer(args.tokenizer_model)

    for split_name in args.splits:
        input_path = AVAILABLE_SPLITS[split_name]
        output_file = DEFAULT_OUTPUT_FILES[split_name]
        if args.output_dir:
            ensure_dir(args.output_dir)
            output_file = args.output_dir / output_file.name

        print(f"🔁 Tokenizing split '{split_name}' → {output_file}")
        stats = tokenizer.tokenize_split(
            split_name=split_name,
            input_path=input_path,
            output_path=output_file,
            include_metadata=args.include_metadata,
            show_progress=args.show_progress,
        )

        print(
            f"✅ {split_name}: {stats.total_records:,} records | "
            f"avg tokens {stats.avg_tokens:.1f} | max tokens {stats.max_tokens}"
        )


if __name__ == "__main__":
    main()

