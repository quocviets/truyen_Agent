# Báo cáo Review Code - Toàn bộ Codebase

**Ngày:** 2025-11-21  
**Mục tiêu:** Đánh giá code quality, maintainability, và khả năng update  
**Phạm vi:** `training/trainer/` - Tất cả scripts preprocessing, QA, và tokenizer

---

## 1. Tổng quan

### 1.1. Scripts đã review

| Script | Mục đích | Dòng code | Status |
|--------|----------|-----------|--------|
| `preprocessing.py` | Tiền xử lý dữ liệu raw | ~1,100 | ✅ Hoàn chỉnh |
| `clean_noise.py` | Làm sạch noise sau preprocessing | ~250 | ✅ Hoàn chỉnh |
| `data_quality_analysis.py` | QA dataset 8 bước | ~400 | ✅ Hoàn chỉnh |
| `split_dataset.py` | Chia train/val/test 90/5/5 | ~370 | ✅ Hoàn chỉnh |
| `build_tokenizer.py` | Build SentencePiece tokenizer | ~330 | ✅ Hoàn chỉnh |

**Tổng:** ~2,450 dòng code

---

## 2. Điểm mạnh (Strengths)

### 2.1. Code Organization ✅

**Tốt:**
- ✅ Mỗi script có một mục đích rõ ràng (single responsibility)
- ✅ Cấu trúc thư mục hợp lý: `training/trainer/`, `training/dataset/`, `training/configs/`
- ✅ Tách biệt rõ ràng: preprocessing → clean → QA → split → tokenizer

**Ví dụ:**
```python
# preprocessing.py - Chỉ làm preprocessing
# clean_noise.py - Chỉ clean noise
# split_dataset.py - Chỉ split dataset
```

### 2.2. Documentation ✅

**Tốt:**
- ✅ Mỗi script có docstring đầu file mô tả mục đích, usage
- ✅ Functions có docstrings với Args/Returns
- ✅ Comments giải thích logic phức tạp
- ✅ Type hints đầy đủ (`from __future__ import annotations`)

**Ví dụ:**
```python
"""
Build SentencePiece tokenizer từ train split cho tiếng Việt.

Chiến lược:
    1. Đọc training/dataset/splits/train.jsonl...
    2. Extract text từ mỗi paragraph...
"""
```

### 2.3. Error Handling ✅

**Tốt:**
- ✅ Try-except cho JSON parsing
- ✅ Kiểm tra file tồn tại trước khi đọc
- ✅ Logging warnings cho lỗi không critical
- ✅ Graceful degradation (bỏ qua lỗi, tiếp tục xử lý)

**Ví dụ:**
```python
try:
    record = json.loads(line)
except json.JSONDecodeError as e:
    print(f"⚠️  Lỗi parse JSON ở dòng {line_num}: {e}")
    continue
```

### 2.4. CLI Interface ✅

**Tốt:**
- ✅ Tất cả scripts dùng `argparse` với defaults hợp lý
- ✅ Help text rõ ràng
- ✅ Validation cho arguments (choices, type)

**Ví dụ:**
```python
parser.add_argument(
    "--cleaning-level",
    choices=["safe", "balanced", "aggressive"],
    default="balanced",
    help="Mức độ làm sạch text"
)
```

### 2.5. Reproducibility ✅

**Tốt:**
- ✅ Fixed random seeds (42) cho shuffle, sampling
- ✅ Deterministic processing
- ✅ Metadata lưu đầy đủ (summary.json, tokenizer_info.json)

---

## 3. Vấn đề cần cải thiện (Issues)

### 3.1. ⚠️ Import Path Management

**Vấn đề:**
- `split_dataset.py` và `build_tokenizer.py` dùng `sys.path.append()` để import `Preprocessor`
- Không có `__init__.py` trong `training/trainer/` → không phải package
- Hard-coded path resolution

**Code hiện tại:**
```python
# split_dataset.py, build_tokenizer.py
import sys
sys.path.append(str(Path(__file__).resolve().parents[2]))
from training.trainer.preprocessing import Preprocessor, CleaningLevel
```

