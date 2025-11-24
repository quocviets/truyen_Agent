# Báo cáo Build Tokenizer

**Ngày:** 2025-11-21  
**Script:** `training/trainer/build_tokenizer.py`  
**Phương pháp:** SentencePiece (BPE)

---

## 1. Tổng quan

### 1.1. Mục tiêu

Xây dựng tokenizer phù hợp với tiếng Việt từ train split để chuẩn bị cho training model 1-3B parameters.

### 1.2. Kết quả

✅ **Tokenizer đã được train thành công**

---

## 2. Thông số kỹ thuật

### 2.1. Cấu hình training

| Tham số | Giá trị | Mô tả |
|---------|---------|-------|
| **Model type** | BPE | Byte Pair Encoding |
| **Vocab size** | 32,000 | Phù hợp model 1-3B |
| **Character coverage** | 0.9995 | Cao hơn tiếng Anh (có dấu) |
| **Normalization** | `nmt_nfkc_cf` | Unicode normalization + case folding |
| **Max sentence length** | 4,192 | Tối ưu cho paragraph truyện |
| **Special tokens** | `<pad>`, `<mask>` | (UNK, BOS, EOS có sẵn) |

### 2.2. Dữ liệu training

| Thống kê | Giá trị |
|----------|---------|
| **Training samples** | 100,259 paragraphs |
| **Total characters** | 175,378,579 chars |
| **Total bytes** | 231,844,932 bytes (~221 MB) |
| **Nguồn** | `training/dataset/splits/train.jsonl` (90% data) |
| **Lý do chỉ dùng train** | Tránh data leakage vào tokenizer |

---

## 3. Kết quả training

### 3.1. Files đã tạo

**Thư mục:** `training/tokenizer/`

| File | Mô tả | Kích thước |
|------|-------|------------|
| `sp_model.model` | SentencePiece model file (để load và sử dụng) | ~0.72 MB |
| `sp_model.vocab` | Vocab file (có thể đọc được, chứa tokens và scores) | ~1-2 MB |
| `tokenizer_info.json` | Metadata về tokenizer | <1 KB |

### 3.2. Tokenizer properties

| Property | Giá trị |
|----------|---------|
| **Vocab size** | 32,000 tokens |
| **UNK ID** | 0 |
| **BOS ID** | 1 (Start of sentence) |
| **EOS ID** | 2 (End of sentence) |
| **PAD ID** | -1 (chưa được set, cần config trong model) |

### 3.3. Compression ratio

Từ test samples:
- **Average compression:** ~4 chars/token
- **Range:** 3.87 - 4.11 chars/token

**Nhận xét:** Hợp lý cho tiếng Việt (có dấu, Unicode phức tạp hơn tiếng Anh).

---

## 4. Test results

### 4.1. Sample test (5 paragraphs)

**Kết quả:**
- ✅ Tokenizer encode/decode hoạt động đúng
- ⚠️ Round-trip có khác biệt nhỏ do normalization (NFKC + case folding)
  - **Lý do:** Normalization chuyển chữ hoa → chữ thường, normalize Unicode
  - **Kết luận:** Bình thường, không phải lỗi

**Ví dụ test:**
```
Original: "Chỉ bất quá, Đông Vực Thánh Vương Phủ..."
Tokens: ['▁chỉ', '▁bất', '▁quá', ',', '▁đông', '▁vực', ...]
Decoded: "chỉ bất quá, đông vực thánh vương phủ..."
```

**Thống kê sample:**
- Sample 1: 1,920 chars → 467 tokens (4.11 chars/token)
- Sample 2: 1,966 chars → 487 tokens (4.04 chars/token)
- Sample 3: 1,993 chars → 515 tokens (3.87 chars/token)
- Sample 4: 1,975 chars → 491 tokens (4.02 chars/token)
- Sample 5: 1,932 chars → 487 tokens (3.97 chars/token)

---

## 5. Đánh giá chất lượng

### 5.1. Điểm mạnh

