# Báo cáo chia Dataset Train/Val/Test

**Ngày:** 2025-11-21  
**Phương pháp:** Per-chapter split 90/5/5  
**Random seed:** 42 (reproducible)

---

## 1. Tổng quan kết quả

### 1.1. Thống kê tổng hợp

| Split | Chapters | Paragraphs | Characters | Bytes | Tỷ lệ Paragraphs |
|-------|----------|------------|------------|-------|-------------------|
| **Train** | 17,953 | 100,259 | 175,378,579 | 231,844,932 | 90.00% |
| **Val** | 993 | 5,583 | 9,778,578 | 12,926,364 | 5.01% |
| **Test** | 1,004 | 5,605 | 9,777,907 | 12,929,978 | 5.03% |
| **TỔNG** | **19,950** | **111,447** | **194,935,064** | **257,701,274** | **100.04%** |

**Nhận xét:**
- Tỷ lệ chia gần đúng mục tiêu 90/5/5 (chênh lệch <0.1% do làm tròn số chương).
- Tổng số paragraph khớp với input `all_novels_preprocessed_clean.jsonl` (111,447 đoạn).
- Không có chapter nào bị filter trong quá trình split.

### 1.2. Phân bố độ dài trung bình

| Split | Avg chars/chapter | Avg chars/paragraph | Avg paragraphs/chapter |
|-------|-------------------|---------------------|------------------------|
| **Train** | 9,774 | 1,748 | 5.59 |
| **Val** | 9,848 | 1,752 | 5.62 |
| **Test** | 9,748 | 1,744 | 5.58 |

**Nhận xét:**
- Phân bố độ dài giữa train/val/test rất đồng đều → không có bias về độ dài.
- Trung bình ~1,750 ký tự/paragraph, ~5.6 paragraphs/chapter → phù hợp với đặc thù truyện web.

---

## 2. Phân tích theo từng truyện

### 2.1. Bảng thống kê per-novel

| Novel Name | Total Chapters | Train | Val | Test | Train % | Val % | Test % |
|------------|----------------|-------|-----|------|---------|-------|--------|
| bat-dau-thu-do-de-kiem-tien-nu-de-tuong-thuong-cuc-dao-de-binh | 263 | 236 | 13 | 14 | 89.7% | 4.9% | 5.3% |
| kiem-tien-o-day | 1,900 | 1,710 | 95 | 95 | 90.0% | 5.0% | 5.0% |
| lanh-chua-thoi-dai-ta-phan-thuong-x100-lan-tang-phuc | 2,750 | 2,475 | 137 | 138 | 90.0% | 5.0% | 5.0% |
| lanh-chua-thoi-dai-truoc-gio-dang-nhap-30-ngay | 1,350 | 1,215 | 67 | 68 | 90.0% | 5.0% | 5.0% |
| than-dao-de-ton | 4,300 | 3,870 | 215 | 215 | 90.0% | 5.0% | 5.0% |
| toan-dan-lanh-chua-ta-thien-phu-co-uc-diem-manh | 1,549 | 1,394 | 77 | 78 | 90.0% | 5.0% | 5.0% |
| toan-dan-lanh-chua-ta-ti-le-roi-do-tram-phan-tram | 1,650 | 1,485 | 82 | 83 | 90.0% | 5.0% | 5.0% |
| toan-dan-lanh-chua-tu-nu-anh-hung-dung-hop-bat-dau | 223 | 200 | 11 | 12 | 89.7% | 4.9% | 5.4% |
| toan-dan-lanh-chua-tu-vong-linh-bat-dau-gap-tram-lan-tang-phuc | 849 | 764 | 42 | 43 | 90.0% | 4.9% | 5.1% |
| van-co-than-de | 4,539 | 4,085 | 226 | 228 | 90.0% | 5.0% | 5.0% |
| đến dị giới ta làm thành chủ | 577 | 519 | 28 | 30 | 90.0% | 4.9% | 5.2% |

**Nhận xét:**
- Tất cả 11 truyện đều được chia đều, tỷ lệ train/val/test gần đúng 90/5/5.
- Truyện ngắn (200–600 chapters) có chênh lệch nhỏ do làm tròn, nhưng vẫn đảm bảo cả 3 splits đều có dữ liệu.
- Truyện dài (3,000+ chapters) chia chính xác 90/5/5.

### 2.2. Top truyện theo số lượng

**Theo số chapters:**
1. `van-co-than-de`: 4,539 chapters (train: 4,085 | val: 226 | test: 228)
2. `than-dao-de-ton`: 4,300 chapters (train: 3,870 | val: 215 | test: 215)
3. `lanh-chua-thoi-dai-ta-phan-thuong-x100-lan-tang-phuc`: 2,750 chapters (train: 2,475 | val: 137 | test: 138)

