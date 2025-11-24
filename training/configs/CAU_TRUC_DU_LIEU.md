# 📁 CẤU TRÚC DỮ LIỆU - CHI TIẾT TỪNG BƯỚC

**Mục đích:** Xác định cấu trúc dữ liệu ở mỗi bước của pipeline, từ raw đến training-ready.

---

## 📋 TỔNG QUAN

### Pipeline Flow:
```
Raw Data → Preprocessed → Tokenized → Splits → Training
```

### Mỗi bước có cấu trúc riêng:
1. **Raw:** Chapter files riêng lẻ
2. **Preprocessed:** Text đã làm sạch (combined hoặc separate)
3. **Tokenized:** Text đã tokenize thành tokens
4. **Splits:** Train/Val/Test splits
5. **Training:** Dataset format cho model

---

## 🔹 BƯỚC 1: RAW DATA

### Cấu trúc hiện tại:
```
training/dataset/raw/truyenmoiii_output/
├── van-co-than-de/
│   ├── chapter_1.txt
│   ├── chapter_2.txt
│   ├── ...
│   ├── chapter_4550.txt
│   └── novel_summary.json
├── than-dao-de-ton/
│   ├── chapter_1.txt
│   ├── ...
│   └── novel_summary.json
└── ...
```

### Format file:
- **Chapter files:** Plain text, UTF-8 encoding
- **novel_summary.json:** Metadata (URLs, chapter list, ...)

### Đặc điểm:
- Mỗi chapter là một file riêng
- Không có preprocessing
- Có thể còn HTML tags, control characters

---

## 🔹 BƯỚC 2: PREPROCESSED DATA

### Cấu trúc đề xuất:

#### **Option A: COMBINED (1 file/truyện) - ⭐ ĐỀ XUẤT**

```
training/dataset/preprocessed/
├── van-co-than-de_preprocessed.txt
├── van-co-than-de_metadata.json
├── than-dao-de-ton_preprocessed.txt
├── than-dao-de-ton_metadata.json
├── ...
└── preprocessing_summary.json
```

**Format file:**

**1. `{novel_name}_preprocessed.txt`:**
```
Đoạn văn 1 từ chapter 1...

Đoạn văn 2 từ chapter 1...

Đoạn văn 1 từ chapter 2...

...
```

- Mỗi paragraph cách nhau bởi 2 newlines (`\n\n`)
- Không có separator giữa các chapter (chỉ dựa vào paragraph breaks)
- Encoding: UTF-8

**2. `{novel_name}_metadata.json`:**
```json
{
  "novel_name": "van-co-than-de",
  "total_chapters": 4550,
  "processed_chapters": 4543,
  "filtered_chapters": 7,
  "total_paragraphs": 125000,
  "total_chars": 8500000,
  "total_bytes": 8500000,
  "avg_chars_per_chapter": 1870,
  "avg_chars_per_paragraph": 68,
  "preprocessing_config": {
    "min_chapter_length": 500,
    "min_ratio": 0.1
  }
}
```

**3. `preprocessing_summary.json`:**
```json
{
  "preprocessing_config": {
    "min_chapter_length": 500,
    "min_ratio": 0.1
  },
  "statistics": {
    "total_novels": 11,
    "total_chapters": 19966,
    "processed_chapters": 19959,
    "filtered_chapters": 7,
    "total_chars": 50000000,
    "total_bytes": 50000000
  },
  "novels": {
    "van-co-than-de": { ... },
    "than-dao-de-ton": { ... },
    ...
  }
}
```

**Ưu điểm:**
- Đơn giản, dễ quản lý
- Dễ đọc toàn bộ truyện
- Phù hợp cho training (có thể đọc tuần tự)

**Nhược điểm:**
- File lớn (có thể vài trăm MB)
- Khó xử lý song song

---

#### **Option B: SEPARATE (Nhiều file/truyện)**

