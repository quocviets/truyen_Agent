# 2025-01-21 – Cập nhật train_lm.py

## Mục tiêu
- Loại bỏ loss trên token padding để tránh model học “dự đoán PAD”.
- Đồng bộ lịch trình LR với số optimizer step thực tế (có gradient accumulation).
- Theo dõi meta dataset/pad_id để dễ audit khi chạy.

## Thay đổi chính
- `PackedTensorDataset` nhận `pad_token_id`, tạo `attention_mask` đúng và set `labels=-100` ở vị trí PAD.
- `train_cfg.pad_token_id` dùng xuyên suốt (dataset + model.config) để HF biết pad token.
- `total_train_steps` tính theo optimizer step: `ceil(len(loader) / grad_accum)`.
- Log meta từ `.pt` (seq_len, num_sequences, pad_id) để chắc chắn packer/trainer trùng config.
- Extract hàm `run_training(...)` để Kaggle runner/CLI có thể tái sử dụng logic huấn luyện chung.

## Kiểm thử
- Chưa chạy thực tế sau patch; cần chạy `python -m training.trainer.train_lm ...` để xác nhận trên GPU thật.

