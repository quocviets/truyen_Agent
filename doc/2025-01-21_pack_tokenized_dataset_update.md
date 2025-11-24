# 2025-01-21 – Cập nhật pack_tokenized_dataset.py

## Mục tiêu
- Gia tăng an toàn dữ liệu khi pack token IDs → tensor.
- Cảnh báo rõ các trường hợp dễ gây nhiễu (stride nhỏ, remainder nhỏ, pad ID trùng `<unk>`).
- Ghi nhận meta thống kê hỗ trợ QA / audit pipeline.

## Thay đổi chính
- Thêm validate `input_ids`: bắt buộc list[int], đếm `invalid_records`/`empty_records`.
- Cảnh báo khi stride < seq_len (sliding window) và khi remainder quá nhỏ.
- Theo dõi thống kê `total_input_tokens`, `padded_sequences`, `dropped_tokens`, ghi kèm trong meta `.pt`.
- Bổ sung tùy chọn `--tokenizer-model` để auto lấy `pad_id`; fallback cảnh báo nếu pad trùng `<unk>`.
- Cho phép `--pad-token-id` = None và ghi rõ nguồn pad ID trong meta.

## Kiểm thử
- Chưa chạy thực tế (logic-only). Cần chạy `python -m training.trainer.pack_tokenized_dataset ...` để xác nhận trên dữ liệu thật.