```
training/dataset/preprocessed/
├── van-co-than-de/
│   ├── chapter_00001.txt
│   ├── chapter_00002.txt
│   ├── ...
│   ├── chapter_04550.txt
│   └── metadata.json
├── than-dao-de-ton/
│   ├── chapter_00001.txt
│   ├── ...
│   └── metadata.json
├── ...
└── preprocessing_summary.json
```

**Format file:**

**1. `chapter_{number:05d}.txt`:**
```
Đoạn văn 1...

Đoạn văn 2...

...
```

- Mỗi file là một chapter đã preprocessed
- Format: `chapter_00001.txt`, `chapter_00002.txt`, ...
- Encoding: UTF-8

**2. `metadata.json` (trong mỗi folder):**
```json
{
  "novel_name": "van-co-than-de",
  "total_chapters": 4550,
  "processed_chapters": 4543,
  "filtered_chapters": 7,
  "total_paragraphs": 125000,
  "total_chars": 8500000,
  "total_bytes": 8500000
}
```

**Ưu điểm:**
- Dễ xử lý song song
- Dễ quản lý từng chapter
- File nhỏ, dễ load

**Nhược điểm:**
- Nhiều file, khó quản lý
- Tốn I/O khi đọc nhiều file

---

### **Khuyến nghị:** Option A (COMBINED) - ⭐

**Lý do:**
- Đơn giản, dễ quản lý
- Phù hợp cho training (đọc tuần tự)
- Dễ implement

---

## 🔹 BƯỚC 3: TOKENIZED DATA

### Cấu trúc đề xuất:

```
training/dataset/tokenized/
├── van-co-than-de_tokenized.pt
├── van-co-than-de_tokenized.json
├── than-dao-de-ton_tokenized.pt
├── than-dao-de-ton_tokenized.json
├── ...
├── tokenizer_config.json
└── tokenization_summary.json
```

### Format file:

**1. `{novel_name}_tokenized.pt` (PyTorch format):**
- Tensor chứa token IDs
- Shape: `[total_tokens]`
- Dtype: `torch.int32` hoặc `torch.int64`
- **Ví dụ:** `[101, 234, 567, ..., 102]`

**2. `{novel_name}_tokenized.json` (Metadata):**
```json
{
  "novel_name": "van-co-than-de",
  "total_tokens": 2000000,
  "total_chars": 8500000,
  "vocab_size": 50000,
  "tokenizer_type": "BPE",
  "special_tokens": {
    "bos": 101,
    "eos": 102,
    "pad": 0,
    "unk": 1
  },
  "chunk_info": [
    {
      "chunk_id": 0,
      "start_token": 0,
      "end_token": 512,
      "source_paragraph": 0
    },
    ...
  ]
}
```

**3. `tokenizer_config.json`:**
```json
{
  "tokenizer_type": "BPE",
  "vocab_size": 50000,
  "model_file": "tokenizer.model",
  "special_tokens": {
    "bos": "<|beginoftext|>",
    "eos": "<|endoftext|>",
    "pad": "<|pad|>",
    "unk": "<|unk|>"
  },
  "added_tokens": []
}
```

**4. `tokenization_summary.json`:**
```json
{
  "total_novels": 11,
  "total_tokens": 20000000,
  "vocab_size": 50000,
  "avg_tokens_per_chapter": 1000,
  "tokenizer_config": { ... }
}
```

---

## 🔹 BƯỚC 4: SPLITS (Train/Val/Test)

### Cấu trúc đề xuất:

```
training/dataset/splits/
├── train/
│   ├── train_data.pt
│   ├── train_metadata.json
│   └── train_indices.json
├── val/
│   ├── val_data.pt
│   ├── val_metadata.json
│   └── val_indices.json
├── test/
│   ├── test_data.pt
│   ├── test_metadata.json
│   └── test_indices.json
└── splits_config.json
```

### Format file:

**1. `{split}_data.pt` (PyTorch format):**
- Tensor chứa token IDs cho split đó
- Shape: `[num_samples, sequence_length]`
- Dtype: `torch.int32` hoặc `torch.int64`
- **Ví dụ:** `[[101, 234, ..., 102], [101, 567, ..., 102], ...]`

