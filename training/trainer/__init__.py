"""
Training pipeline utilities and scripts.

This module provides:
- Preprocessor: Text preprocessing for Vietnamese stories
- CleaningLevel: Enum for cleaning levels (SAFE, BALANCED, AGGRESSIVE)
- Config classes: Centralized configuration
- Utility functions: Common I/O and encoding utilities
"""

from .preprocessing import Preprocessor
from .config import (
    Paths,
    CleaningLevel,
    PreprocessingConfig,
    TokenizerConfig,
    SplitConfig,
)
from .utils import setup_encoding, read_jsonl, write_jsonl

__all__ = [
    'Preprocessor',
    'CleaningLevel',
    'Paths',
    'PreprocessingConfig',
    'TokenizerConfig',
    'SplitConfig',
    'setup_encoding',
    'read_jsonl',
    'write_jsonl',
]

__version__ = "0.1.0"

