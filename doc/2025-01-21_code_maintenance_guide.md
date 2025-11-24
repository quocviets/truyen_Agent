# Hướng Dẫn Update và Maintain Code

**Ngày tạo:** 2025-01-21  
**Mục đích:** Hướng dẫn chi tiết cách update, maintain và mở rộng code sau này

---

## Mục Lục

1. [Tổng Quan Cấu Trúc](#tổng-quan-cấu-trúc)
2. [Cách Update Paths (Đường Dẫn)](#cách-update-paths-đường-dẫn)
3. [Cách Update Config Values](#cách-update-config-values)
4. [Cách Thêm Utility Functions](#cách-thêm-utility-functions)
5. [Cách Tạo Script Mới](#cách-tạo-script-mới)
6. [Best Practices](#best-practices)
7. [Ví Dụ Cụ Thể](#ví-dụ-cụ-thể)
8. [Troubleshooting](#troubleshooting)

---

## Tổng Quan Cấu Trúc

### Kiến Trúc Code

```
training/
├── trainer/
│   ├── config.py          ← TẤT CẢ CONFIG VÀ PATHS Ở ĐÂY
│   ├── utils.py           ← TẤT CẢ UTILITY FUNCTIONS Ở ĐÂY
│   ├── preprocessing.py   ← Preprocessing logic
│   ├── split_dataset.py   ← Dataset splitting
│   ├── build_tokenizer.py ← Tokenizer building
│   └── clean_noise.py     ← Noise cleaning
└── ...
```

### Nguyên Tắc Thiết Kế

1. **Single Source of Truth**: Tất cả config và paths tập trung trong `config.py`
2. **DRY (Don't Repeat Yourself)**: Utilities tái sử dụng trong `utils.py`
3. **Separation of Concerns**: Mỗi module có trách nhiệm riêng
4. **Easy to Extend**: Dễ dàng thêm config/function mới

---

## Cách Update Paths (Đường Dẫn)

### Vị Trí: `training/trainer/config.py`

### Cấu Trúc Paths Class

```python
class Paths:
    """Centralized path constants for training pipeline."""
    
    # Project root
    ROOT = Path(__file__).resolve().parents[2]
    
    # Dataset paths
    RAW_DIR = ROOT / "training" / "dataset" / "raw" / "truyenmoiii_output"
    PREPROCESSED_DIR = ROOT / "training" / "dataset" / "preprocessed"
    # ... các paths khác
```

### Ví Dụ Update Paths

#### Ví Dụ 1: Đổi Thư Mục Raw Data

**Trước:**
```python
RAW_DIR = ROOT / "training" / "dataset" / "raw" / "truyenmoiii_output"
```

**Sau (nếu đổi sang thư mục khác):**
```python
RAW_DIR = ROOT / "data" / "raw" / "novels"
```

**Kết quả:** Tất cả scripts tự động dùng path mới, không cần sửa ở chỗ khác.

#### Ví Dụ 2: Thêm Path Mới

**Thêm vào Paths class:**
```python
class Paths:
    # ... existing paths ...
    
    # Thêm path mới
    CACHE_DIR = ROOT / "training" / "cache"
    LOGS_DIR = ROOT / "training" / "logs"
```

**Sử dụng trong script:**
```python
from .config import Paths

# Tự động dùng path mới
cache_file = Paths.CACHE_DIR / "model_cache.pkl"
```

### Lưu Ý

- ✅ **Nên:** Sửa paths trong `config.py` → Paths class
- ❌ **Không nên:** Hardcode paths trong scripts
- ✅ **Nên:** Dùng `Paths.PATH_NAME` trong tất cả scripts
- ❌ **Không nên:** Tạo path constants riêng trong mỗi script

---

## Cách Update Config Values

### Vị Trí: `training/trainer/config.py`

### Các Config Classes Hiện Có

1. **PreprocessingConfig**: Config cho preprocessing
2. **TokenizerConfig**: Config cho tokenizer
3. **SplitConfig**: Config cho dataset splitting
4. **CleanNoiseConfig**: Config cho noise cleaning

### Ví Dụ Update Config

#### Ví Dụ 1: Thay Đổi Min Paragraph Length

**File:** `training/trainer/config.py`

**Tìm:**
```python
@dataclass
class PreprocessingConfig:
    min_paragraph_length: int = 50  # ← Sửa giá trị này
```

**Sửa thành:**
```python
@dataclass
class PreprocessingConfig:
    min_paragraph_length: int = 100  # Đổi từ 50 → 100
```

**Kết quả:** Preprocessor tự động dùng giá trị mới khi khởi tạo.

#### Ví Dụ 2: Thay Đổi Vocab Size

**Tìm:**
```python
@dataclass
class TokenizerConfig:
    vocab_size: int = 32000  # ← Sửa giá trị này
```

**Sửa thành:**
```python
@dataclass
class TokenizerConfig:
    vocab_size: int = 50000  # Đổi từ 32000 → 50000
```

#### Ví Dụ 3: Thay Đổi Train/Val/Test Ratios

**Tìm:**
```python
@dataclass
class SplitConfig:
    train_ratio: float = 0.9
    val_ratio: float = 0.05
    test_ratio: float = 0.05
```

**Sửa thành:**
```python
@dataclass
class SplitConfig:
    train_ratio: float = 0.8   # Đổi từ 0.9 → 0.8
    val_ratio: float = 0.1     # Đổi từ 0.05 → 0.1
    test_ratio: float = 0.1    # Đổi từ 0.05 → 0.1
```

**Lưu ý:** Tổng 3 ratios phải = 1.0 (có validation tự động).

### Thêm Config Mới

#### Bước 1: Tạo Config Class

**Thêm vào `config.py`:**
```python
@dataclass
class TrainingConfig:
    """Configuration for model training."""
    
    batch_size: int = 32
    learning_rate: float = 1e-4
    num_epochs: int = 10
    max_seq_length: int = 512
    
    # Paths (optional, defaults to Paths class)
    model_dir: Optional[Path] = None
    
    def __post_init__(self):
        """Set default paths if not provided."""
        if self.model_dir is None:
            self.model_dir = Paths.MODEL_DIR
```

#### Bước 2: Sử Dụng Config

**Trong script mới:**
```python
from .config import TrainingConfig

# Tạo config instance
config = TrainingConfig(
    batch_size=64,
    learning_rate=2e-4
)

# Sử dụng
print(f"Batch size: {config.batch_size}")
print(f"Model dir: {config.model_dir}")
```

### Lưu Ý

- ✅ **Nên:** Sửa config trong `config.py` → Config classes
- ❌ **Không nên:** Hardcode config values trong scripts
- ✅ **Nên:** Dùng dataclass với type hints
- ✅ **Nên:** Validate config values trong `__post_init__`

---

## Cách Thêm Utility Functions

### Vị Trí: `training/trainer/utils.py`

### Các Utility Functions Hiện Có

1. `setup_encoding()`: Setup UTF-8 encoding cho Windows
2. `read_jsonl()`: Đọc JSONL file
3. `write_jsonl()`: Ghi JSONL file
4. `load_json()`: Load JSON file
5. `save_json()`: Save JSON file
6. `ensure_dir()`: Tạo directory nếu chưa có

### Ví Dụ Thêm Utility Function

#### Ví Dụ 1: Thêm Function Đếm Tokens

**Thêm vào `utils.py`:**
```python
def count_tokens(text: str, tokenizer) -> int:
    """
    Count tokens in text using tokenizer.
    
    Args:
        text: Input text
        tokenizer: Tokenizer instance
        
    Returns:
        Number of tokens
    """
    return len(tokenizer.encode(text))
```

**Sử dụng trong script:**
```python
from .utils import count_tokens

# Tự động có function mới
num_tokens = count_tokens("Hello world", tokenizer)
```

#### Ví Dụ 2: Thêm Function Format Size

**Thêm vào `utils.py`:**
```python
def format_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted string (e.g., "1.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"
```

**Sử dụng:**
```python
from .utils import format_size

file_size = os.path.getsize("data.jsonl")
print(f"File size: {format_size(file_size)}")
```

#### Ví Dụ 3: Thêm Function Validate JSONL

**Thêm vào `utils.py`:**
```python
def validate_jsonl(path: Path) -> Dict[str, Any]:
    """
    Validate JSONL file and return statistics.
    
    Args:
        path: Path to JSONL file
        
    Returns:
        Dict with validation results
    """
    stats = {
        "total_lines": 0,
        "valid_lines": 0,
        "invalid_lines": 0,
        "errors": []
    }
    
    for line_num, line in enumerate(open(path, 'r', encoding='utf-8'), 1):
        stats["total_lines"] += 1
        if not line.strip():
            continue
        try:
            json.loads(line)
            stats["valid_lines"] += 1
        except json.JSONDecodeError as e:
            stats["invalid_lines"] += 1
            stats["errors"].append({
                "line": line_num,
                "error": str(e)
            })
    
    return stats
```

### Lưu Ý

- ✅ **Nên:** Thêm utilities vào `utils.py` để tái sử dụng
- ✅ **Nên:** Viết docstring rõ ràng với Args/Returns
- ✅ **Nên:** Dùng type hints
- ❌ **Không nên:** Copy-paste utility code vào nhiều scripts
- ✅ **Nên:** Handle errors gracefully

---

## Cách Tạo Script Mới

### Template Script Mới

```python
"""
Script description here.

This script does X, Y, Z.
"""

import argparse
from pathlib import Path

from .config import Paths, SomeConfig
from .utils import setup_encoding, read_jsonl, write_jsonl


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Script description")
    
    parser.add_argument(
        "--input",
        type=Path,
        default=Paths.SOME_INPUT_FILE,
        help="Input file path"
    )
    
    parser.add_argument(
        "--output",
        type=Path,
        default=Paths.SOME_OUTPUT_FILE,
        help="Output file path"
    )
    
    parser.add_argument(
        "--config-value",
        type=int,
        default=100,
        help="Some config value"
    )
    
    return parser.parse_args()


def process_data(input_path: Path, output_path: Path, config_value: int):
    """
    Process data from input to output.
    
    Args:
        input_path: Path to input file
        output_path: Path to output file
        output_path: Some config value
    """
    # Setup encoding
    setup_encoding()
    
    # Read input
    records = read_jsonl(input_path)
    
    # Process
    processed_records = []
    for record in records:
        # Your processing logic here
        processed_record = {
            "text": record["text"],
            "processed": True
        }
        processed_records.append(processed_record)
    
    # Write output
    write_jsonl(output_path, iter(processed_records))
    
    print(f"✅ Processed {len(processed_records)} records")
    print(f"✅ Output saved to {output_path}")


def main():
    """Main function."""
    args = parse_args()
    
    # Validate inputs
    if not args.input.exists():
        print(f"❌ Input file not found: {args.input}")
        return
    
    # Process
    process_data(args.input, args.output, args.config_value)


if __name__ == "__main__":
    main()
```

### Bước Tạo Script Mới

#### Bước 1: Tạo File Mới

**Tạo file:** `training/trainer/my_new_script.py`

#### Bước 2: Import Config và Utils

```python
from .config import Paths, SomeConfig
from .utils import setup_encoding, read_jsonl, write_jsonl
```

#### Bước 3: Sử Dụng Paths

```python
# Thay vì hardcode
input_file = Paths.PREPROCESSED_DIR / "data.jsonl"

# Hoặc dùng config
config = SomeConfig()
output_dir = config.output_dir
```

#### Bước 4: Sử Dụng Utils

```python
# Setup encoding (quan trọng cho Windows)
setup_encoding()

# Read JSONL
for record in read_jsonl(input_path):
    # Process record
    pass

# Write JSONL
write_jsonl(output_path, records)
```

#### Bước 5: Thêm Script Vào `__init__.py` (Optional)

**File:** `training/trainer/__init__.py`

```python
from .my_new_script import process_data
```

### Ví Dụ Script Hoàn Chỉnh

**File:** `training/trainer/analyze_dataset.py`

```python
"""
Analyze dataset statistics.
"""

import argparse
from pathlib import Path
from collections import Counter

from .config import Paths
from .utils import setup_encoding, read_jsonl, save_json


def analyze_dataset(input_path: Path) -> dict:
    """
    Analyze dataset and return statistics.
    
    Args:
        input_path: Path to input JSONL file
        
    Returns:
        Dict with statistics
    """
    stats = {
        "total_records": 0,
        "total_chars": 0,
        "total_words": 0,
        "novel_counts": Counter()
    }
    
    for record in read_jsonl(input_path):
        stats["total_records"] += 1
        text = record.get("text", "")
        stats["total_chars"] += len(text)
        stats["total_words"] += len(text.split())
        
        novel_id = record.get("novel_id", "unknown")
        stats["novel_counts"][novel_id] += 1
    
    return {
        "total_records": stats["total_records"],
        "total_chars": stats["total_chars"],
        "total_words": stats["total_words"],
        "avg_chars_per_record": stats["total_chars"] / stats["total_records"] if stats["total_records"] > 0 else 0,
        "avg_words_per_record": stats["total_words"] / stats["total_records"] if stats["total_records"] > 0 else 0,
        "num_novels": len(stats["novel_counts"]),
        "novel_counts": dict(stats["novel_counts"])
    }


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Analyze dataset")
    parser.add_argument(
        "--input",
        type=Path,
        default=Paths.ALL_NOVELS_PREPROCESSED_CLEAN_JSONL,
        help="Input JSONL file"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Paths.PREPROCESSED_DIR / "dataset_stats.json",
        help="Output JSON file"
    )
    
    args = parser.parse_args()
    setup_encoding()
    
    if not args.input.exists():
        print(f"❌ Input file not found: {args.input}")
        return
    
    print(f"📊 Analyzing dataset: {args.input}")
    stats = analyze_dataset(args.input)
    
    save_json(args.output, stats)
    print(f"✅ Statistics saved to {args.output}")
    print(f"   Total records: {stats['total_records']:,}")
    print(f"   Total chars: {stats['total_chars']:,}")
    print(f"   Total words: {stats['total_words']:,}")


if __name__ == "__main__":
    main()
```

### Lưu Ý

- ✅ **Nên:** Dùng config và utils từ đầu
- ✅ **Nên:** Viết docstring cho functions
- ✅ **Nên:** Validate inputs
- ✅ **Nên:** Handle errors gracefully
- ❌ **Không nên:** Hardcode paths hoặc config values
- ❌ **Không nên:** Copy-paste code từ scripts khác

---

## Best Practices

### 1. Import Order

```python
# Standard library
import argparse
from pathlib import Path

# Local imports
from .config import Paths, SomeConfig
from .utils import setup_encoding, read_jsonl
```

### 2. Error Handling

```python
try:
    data = load_json(path)
except FileNotFoundError:
    print(f"❌ File not found: {path}")
    return
except json.JSONDecodeError as e:
    print(f"❌ Invalid JSON: {e}")
    return
```

### 3. Progress Reporting

```python
from .utils import read_jsonl

# Với progress bar
for record in read_jsonl(input_path, show_progress=True):
    # Process
    pass
```

### 4. Path Validation

```python
from pathlib import Path

def validate_path(path: Path, must_exist: bool = True):
    """Validate path exists."""
    if must_exist and not path.exists():
        raise FileNotFoundError(f"Path not found: {path}")
    return path
```

### 5. Config Usage

```python
# ✅ Good: Dùng config class
config = PreprocessingConfig(min_paragraph_length=100)
preprocessor = Preprocessor(config)

# ❌ Bad: Hardcode values
preprocessor = Preprocessor(min_paragraph_length=100)
```

---

## Ví Dụ Cụ Thể

### Scenario 1: Đổi Thư Mục Dataset

**Yêu cầu:** Đổi thư mục dataset từ `training/dataset` sang `data/dataset`

**Bước 1:** Sửa `config.py`

```python
class Paths:
    ROOT = Path(__file__).resolve().parents[2]
    
    # Đổi từ training/dataset → data/dataset
    RAW_DIR = ROOT / "data" / "dataset" / "raw" / "truyenmoiii_output"
    PREPROCESSED_DIR = ROOT / "data" / "dataset" / "preprocessed"
    SPLITS_DIR = ROOT / "data" / "dataset" / "splits"
    # ... các paths khác
```

**Kết quả:** Tất cả scripts tự động dùng paths mới.

### Scenario 2: Thêm Config Cho Training

**Yêu cầu:** Thêm config cho model training

**Bước 1:** Thêm config class vào `config.py`

```python
@dataclass
class TrainingConfig:
    """Configuration for model training."""
    
    batch_size: int = 32
    learning_rate: float = 1e-4
    num_epochs: int = 10
    max_seq_length: int = 512
    gradient_accumulation_steps: int = 1
    
    # Paths
    model_dir: Optional[Path] = None
    checkpoint_dir: Optional[Path] = None
    
    def __post_init__(self):
        if self.model_dir is None:
            self.model_dir = Paths.MODEL_DIR
        if self.checkpoint_dir is None:
            self.checkpoint_dir = Paths.MODEL_DIR / "checkpoints"
```

**Bước 2:** Sử dụng trong training script

```python
from .config import TrainingConfig

config = TrainingConfig(
    batch_size=64,
    learning_rate=2e-4
)

# Training logic sử dụng config
for epoch in range(config.num_epochs):
    # ...
    pass
```

### Scenario 3: Thêm Utility Function

**Yêu cầu:** Thêm function tính toán statistics

**Bước 1:** Thêm vào `utils.py`

```python
def compute_statistics(records: Iterator[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Compute statistics from records.
    
    Args:
        records: Iterator of records
        
    Returns:
        Dict with statistics
    """
    stats = {
        "count": 0,
        "total_chars": 0,
        "total_words": 0
    }
    
    for record in records:
        stats["count"] += 1
        text = record.get("text", "")
        stats["total_chars"] += len(text)
        stats["total_words"] += len(text.split())
    
    if stats["count"] > 0:
        stats["avg_chars"] = stats["total_chars"] / stats["count"]
        stats["avg_words"] = stats["total_words"] / stats["count"]
    
    return stats
```

**Bước 2:** Sử dụng trong scripts

```python
from .utils import read_jsonl, compute_statistics

records = read_jsonl(input_path)
stats = compute_statistics(records)
print(f"Average chars: {stats['avg_chars']:.2f}")
```

---

## Troubleshooting

### Vấn Đề 1: Import Error

**Lỗi:**
```
ModuleNotFoundError: No module named 'training.trainer'
```

**Giải pháp:**
- Đảm bảo đang chạy từ project root
- Kiểm tra `training/__init__.py` và `training/trainer/__init__.py` tồn tại
- Dùng relative imports: `from .config import Paths`

### Vấn Đề 2: Path Không Đúng

**Lỗi:**
```
FileNotFoundError: training/dataset/raw/...
```

**Giải pháp:**
- Kiểm tra `Paths.ROOT` đúng không
- Kiểm tra paths trong `config.py`
- Đảm bảo directories tồn tại hoặc dùng `ensure_dir()`

### Vấn Đề 3: Config Không Áp Dụng

**Lỗi:** Thay đổi config nhưng script vẫn dùng giá trị cũ

**Giải pháp:**
- Đảm bảo tạo config instance mới: `config = PreprocessingConfig(...)`
- Không hardcode values trong scripts
- Kiểm tra default values trong config class

### Vấn Đề 4: Encoding Issues (Windows)

**Lỗi:** Tiếng Việt hiển thị sai

**Giải pháp:**
- Luôn gọi `setup_encoding()` ở đầu script
- Đảm bảo files được đọc/ghi với `encoding='utf-8'`
- Utils functions đã handle encoding tự động

---

## Tóm Tắt

### Checklist Khi Update Code

- [ ] Paths: Sửa trong `config.py` → Paths class
- [ ] Config values: Sửa trong `config.py` → Config classes
- [ ] Utilities: Thêm vào `utils.py`
- [ ] Scripts mới: Import từ config và utils
- [ ] Không hardcode paths/config trong scripts
- [ ] Viết docstring cho functions mới
- [ ] Test sau khi update

### Quy Tắc Vàng

1. **Single Source of Truth**: Config và paths chỉ ở `config.py`
2. **DRY**: Utilities chỉ ở `utils.py`
3. **Easy to Extend**: Dễ thêm config/function mới
4. **Maintainable**: Code dễ đọc, dễ sửa

---

## Kết Luận

Với cấu trúc code hiện tại, việc update và maintain code trở nên rất dễ dàng:

- ✅ **Update paths**: Chỉ sửa 1 file (`config.py`)
- ✅ **Update config**: Chỉ sửa 1 file (`config.py`)
- ✅ **Thêm utilities**: Chỉ thêm vào 1 file (`utils.py`)
- ✅ **Tạo script mới**: Import sẵn config và utils

**Lưu ý:** Luôn tuân thủ nguyên tắc "Single Source of Truth" - không duplicate config/paths ở nhiều nơi.


