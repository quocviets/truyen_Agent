"""
Central configuration for training pipeline.

This module provides:
- Paths: Centralized path constants
- PreprocessingConfig: Configuration for preprocessing
- TokenizerConfig: Configuration for tokenizer
- SplitConfig: Configuration for dataset splitting
"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional


class Paths:
    """Centralized path constants for training pipeline."""
    
    # Project root (3 levels up from this file: training/trainer/config.py)
    ROOT = Path(__file__).resolve().parents[2]
    
    # Dataset paths
    RAW_DIR = ROOT / "training" / "dataset" / "raw" / "truyenmoiii_output"
    PREPROCESSED_DIR = ROOT / "training" / "dataset" / "preprocessed"
    SPLITS_DIR = ROOT / "training" / "dataset" / "splits"
    TOKENIZED_DIR = ROOT / "training" / "dataset" / "tokenized"
    
    # Model paths
    TOKENIZER_DIR = ROOT / "training" / "tokenizer"
    MODEL_DIR = ROOT / "training" / "model"
    
    # Output files
    ALL_NOVELS_PREPROCESSED_JSONL = PREPROCESSED_DIR / "all_novels_preprocessed.jsonl"
    ALL_NOVELS_PREPROCESSED_CLEAN_JSONL = PREPROCESSED_DIR / "all_novels_preprocessed_clean.jsonl"
    PREPROCESSING_SUMMARY_JSON = PREPROCESSED_DIR / "preprocessing_summary.json"
    CLEAN_NOISE_REPORT_JSON = PREPROCESSED_DIR / "clean_noise_report.json"
    
    # Split files
    TRAIN_JSONL = SPLITS_DIR / "train.jsonl"
    VAL_JSONL = SPLITS_DIR / "val.jsonl"
    TEST_JSONL = SPLITS_DIR / "test.jsonl"
    TRAIN_SUMMARY_JSON = SPLITS_DIR / "train_summary.json"
    VAL_SUMMARY_JSON = SPLITS_DIR / "val_summary.json"
    TEST_SUMMARY_JSON = SPLITS_DIR / "test_summary.json"
    SPLITS_SUMMARY_JSON = SPLITS_DIR / "splits_summary.json"
    
    # Tokenizer files
    TOKENIZER_MODEL = TOKENIZER_DIR / "sp_model.model"
    TOKENIZER_VOCAB = TOKENIZER_DIR / "sp_model.vocab"
    TOKENIZER_INFO_JSON = TOKENIZER_DIR / "tokenizer_info.json"


class CleaningLevel(Enum):
    """Cleaning intensity used during preprocessing."""
    
    SAFE = "safe"
    BALANCED = "balanced"
    AGGRESSIVE = "aggressive"


@dataclass
class PreprocessingConfig:
    """Configuration for text preprocessing."""
    
    # Cleaning level
    cleaning_level: CleaningLevel = CleaningLevel.BALANCED
    
    # Paragraph filtering
    min_paragraph_length: int = 50
    max_paragraph_length: int = 2000
    min_line_length: int = 10
    
    # Chapter filtering
    min_chapter_length: int = 500  # bytes
    min_ratio: float = 0.1  # ratio compared to average
    
    # Output format
    output_format: str = "combined"  # "combined" or "jsonl"
    
    # Paths (optional, defaults to Paths class)
    raw_dir: Optional[Path] = None
    output_dir: Optional[Path] = None
    
    def __post_init__(self):
        """Set default paths if not provided."""
        if self.raw_dir is None:
            self.raw_dir = Paths.RAW_DIR
        if self.output_dir is None:
            self.output_dir = Paths.PREPROCESSED_DIR


@dataclass
class TokenizerConfig:
    """Configuration for SentencePiece tokenizer."""
    
    vocab_size: int = 32000
    model_type: str = "bpe"  # "bpe" or "unigram"
    character_coverage: float = 0.9995
    test_samples: int = 5
    
    # Paths (optional, defaults to Paths class)
    input_jsonl: Optional[Path] = None
    output_dir: Optional[Path] = None
    
    def __post_init__(self):
        """Set default paths if not provided."""
        if self.input_jsonl is None:
            self.input_jsonl = Paths.TRAIN_JSONL
        if self.output_dir is None:
            self.output_dir = Paths.TOKENIZER_DIR


@dataclass
class SplitConfig:
    """Configuration for dataset splitting."""
    
    train_ratio: float = 0.9
    val_ratio: float = 0.05
    test_ratio: float = 0.05
    seed: int = 42
    
    # Paths (optional, defaults to Paths class)
    input_jsonl: Optional[Path] = None
    raw_dir: Optional[Path] = None
    output_dir: Optional[Path] = None
    
    def __post_init__(self):
        """Set default paths if not provided."""
        if self.input_jsonl is None:
            self.input_jsonl = Paths.ALL_NOVELS_PREPROCESSED_CLEAN_JSONL
        if self.raw_dir is None:
            self.raw_dir = Paths.RAW_DIR
        if self.output_dir is None:
            self.output_dir = Paths.SPLITS_DIR
        
        # Validate ratios
        total = self.train_ratio + self.val_ratio + self.test_ratio
        if abs(total - 1.0) > 1e-6:
            raise ValueError(f"Ratios must sum to 1.0, got {total}")


@dataclass
class CleanNoiseConfig:
    """Configuration for noise cleaning."""
    
    # Paths (optional, defaults to Paths class)
    input_jsonl: Optional[Path] = None
    output_jsonl: Optional[Path] = None
    report_json: Optional[Path] = None
    dry_run: bool = False
    
    def __post_init__(self):
        """Set default paths if not provided."""
        if self.input_jsonl is None:
            self.input_jsonl = Paths.ALL_NOVELS_PREPROCESSED_JSONL
        if self.output_jsonl is None:
            self.output_jsonl = Paths.ALL_NOVELS_PREPROCESSED_CLEAN_JSONL
        if self.report_json is None:
            self.report_json = Paths.CLEAN_NOISE_REPORT_JSON

