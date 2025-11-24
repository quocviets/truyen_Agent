# Báo cáo Implementation: Build Tokenizer

**Ngày:** 2025-11-21  
**Script:** `training/trainer/build_tokenizer.py`  
**Phương pháp:** SentencePiece (BPE)

---

## 1. Tổng quan

### 1.1. Mục tiêu

Tạo tokenizer phù hợp với tiếng Việt từ train split để chuẩn bị cho training model 1-3B parameters.

### 1.2. Lựa chọn công nghệ

**SentencePiece (BPE):**
- ✅ Hỗ trợ tiếng Việt tốt (Unicode, dấu)
- ✅ Subword tokenization hiệu quả
- ✅ Được dùng trong nhiều model lớn (T5, mT5, LLaMA)
- ✅ Character coverage cao (0.9995) phù hợp tiếng Việt

**Vocab size:** 32,000 tokens (phù hợp model 1-3B)

---

## 2. Chi tiết implementation

### 2.1. Input

- **File:** `training/dataset/splits/train.jsonl`
- **Nội dung:** 100,259 paragraphs từ train split (90% data)
- **Format:** Mỗi dòng là JSON với field `text`

### 2.2. Quy trình

1. **Load texts:** Đọc `train.jsonl`, extract text từ mỗi paragraph
2. **Tạo file tạm:** Ghi tất cả texts vào file tạm (1 dòng = 1 paragraph)
3. **Train SentencePiece:**
   - Model type: BPE (Byte Pair Encoding)
   - Vocab size: 32,000 (có thể tùy chỉnh)
   - Character coverage: 0.9995 (cao hơn tiếng Anh vì có dấu)
   - Normalization: `nmt_nfkc_cf` (Unicode normalization)
   - Special tokens: `<pad>`, `<unk>`, `<s>`, `</s>`, `<mask>`
   - Seed: 42 (reproducible)
4. **Test tokenizer:** Encode/decode sample texts để verify
5. **Lưu metadata:** Ghi `tokenizer_info.json` với thông tin training

### 2.3. Output

**Thư mục:** `training/tokenizer/`

**Files:**
- `sp_model.model`: SentencePiece model file
- `sp_model.vocab`: Vocab file (có thể đọc được)
- `tokenizer_info.json`: Metadata về tokenizer

### 2.4. CLI Arguments

```bash
python training/trainer/build_tokenizer.py \
    --input-jsonl training/dataset/splits/train.jsonl \
    --output-dir training/tokenizer \
    --vocab-size 32000 \
    --model-type bpe \
    --character-coverage 0.9995 \
    --test-samples 5
```

**Arguments:**
- `--input-jsonl`: File train.jsonl (default: `training/dataset/splits/train.jsonl`)
- `--output-dir`: Thư mục lưu tokenizer (default: `training/tokenizer`)
- `--vocab-size`: Vocab size (default: 32000)
- `--model-type`: `bpe` hoặc `unigram` (default: `bpe`)
- `--character-coverage`: Character coverage (default: 0.9995)
- `--test-samples`: Số sample để test (default: 5)

---

## 3. Các hàm chính

### 3.1. `load_train_texts(input_jsonl: Path) -> List[str]`

Đọc file `train.jsonl` và extract text từ mỗi paragraph.

**Xử lý lỗi:**
- Bỏ qua dòng trống
- Log warning nếu parse JSON lỗi
- Trả về list các đoạn text

### 3.2. `train_tokenizer(...) -> Path`

Train SentencePiece tokenizer từ danh sách texts.

**Tham số quan trọng:**
- `normalization_rule_name='nmt_nfkc_cf'`: Normalize Unicode
- `remove_extra_whitespaces=True`: Xóa whitespace thừa
- `user_defined_symbols`: Special tokens cho training
- `shuffle_input_sentence=True`: Shuffle để training ổn định
- `seed_sentencepiece=42`: Reproducible
- `max_sentence_length=4192`: Tối ưu cho text dài (truyện)

### 3.3. `test_tokenizer(model_path: Path, texts: List[str], num_samples: int)`

Test tokenizer trên sample texts:
- Encode text → tokens
- Decode tokens → text
- Kiểm tra round-trip (có thể khác do normalization)
- Thống kê: token count, compression ratio

### 3.4. `save_tokenizer_info(...)`

Lưu metadata về tokenizer vào `tokenizer_info.json`:
- Tokenizer type, model type
- Vocab size, character coverage
- Số samples training
- Đường dẫn model/vocab
- Notes

---

## 4. Sử dụng tokenizer

### 4.1. Load tokenizer

```python
import sentencepiece as spm

sp = spm.SentencePieceProcessor()
sp.load('training/tokenizer/sp_model.model')
```

### 4.2. Encode text

```python
text = "Đây là một đoạn văn tiếng Việt."
tokens = sp.encode(text, out_type=str)  # List of subword tokens
token_ids = sp.encode(text, out_type=int)  # List of token IDs
```

### 4.3. Decode tokens

```python
decoded = sp.decode(tokens)  # Từ list tokens
decoded = sp.decode_ids(token_ids)  # Từ list token IDs
```

### 4.4. Thống kê

```python
vocab_size = sp.get_piece_size()  # Vocab size
unk_id = sp.unk_id()  # UNK token ID
pad_id = sp.pad_id()  # PAD token ID
```

---

## 5. Lưu ý kỹ thuật

### 5.1. Character Coverage

- **Tiếng Anh:** 0.9995 (đủ cho ASCII)
- **Tiếng Việt:** 0.9995 (cần cao hơn vì có dấu, Unicode phức tạp)

### 5.2. Vocab Size

- **1B model:** 32k-50k tokens
- **3B model:** 32k-50k tokens
- **7B+ model:** 50k-100k tokens

**Khuyến nghị:** 32k cho model 1-3B (đủ để cover tiếng Việt, không quá lớn)

### 5.3. Normalization

`nmt_nfkc_cf` (NFKC + case folding):
- Normalize Unicode (ví dụ: é → e + ́)
- Case folding (A → a)
- Phù hợp cho multilingual models

### 5.4. Special Tokens

- `<pad>`: Padding token
- `<unk>`: Unknown token
- `<s>`: Start of sentence
- `</s>`: End of sentence
- `<mask>`: Mask token (cho masked LM nếu cần)

---

## 6. Bước tiếp theo

Sau khi build tokenizer xong:

1. **Tokenize dataset:** Tạo script tokenize train/val/test splits
2. **Train model:** Sử dụng tokenized data để train base model
3. **Evaluate:** Test tokenizer trên val/test để verify quality

---

## 7. Dependencies

Thêm vào `requirements_preprocessing.txt`:
```
sentencepiece>=0.1.99
```

Cài đặt:
```bash
pip install sentencepiece>=0.1.99
```

---

**Ghi chú:** Script này chỉ train tokenizer từ train split (90% data) để tránh data leakage. Val/test splits sẽ được tokenize sau khi tokenizer đã sẵn sàng.