**2. `{split}_metadata.json`:**
```json
{
  "split": "train",
  "num_samples": 150000,
  "sequence_length": 512,
  "total_tokens": 76800000,
  "source_novels": [
    "van-co-than-de",
    "than-dao-de-ton",
    ...
  ]
}
```

**3. `{split}_indices.json`:**
```json
{
  "indices": [
    {
      "sample_id": 0,
      "novel": "van-co-than-de",
      "chunk_id": 0,
      "paragraph_id": 0
    },
    ...
  ]
}
```

**4. `splits_config.json`:**
```json
{
  "train_ratio": 0.8,
  "val_ratio": 0.1,
  "test_ratio": 0.1,
  "split_method": "sequential",  // hoặc "random"
  "sequence_length": 512,
  "stride": 256  // overlap cho sliding window
}
```

---

## 🔹 BƯỚC 5: TRAINING DATASET

### Cấu trúc đề xuất:

```
training/dataset/training/
├── dataset.pt
├── dataset_metadata.json
└── dataset_config.json
```

### Format file:

**1. `dataset.pt` (PyTorch Dataset):**
- Có thể dùng `torch.utils.data.Dataset`
- Hoặc lưu trực tiếp tensor

**2. `dataset_metadata.json`:**
```json
{
  "train_samples": 150000,
  "val_samples": 15000,
  "test_samples": 15000,
  "sequence_length": 512,
  "vocab_size": 50000,
  "total_tokens": 90000000
}
```

**3. `dataset_config.json`:**
```json
{
  "batch_size": 32,
  "sequence_length": 512,
  "vocab_size": 50000,
  "data_loader_config": {
    "shuffle": true,
    "num_workers": 4,
    "pin_memory": true
  }
}
```

---

## 📊 TỔNG KẾT CẤU TRÚC

### **Cấu trúc đầy đủ:**

```
training/dataset/
├── raw/
│   └── truyenmoiii_output/
│       ├── van-co-than-de/
│       │   ├── chapter_*.txt
│       │   └── novel_summary.json
│       └── ...
├── preprocessed/
│   ├── {novel}_preprocessed.txt
│   ├── {novel}_metadata.json
│   └── preprocessing_summary.json
├── tokenized/
│   ├── {novel}_tokenized.pt
│   ├── {novel}_tokenized.json
│   ├── tokenizer_config.json
│   └── tokenization_summary.json
├── splits/
│   ├── train/
│   │   ├── train_data.pt
│   │   ├── train_metadata.json
│   │   └── train_indices.json
│   ├── val/
│   └── test/
└── training/
    ├── dataset.pt
    ├── dataset_metadata.json
    └── dataset_config.json
```

---

## 🔄 QUY TRÌNH CHUYỂN ĐỔI

### **Raw → Preprocessed:**
```
chapter_*.txt → clean_text() → paragraphs → {novel}_preprocessed.txt
```

### **Preprocessed → Tokenized:**
```
{novel}_preprocessed.txt → tokenizer.encode() → token_ids → {novel}_tokenized.pt
```

### **Tokenized → Splits:**
```
{novel}_tokenized.pt → chunking (sliding window) → train/val/test splits
```

### **Splits → Training:**
```
train/val/test splits → PyTorch Dataset → DataLoader
```

---

## 📝 LƯU Ý QUAN TRỌNG

1. **Encoding:** Tất cả file text đều UTF-8
2. **Format:** Metadata luôn là JSON
3. **Tensor:** Dùng PyTorch format (.pt) cho tokenized data
4. **Naming:** Consistent naming convention
5. **Versioning:** Có thể thêm version number nếu cần

---

## 🎯 KẾT LUẬN

**Cấu trúc đề xuất:**
- **Raw:** Chapter files riêng lẻ
- **Preprocessed:** Combined format (1 file/truyện) - ⭐
- **Tokenized:** PyTorch tensor + JSON metadata
- **Splits:** Train/Val/Test với metadata
- **Training:** PyTorch Dataset format

**Lý do:**
- Đơn giản, dễ quản lý
- Phù hợp cho training
- Dễ debug và validate