**Vấn đề:**
- ❌ Không portable (phụ thuộc vào cấu trúc thư mục)
- ❌ Khó test (phải setup path đúng)
- ❌ Không chuẩn Python package structure

**Khuyến nghị:**
1. Tạo `training/trainer/__init__.py` để biến thành package
2. Tạo `training/__init__.py` 
3. Hoặc dùng relative imports: `from .preprocessing import Preprocessor`

---

### 3.2. ⚠️ Code Duplication

**Vấn đề:**
- Một số logic bị lặp lại giữa các scripts

**Ví dụ 1: JSONL Reading**
```python
# build_tokenizer.py
with open(input_jsonl, 'r', encoding='utf-8') as f:
    for line_num, line in enumerate(f, 1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
            text = record.get('text', '').strip()
            if text:
                texts.append(text)
        except json.JSONDecodeError as e:
            print(f"⚠️  Lỗi parse JSON ở dòng {line_num}: {e}")
            continue
```

```python
# split_dataset.py - Có logic tương tự
# clean_noise.py - Có logic tương tự
```

**Khuyến nghị:**
- Tạo utility module `training/trainer/utils.py`:
  ```python
  def read_jsonl(path: Path) -> Iterator[Dict]:
      """Read JSONL file with error handling."""
      ...
  ```

**Ví dụ 2: Path Constants**
- Nhiều scripts hard-code paths như `"training/dataset/preprocessed/..."`

**Khuyến nghị:**
- Tạo `training/trainer/config.py`:
  ```python
  class Paths:
      RAW_DIR = Path("training/dataset/raw/truyenmoiii_output")
      PREPROCESSED_DIR = Path("training/dataset/preprocessed")
      SPLITS_DIR = Path("training/dataset/splits")
      TOKENIZER_DIR = Path("training/tokenizer")
  ```

---

### 3.3. ⚠️ Configuration Management

**Vấn đề:**
- Constants rải rác trong code (MIN_PARAGRAPH_LENGTH, MAX_PARAGRAPH_LENGTH, ...)
- Không có central config file
- Khó thay đổi config mà không sửa code

**Ví dụ:**
```python
# preprocessing.py
MIN_PARAGRAPH_LENGTH = 50
MAX_PARAGRAPH_LENGTH = 2000
MIN_LINE_LENGTH = 10
```

**Khuyến nghị:**
- Tạo `training/trainer/config.py`:
  ```python
  @dataclass
  class PreprocessingConfig:
      min_paragraph_length: int = 50
      max_paragraph_length: int = 2000
      min_line_length: int = 10
      cleaning_level: CleaningLevel = CleaningLevel.BALANCED
  ```

---

### 3.4. ⚠️ Logging System

**Vấn đề:**
- Dùng `print()` thay vì logging module
- Không có log levels (INFO, WARNING, ERROR)
- Khó redirect logs vào file
- Không có structured logging

**Ví dụ:**
```python
print(f"📖 Đang đọc {input_jsonl}...")
print(f"✅ Đã đọc {len(texts):,} paragraphs")
print(f"⚠️  Lỗi parse JSON ở dòng {line_num}: {e}")
```

**Khuyến nghị:**
- Dùng `logging` module:
  ```python
  import logging
  logger = logging.getLogger(__name__)
  logger.info(f"Đang đọc {input_jsonl}...")
  logger.warning(f"Lỗi parse JSON ở dòng {line_num}: {e}")
  ```

---

### 3.5. ⚠️ Windows Encoding Handling

**Vấn đề:**
- `preprocessing.py` có code xử lý Windows encoding, nhưng các script khác không có
- Inconsistent

**Code hiện tại:**
```python
# preprocessing.py
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass
```

**Khuyến nghị:**
- Tạo utility function trong `utils.py`:
  ```python
  def setup_encoding():
      """Setup UTF-8 encoding for Windows."""
      if sys.platform == 'win32':
          try:
              sys.stdout.reconfigure(encoding='utf-8')
              sys.stderr.reconfigure(encoding='utf-8')
          except Exception:
              pass
  ```

---

### 3.6. ⚠️ Dependencies Management

**Vấn đề:**
- Chỉ có `requirements_preprocessing.txt` với 2 packages
- Không có version pinning chặt chẽ
- Không có `requirements.txt` ở root

