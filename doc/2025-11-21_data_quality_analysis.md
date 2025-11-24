## 2025-11-21 – DATA QUALITY QA (8-STEP CHECKLIST)

- **Input**:
  - `training/dataset/preprocessed/preprocessing_summary.json`
  - `training/dataset/preprocessed/all_novels_preprocessed.jsonl`
- **Script**: `training/trainer/data_quality_analysis.py --seed 42`

### 1. Sanity check số liệu tổng
- Tổng chương: 19,966 (processed 19,950, filtered 16 → 0.08%)
- Tổng đoạn: 111,447 | Tổng ký tự: 194,944,771 (~55.7M tokens)
- Không phát hiện mất dữ liệu (processed = total - filtered).

### 2. Phân bố độ dài paragraph
- Min/Max: 1 / 3,731 ký tự
- Mean/Median/Std: 1,749 / 1,932 / 470
- Percentiles: P10=930, P25=1,849, P50=1,932, P75=1,971, P90=1,989, P95=1,994, P99=1,999
- Bucket:
  - `<50`: 181 (0.16%)
  - `50-200`: 2,249 (2.02%)
  - `200-500`: 4,450 (3.99%)
  - `500-1000`: 4,786 (4.29%)
  - `1000-2000`: 99,487 (89.27%)
  - `>2000`: 294 (0.26%)
- Nhận xét: tập trung mạnh ở 1,8–2,0k ký tự, ít đoạn quá ngắn/dài → ổn định cho tokenizer.

### 3. Phân tích theo từng truyện
- Không truyện nào bị mất quá 1% chương; ngoại lệ:
  - `van-co-than-de`: lọc 11/4,550 chương (~0.24%)
  - `đến dị giới ta làm thành chủ`: lọc 3/580 (0.5%)
  - `toan-dan-lanh-chua-ta-thien-phu-co-uc-diem-manh`: lọc 1 chương
  - `toan-dan-lanh-chua-tu-vong-linh-bat-dau-gap-tram-lan-tang-phuc`: lọc 1 chương
- `avg_chars_per_chapter` dao động 6.9k–13.9k → hợp lý, không có outlier cực đoan.

### 4. Noise / hard patterns
- Pattern counts /1k đoạn:
  - `http`: 125 occurrences (1.12/1k đoạn)
  - `https`: 23 (0.21/1k)
  - `website`: 719 (6.45/1k) → cần xem lại nguồn/credit
  - `<`/`>` tổng 30 lần → nhỏ
  - `&nbsp`, `&amp`: hầu như không đáng kể

### 5. Ký tự không hợp lệ
- Control chars: 0 (đã sạch)
- Foreign chars (CJK/Hiragana/Katakana): 355 ký tự, ví dụ `歘`, `ェ`, `ヾ`, `芔`, `茻`
  - Cần quyết định giữ hay lọc khi tokenizer (có thể là từ ngoại ngữ đặc biệt).

### 6. Duplicate paragraphs
- 1,932 trùng lặp → 1.73% tổng số đoạn (<5% ngưỡng cảnh báo).

### 7. Spot-check
- 6 đoạn ngắn, 7 trung bình, 7 dài → nội dung đọc tự nhiên, dấu câu đầy đủ, không thấy split lỗi.

### 8. Ước lượng tokens
- ~55.7M tokens.
- Đủ để fine-tune model 1–3B hoặc làm bổ sung cho 7B (nếu mix với corpora khác).

### Cảnh báo & kết luận
- Cảnh báo:
  1. Xuất hiện pattern `http/https/website` → cần rà soát attribution/noise.
  2. Có ký tự CJK/Hiragana/Katakana (355 ký tự) → cần quyết định xử lý trước khi tokenize.
- Kết luận: dataset **cần kiểm tra bổ sung** đối với hai cảnh báo trên, sau đó có thể sử dụng để train/fine-tune LLM.

### Gợi ý cải thiện
1. Viết bước lọc tự động các pattern `http|website|Nguồn` (regex) trước khi tokenize.
2. Lưu danh sách chương bị filter và các đoạn chứa ký tự ngoại để review thủ công.
3. Quy định chính sách với ký tự ngoài Latin (giữ nguyên hay chuẩn hóa) để tokenizer hoạt động ổn định.

---

## 2025-11-21 (Chiều) – CLEAN NOISE + QA LẦN 2

- **Bước làm sạch**: `python training/trainer/clean_noise.py --input all_novels_preprocessed.jsonl --output all_novels_preprocessed_clean.jsonl`
  - URLs xóa: 119, bare `http/https`: 6
  - `website` occurrences xóa: 719, `Nguồn:`: 2
  - Ký tự CJK/Hiragana/Katakana xóa: 355
  - 103,117/111,447 đoạn bị chạm (normalize whitespace, bỏ noise)
  - Báo cáo chi tiết: `training/dataset/preprocessed/clean_noise_report.json`