✅ **Vocab size phù hợp:** 32k tokens đủ cho model 1-3B, không quá lớn  
✅ **Character coverage cao:** 0.9995 cover được hầu hết ký tự tiếng Việt  
✅ **BPE phù hợp:** Subword tokenization hiệu quả cho tiếng Việt  
✅ **Normalization hợp lý:** NFKC + case folding chuẩn cho multilingual  
✅ **Training data đủ:** 100k+ paragraphs đảm bảo tokenizer ổn định  

### 5.2. Lưu ý

⚠️ **PAD ID = -1:** Cần config trong model training (thường set = 0 hoặc vocab_size)  
⚠️ **Round-trip khác biệt:** Do normalization, không ảnh hưởng training  
⚠️ **Case folding:** Chữ hoa → chữ thường, có thể mất thông tin (nhưng phù hợp cho LM)  

---

## 6. Sử dụng tokenizer

### 6.1. Load tokenizer

```python
import sentencepiece as spm

sp = spm.SentencePieceProcessor()
sp.load('training/tokenizer/sp_model.model')
```

### 6.2. Encode text

```python
text = "Văn bản tiếng Việt"
tokens = sp.encode(text, out_type=str)  # List of subword tokens
token_ids = sp.encode(text, out_type=int)  # List of token IDs
```

### 6.3. Decode tokens

```python
decoded = sp.decode(tokens)  # Từ list tokens
decoded = sp.decode_ids(token_ids)  # Từ list token IDs
```

### 6.4. Thống kê

```python
vocab_size = sp.get_piece_size()  # 32000
unk_id = sp.unk_id()  # 0
bos_id = sp.bos_id()  # 1
eos_id = sp.eos_id()  # 2
```

---

## 7. So sánh với tiêu chuẩn

### 7.1. Vocab size

| Model size | Vocab size khuyến nghị | Tokenizer hiện tại |
|------------|------------------------|-------------------|
| 1B | 32k-50k | ✅ 32k |
| 3B | 32k-50k | ✅ 32k |
| 7B+ | 50k-100k | - |

**Kết luận:** Phù hợp cho model 1-3B.

### 7.2. Character coverage

| Ngôn ngữ | Coverage khuyến nghị | Tokenizer hiện tại |
|----------|----------------------|-------------------|
| Tiếng Anh | 0.9995 | - |
| Tiếng Việt | 0.9995+ | ✅ 0.9995 |

**Kết luận:** Đạt chuẩn.

---

## 8. Bước tiếp theo

### 8.1. Tokenize dataset

Tạo script tokenize train/val/test splits:
- Input: `train.jsonl`, `val.jsonl`, `test.jsonl`
- Output: Tokenized files (có thể là `.pt`, `.npy`, hoặc `.bin`)

### 8.2. Train model

Sử dụng tokenized data để train base model (StoryBaseModel).

### 8.3. Evaluate tokenizer

Test tokenizer trên val/test để verify quality:
- Perplexity trên val set
- Sample generation quality

---

## 9. Metadata

**File:** `training/tokenizer/tokenizer_info.json`

```json
{
  "tokenizer_type": "sentencepiece",
  "model_type": "bpe",
  "vocab_size": 32000,
  "character_coverage": 0.9995,
  "training_samples": 100259,
  "model_path": "training\\tokenizer\\sp_model.model",
  "vocab_path": "training\\tokenizer\\sp_model.vocab",
  "notes": [
    "Tokenizer được train từ train split (90% data)",
    "Phù hợp cho model 1-3B parameters",
    "Sử dụng BPE với character coverage cao cho tiếng Việt"
  ]
}
```

---

## 10. Kết luận

✅ **Tokenizer đã sẵn sàng để sử dụng**

- Vocab size: 32k (phù hợp model 1-3B)
- Character coverage: 0.9995 (đạt chuẩn tiếng Việt)
- Training data: 100k+ paragraphs (đủ để ổn định)
- Compression: ~4 chars/token (hợp lý)
- Test results: Encode/decode hoạt động đúng

**Trạng thái:** ✅ **Đạt chuẩn để tiếp tục pipeline**

---

**Ghi chú:** Tokenizer được train từ train split (90% data) để tránh data leakage. Val/test splits sẽ được tokenize sau khi tokenizer đã sẵn sàng.