**File hiện tại:**
```
# requirements_preprocessing.txt
tqdm>=4.65.0
sentencepiece>=0.1.99
```

**Khuyến nghị:**
- Tạo `requirements.txt` ở root với tất cả dependencies
- Pin versions chặt hơn (hoặc dùng `requirements-dev.txt` cho dev)
- Thêm `setup.py` hoặc `pyproject.toml` nếu muốn install như package

---

### 3.7. ⚠️ Testing

**Vấn đề:**
- ❌ Không có unit tests
- ❌ Không có integration tests
- ❌ Không có test data

**Khuyến nghị:**
- Tạo `training/trainer/tests/`:
  - `test_preprocessing.py`
  - `test_clean_noise.py`
  - `test_split_dataset.py`
  - `test_build_tokenizer.py`
- Dùng `pytest` hoặc `unittest`

---

### 3.8. ⚠️ Type Hints Inconsistency

**Vấn đề:**
- Một số functions thiếu return type hints
- Một số dùng `Dict` thay vì `Dict[str, Any]`

**Ví dụ:**
```python
# data_quality_analysis.py
def load_summary(path: Path) -> Dict:  # Nên là Dict[str, Any]
    ...
```

**Khuyến nghị:**
- Thêm đầy đủ type hints
- Dùng `from typing import Dict, List, Any, Optional, Tuple`

---

## 4. Khuyến nghị cải thiện (Recommendations)

### 4.1. Tạo Package Structure

**Tạo các file:**
```
training/
├── __init__.py
├── trainer/
│   ├── __init__.py          # NEW
│   ├── config.py            # NEW - Central config
│   ├── utils.py             # NEW - Utility functions
│   ├── preprocessing.py
│   ├── clean_noise.py
│   ├── data_quality_analysis.py
│   ├── split_dataset.py
│   ├── build_tokenizer.py
│   └── tests/               # NEW
│       ├── __init__.py
│       ├── test_preprocessing.py
│       └── ...
```

**`training/trainer/__init__.py`:**
```python
"""Training pipeline utilities."""
from .preprocessing import Preprocessor, CleaningLevel
from .config import PreprocessingConfig, Paths

__all__ = [
    'Preprocessor',
    'CleaningLevel',
    'PreprocessingConfig',
    'Paths',
]
```

---

### 4.2. Tạo Config Module

**`training/trainer/config.py`:**
```python
"""Central configuration for training pipeline."""
from dataclasses import dataclass
from pathlib import Path
from .preprocessing import CleaningLevel

class Paths:
    """Centralized path constants."""
    ROOT = Path(__file__).resolve().parents[2]
    RAW_DIR = ROOT / "training" / "dataset" / "raw" / "truyenmoiii_output"
    PREPROCESSED_DIR = ROOT / "training" / "dataset" / "preprocessed"
    SPLITS_DIR = ROOT / "training" / "dataset" / "splits"
    TOKENIZER_DIR = ROOT / "training" / "tokenizer"
    MODEL_DIR = ROOT / "training" / "model"

@dataclass
class PreprocessingConfig:
    """Configuration for preprocessing."""
    min_paragraph_length: int = 50
    max_paragraph_length: int = 2000
    min_line_length: int = 10
    cleaning_level: CleaningLevel = CleaningLevel.BALANCED
    min_chapter_length: int = 500
    min_ratio: float = 0.1

@dataclass
class TokenizerConfig:
    """Configuration for tokenizer."""
    vocab_size: int = 32000
    model_type: str = "bpe"
    character_coverage: float = 0.9995
```

---

### 4.3. Tạo Utils Module

**`training/trainer/utils.py`:**
```python
"""Utility functions for training pipeline."""
import json
import sys
from pathlib import Path
from typing import Iterator, Dict, Any

def setup_encoding():
    """Setup UTF-8 encoding for Windows."""
    if sys.platform == 'win32':
        try:
            sys.stdout.reconfigure(encoding='utf-8')
            sys.stderr.reconfigure(encoding='utf-8')
        except Exception:
            pass

def read_jsonl(path: Path) -> Iterator[Dict[str, Any]]:
    """Read JSONL file with error handling."""
    with open(path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            if not line.strip():
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as e:
                print(f"⚠️  Lỗi parse JSON ở dòng {line_num}: {e}")
                continue

def write_jsonl(path: Path, records: Iterator[Dict[str, Any]]):
    """Write records to JSONL file."""
    with open(path, 'w', encoding='utf-8') as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
```