- **QA lại**: `python training/trainer/data_quality_analysis.py --jsonl-file ..._clean.jsonl`

### Kết quả chính
- Thống kê tổng không thay đổi (giữ 111,447 đoạn, ~55.7M tokens).
- Noise patterns: `http/https/website/Nguồn/< >/&nbsp/&amp` đều bằng 0.
- Foreign chars: 0; Control chars: 0.
- Duplicate giữ nguyên 1.73%.
- Spot-check 20 đoạn vẫn ổn, không bị gãy cấu trúc.
- **Cảnh báo: không còn** → Dataset chính thức “đạt chuẩn để train LLM”.

### Ghi chú sử dụng
- Dữ liệu sạch cho các bước tiếp theo: `training/dataset/preprocessed/all_novels_preprocessed_clean.jsonl`
- Giữ cả bản gốc + bản clean để đối chiếu khi cần audit.
- Khi tokenizer/training, ưu tiên dùng bản `_clean` để tránh noise quay lại.

### Fine-tune 2025-11-21 (tối) – Bảo toàn xuống dòng & audit bổ sung
- Update `clean_noise.py`:
  - Normalize whitespace nhưng giữ nguyên `\n` (hội thoại/ thơ không bị dính liền).
  - Regex mới bắt cả `Nguon:` không dấu.
  - `clean_noise_report.json` log thêm `novel_name` + `paragraph_index` cho mẫu bị chỉnh.
- **Output chính**:
  - JSONL sạch: `training/dataset/preprocessed/all_novels_preprocessed_clean.jsonl`
  - Báo cáo: `training/dataset/preprocessed/clean_noise_report.json`
    - Tổng đoạn: 111 447 | Đoạn bị chỉnh: 1 135
    - URL xóa: 119 | `http/https` rời: 6 | `website`: 719 | `Nguồn/Nguon`: 2
    - Foreign chars xóa: 355 | Normalize whitespace: 940 đoạn
    - Mục `samples` chứa tối đa 20 đoạn (kèm `novel_name`, `paragraph_index`, preview trước/sau)
- Re-run QA với file `_clean` → noise counters vẫn = 0, dataset tiếp tục “đạt chuẩn để train LLM”.

## Chiến lược chia train/val/test (2025-11-21)

- **Lý do chọn per-chapter split 90/5/5**
  - Dữ liệu mỗi tập ổn định, train/val/test cùng domain → loss đo được tín hiệu rõ ràng.
  - Phù hợp mục tiêu fine-tune model 1–3B: cần kiểm soát token-level learning hơn là generalization cross-novel.
  - Per-novel split tuy kiểm tra được cross-novel nhưng test quá khó, dữ liệu ít → không phù hợp giai đoạn này.

- **Quy tắc thực thi**
  1. Đọc `training/dataset/preprocessed/all_novels_preprocessed_clean.jsonl`.
  2. Group paragraph theo `novel_name`, `chapter_index`, `paragraph_index`.
  3. Với từng truyện: sắp xếp theo chapter → chia 90% chương đầu vào train, 5% vào val, 5% vào test (seed=42 để reproducible). Không cắt nhỏ chương.
  4. Gộp tất cả truyện để tạo 3 file:
     - `training/dataset/splits/train.jsonl`
     - `training/dataset/splits/val.jsonl`
     - `training/dataset/splits/test.jsonl`
  5. Ghi `splits_summary.json` (chứa số truyện/chapter/paragraph mỗi tập).
  6. QA lại từng file (noise, duplicate, length distribution) để đảm bảo không leak.

- **Policy đánh giá model**
  - Training: theo dõi train loss ↓ đều, val loss ↓ rồi phẳng; tránh train ↓ nhưng val ↑ (dấu hiệu overfit/leak).
  - Sau train: báo cáo test loss & perplexity. Thang tham chiếu cho truyện web:
    - PPL 20–40: rất tốt.
    - 40–80: chấp nhận được.
    - >100: mô hình học kém hoặc dữ liệu chưa chuẩn.
  - Bổ sung bộ prompt test cố định (5 tình huống webnovel: mở đầu bị từ hôn, chiến đấu vượt cấp, đối thoại sư đồ, đột phá Trúc Cơ→Kim Đan, bước vào bí cảnh) để so sánh đầu ra base vs fine-tune bằng mắt.

- **Ghi chú**
  - Sau khi hoàn tất split, mới tiến hành tokenizer/training để tránh phải làm lại.
  - Prompt test được lưu riêng trong `agent/runtime/prompts/` (sẽ tạo sau khi chuẩn bị splits).
