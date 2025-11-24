## 2025-11-21 – PIPELINE OVERVIEW UPDATE

- Yêu cầu: Ghi lại pipeline theo các pha (0-4).
- Thực hiện:
  - Tạo file `training/PIPELINE_OVERVIEW.md` mô tả Phase 0 → Phase 4.
  - Mỗi phase liệt kê các bước chính (data check, offline learning, writer agent, distillation, vận hành).
- Ghi chú:
  - Đây là tài liệu định hướng, không chạy code.
  - Dữ liệu raw đã OK, JSON issue bỏ qua.

## 2025-11-21 – PREPROCESSOR IMPROVEMENTS

- Tối ưu `training/trainer/preprocessing.py` theo review:
  - Chuẩn hóa `DIALOGUE_PATTERN`, cho phép đoạn 30-49 ký tự nếu có dấu câu.
  - `is_dialogue_line()` hỗ trợ tham số `allow_longer`.
  - Ghi log lý do filter chương + lưu vào summary.
  - Thêm tùy chọn `--global-jsonl` để gộp toàn bộ paragraph vào `all_novels_preprocessed.jsonl`.
  - Lưu cấu hình/ thống kê mới (relaxed length, global JSONL, filter reasons) trong summary.