---

### 4.4. Cải thiện Logging

**Tạo `training/trainer/logger.py`:**
```python
"""Logging setup for training pipeline."""
import logging
import sys
from pathlib import Path

def setup_logger(name: str, log_file: Path = None, level=logging.INFO):
    """Setup logger with file and console handlers."""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger
```

**Sử dụng:**
```python
from .logger import setup_logger
logger = setup_logger(__name__)
logger.info("Đang đọc file...")
logger.warning("Lỗi parse JSON")
```

---

### 4.5. Tạo Requirements File

**`requirements.txt` (root):**
```
# Core dependencies
tqdm>=4.65.0,<5.0.0
sentencepiece>=0.1.99,<1.0.0

# Development dependencies (optional)
pytest>=7.0.0
pytest-cov>=4.0.0
black>=23.0.0
mypy>=1.0.0
```

---

## 5. Action Items (Ưu tiên)

### Priority 1 (Critical - Làm ngay)

1. **Tạo package structure**
   - Tạo `training/trainer/__init__.py`
   - Tạo `training/__init__.py`
   - Fix imports (bỏ `sys.path.append`)

2. **Tạo config module**
   - `training/trainer/config.py` với Paths và Config classes
   - Refactor scripts để dùng config

3. **Tạo utils module**
   - `training/trainer/utils.py` với common functions
   - Refactor duplicate code

### Priority 2 (Important - Làm sau)

4. **Cải thiện logging**
   - Tạo `logger.py`
   - Thay `print()` bằng `logger.info/warning/error`

5. **Tạo requirements.txt**
   - Root level requirements file
   - Pin versions

### Priority 3 (Nice to have)

6. **Tạo tests**
   - Unit tests cho mỗi module
   - Integration tests

7. **Documentation**
   - API documentation (Sphinx hoặc mkdocs)
   - Usage examples

---

## 6. Code Quality Metrics

### 6.1. Maintainability Score

| Metric | Score | Notes |
|--------|-------|-------|
| **Code Organization** | 8/10 | Tốt, nhưng thiếu package structure |
| **Documentation** | 9/10 | Rất tốt, docstrings đầy đủ |
| **Error Handling** | 7/10 | Tốt, nhưng thiếu structured logging |
| **Type Hints** | 8/10 | Tốt, nhưng một số chỗ thiếu |
| **Testing** | 0/10 | ❌ Chưa có tests |
| **Config Management** | 5/10 | ⚠️ Constants rải rác |
| **Dependencies** | 6/10 | ⚠️ Thiếu requirements.txt ở root |

**Overall: 6.1/10** - Tốt nhưng cần cải thiện

---

## 7. Kết luận

### 7.1. Điểm mạnh

✅ Code organization rõ ràng  
✅ Documentation đầy đủ  
✅ Error handling cơ bản tốt  
✅ CLI interface chuẩn  
✅ Reproducibility tốt  

### 7.2. Cần cải thiện

⚠️ Package structure (import paths)  
⚠️ Code duplication (utils module)  
⚠️ Config management (central config)  
⚠️ Logging system (structured logging)  
⚠️ Testing (chưa có tests)  

### 7.3. Khuyến nghị

**Ngắn hạn (1-2 ngày):**
1. Tạo package structure
2. Tạo config và utils modules
3. Refactor imports

**Trung hạn (1 tuần):**
4. Cải thiện logging
5. Tạo requirements.txt
6. Thêm type hints đầy đủ

**Dài hạn (1 tháng):**
7. Tạo unit tests
8. API documentation
9. CI/CD pipeline

---

**Tổng kết:** Codebase hiện tại **tốt về mặt functionality** nhưng cần **cải thiện về mặt structure và maintainability** để dễ update và mở rộng sau này.