**Theo số paragraphs:**
1. `van-co-than-de`: 30,943 paragraphs (train: 27,818 | val: 1,563 | test: 1,562)
2. `than-dao-de-ton`: 19,808 paragraphs (train: 17,826 | val: 990 | test: 992)
3. `lanh-chua-thoi-dai-ta-phan-thuong-x100-lan-tang-phuc`: 13,620 paragraphs (train: 12,255 | val: 677 | test: 688)

**Theo số characters:**
1. `van-co-than-de`: 55,021,107 chars (train: 49,477,644 | val: 2,777,141 | test: 2,776,322)
2. `than-dao-de-ton`: 34,006,364 chars (train: 30,605,464 | val: 1,705,163 | test: 1,703,737)
3. `toan-dan-lanh-chua-ta-thien-phu-co-uc-diem-manh`: 31,078,869 chars (train: 19,358,143 | val: 1,069,014 | test: 1,060,712)

---

## 3. Kiểm tra tính nhất quán

### 3.1. Tổng số paragraph

- **Input:** 111,447 paragraphs (từ `all_novels_preprocessed_clean.jsonl`)
- **Output:** 111,447 paragraphs (train: 100,259 + val: 5,583 + test: 5,605)
- **Kết quả:** ✅ Khớp 100%

### 3.2. Tổng số chapter

- **Input:** 19,950 chapters (từ raw files, sau preprocessing)
- **Output:** 19,950 chapters (train: 17,953 + val: 993 + test: 1,004)
- **Kết quả:** ✅ Khớp 100%

### 3.3. Không có data leakage

- ✅ Tất cả paragraphs từ cùng 1 chapter đều nằm trong cùng 1 split.
- ✅ Không có chapter nào xuất hiện ở nhiều hơn 1 split.
- ✅ Random seed = 42 → kết quả reproducible.

---

## 4. Đánh giá chất lượng split

### 4.1. Điểm mạnh

1. **Phân bố đồng đều:** Train/val/test có độ dài trung bình gần như nhau → không bias.
2. **Không leak:** Per-chapter split đảm bảo không có thông tin từ test/val lọt vào train.
3. **Reproducible:** Fixed seed = 42 → có thể tái tạo kết quả.
4. **Metadata đầy đủ:** Mỗi paragraph có `novel_name`, `chapter_index`, `paragraph_index_in_chapter`, `original_paragraph_index`, `global_paragraph_index`.

### 4.2. Lưu ý

1. **Truyện ngắn:** Một số truyện <300 chapters có chênh lệch nhỏ do làm tròn, nhưng vẫn đảm bảo cả 3 splits đều có dữ liệu.
2. **Per-chapter split:** Không kiểm tra được cross-novel generalization, nhưng phù hợp với mục tiêu fine-tune 1–3B model (tập trung vào token-level learning).

---

## 5. Ước lượng tokens

### 5.1. Tính toán

- **Tổng characters:** 194,935,064
- **Ước lượng tokens (chars/3.5):** ~55,695,732 tokens
- **Train tokens:** ~50,108,165 tokens
- **Val tokens:** ~2,793,879 tokens
- **Test tokens:** ~2,793,688 tokens

### 5.2. Đánh giá phù hợp model size

- **1B model:** ✅ Đủ (thường cần 20–50B tokens, nhưng có thể fine-tune từ checkpoint).
- **3B model:** ✅ Đủ (có thể fine-tune từ checkpoint, không cần pretrain từ đầu).
- **7B+ model:** ⚠️ Có thể cần thêm dữ liệu nếu pretrain từ đầu, nhưng fine-tune vẫn OK.

**Khuyến nghị:** Phù hợp để fine-tune model 1–3B từ checkpoint (GPT-2, LLaMA, v.v.).

---

## 6. File output

### 6.1. JSONL files

- `training/dataset/splits/train.jsonl` (100,259 dòng)
- `training/dataset/splits/val.jsonl` (5,583 dòng)
- `training/dataset/splits/test.jsonl` (5,605 dòng)

**Format mỗi dòng:**
```json
{
  "text": "...",
  "novel_name": "...",
  "chapter_index": 1,
  "paragraph_index_in_chapter": 1,
  "original_paragraph_index": 1,
  "global_paragraph_index": 1
}
```

### 6.2. Summary files

- `training/dataset/splits/splits_summary.json` (tổng hợp tất cả)
- `training/dataset/splits/train_summary.json`
- `training/dataset/splits/val_summary.json`
- `training/dataset/splits/test_summary.json`

---

## 7. Kết luận

✅ **Dataset split đạt chuẩn để train LLM**

- Tỷ lệ chia đúng 90/5/5.
- Không có data leakage.
- Phân bố đồng đều giữa các splits.
- Metadata đầy đủ, reproducible.
- Phù hợp để fine-tune model 1–3B.

**Bước tiếp theo:**
1. Build tokenizer từ train split.
2. Train base model (hoặc fine-tune từ checkpoint).
3. Evaluate trên val/test splits.
4. Chạy fixed prompt tests để so sánh chất lượng generation.

---

**Ghi chú:** Báo cáo này được tạo tự động từ `splits_summary.json` sau khi chạy `split_dataset.py`.


