"""
Utility functions for training pipeline.

This module provides common I/O and encoding utilities used across
multiple training scripts.
"""

import json
import sys
from pathlib import Path
from typing import Iterator, Dict, Any, List, Optional


def setup_encoding():
    """
    Setup UTF-8 encoding for Windows console.
    
    Windows console mặc định dùng encoding khác UTF-8, cần reconfigure
    để hiển thị tiếng Việt đúng.
    """
    if sys.platform == 'win32':
        try:
            sys.stdout.reconfigure(encoding='utf-8')
            sys.stderr.reconfigure(encoding='utf-8')
        except Exception:
            # Nếu không reconfigure được thì bỏ qua (không ảnh hưởng xử lý)
            pass


def read_jsonl(path: Path, show_progress: bool = False) -> Iterator[Dict[str, Any]]:
    """
    Read JSONL file with error handling.
    
    Args:
        path: Path to JSONL file
        show_progress: Whether to show progress (requires tqdm)
        
    Yields:
        Dict records from JSONL file
        
    Example:
        >>> for record in read_jsonl(Path("data.jsonl")):
        ...     print(record['text'])
    """
    if show_progress:
        from tqdm import tqdm
        
        # Count lines first for progress bar
        total_lines = sum(1 for _ in open(path, 'r', encoding='utf-8'))
        file_handle = open(path, 'r', encoding='utf-8')
        iterator = tqdm(file_handle, total=total_lines, desc=f"Reading {path.name}")
    else:
        file_handle = open(path, 'r', encoding='utf-8')
        iterator = file_handle
    
    try:
        for line_num, line in enumerate(iterator, 1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
                yield record
            except json.JSONDecodeError as e:
                print(f"⚠️  Lỗi parse JSON ở dòng {line_num}: {e}")
                continue
    finally:
        file_handle.close()


def write_jsonl(path: Path, records: Iterator[Dict[str, Any]], show_progress: bool = False):
    """
    Write records to JSONL file.
    
    Args:
        path: Path to output JSONL file
        records: Iterator of dict records to write
        show_progress: Whether to show progress (requires tqdm)
        
    Example:
        >>> records = [{'text': 'Hello'}, {'text': 'World'}]
        >>> write_jsonl(Path("output.jsonl"), iter(records))
    """
    # Ensure parent directory exists
    path.parent.mkdir(parents=True, exist_ok=True)
    
    if show_progress:
        from tqdm import tqdm
        # Convert to list to get length (may be memory-intensive for large datasets)
        records_list = list(records)
        records = iter(records_list)
        iterator = tqdm(records_list, desc=f"Writing {path.name}")
    else:
        iterator = records
    
    with open(path, 'w', encoding='utf-8') as f:
        for record in iterator:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')


def load_json(path: Path) -> Dict[str, Any]:
    """
    Load JSON file.
    
    Args:
        path: Path to JSON file
        
    Returns:
        Dict from JSON file
        
    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If file is not valid JSON
    """
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json(path: Path, data: Dict[str, Any], indent: int = 2):
    """
    Save dict to JSON file.
    
    Args:
        path: Path to output JSON file
        data: Dict to save
        indent: JSON indentation (default: 2)
    """
    # Ensure parent directory exists
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=indent)


def ensure_dir(path: Path):
    """
    Ensure directory exists, create if not.
    
    Args:
        path: Path to directory
    """
    path.mkdir(parents=True, exist_ok=True)

