# 2025-01-21 – Kaggle Dataset Bundle & Runner

## Mục tiêu
- Trả lời câu hỏi “cần upload những file nào lên Kaggle để train”.
- Tạo script **prepare_kaggle_bundle.py** gom toàn bộ artifact cần thiết thành một thư mục/zip duy nhất.
- Cung cấp **kaggle_entry.py** (one-click runner) để pack `.pt` + gọi `train_lm` trực tiếp trong môi trường Kaggle.

## File nên xuất hiện trong Kaggle dataset
| Nhóm | Đường dẫn trong bundle | Ghi chú |
| --- | --- | --- |
| Config | `config/training_config.json` | Toàn bộ script đọc chung file này |
| Tokenizer | `tokenizer/sp_model.model`, `sp_model.vocab`, `tokenizer_info.json` | Dùng cho tokenization + pad_id |
| Splits | `dataset/splits/train.jsonl`, `val.jsonl`, `test.jsonl` | Giữ nguyên phân đoạn 90/5/5 |
| Tokenized | `dataset/tokenized/train_tokens.jsonl`, `val_tokens.jsonl`, `test_tokens.jsonl` | Đầu vào cho packer trên Kaggle |
| (Optional) QA | `reports/preprocessing_summary.json`, `clean_noise_report.json`, `*_summary.json` | Giúp audit khi cần |
| (Optional) Preprocessed | `dataset/preprocessed/all_novels_preprocessed_clean.jsonl` | Phòng trường hợp phải re-tokenize |

## Script mới
1. `training/trainer/prepare_kaggle_bundle.py`
   - Copy các file cốt lõi vào `training/kaggle_bundle/`.
   - Flags: `--include-reports`, `--include-preprocessed`, `--include-extra`, `--zip`.
   - Sinh `bundle_manifest.json` liệt kê file gốc & file thiếu.

2. `training/trainer/kaggle_entry.py`
   - Nhận `--dataset-root`, `--work-dir`, `--seq-len`, `--stride`, `--skip-pack`, `--skip-train`...
   - Tự pack JSONL → `.pt` (dùng chung `pack_sequences`) và gọi `train_lm.run_training`.
   - Cho phép override pad token, resume checkpoint, hoặc chỉ pack mà chưa train.

3. `training/trainer/train_lm.py`
   - Tách logic thành hàm `run_training(...)` để Kaggle runner tái sử dụng trực tiếp.
   - Không thay đổi CLI hiện tại (vẫn dùng `python -m training.trainer.train_lm ...` như cũ).

## Hướng dẫn sử dụng nhanh
```bash
# 1) Tạo gói upload
python -m training.trainer.prepare_kaggle_bundle --include-reports --zip

# 2) Trên Kaggle Notebook
!python -m training.trainer.kaggle_entry \
    --dataset-root /kaggle/input/novel-lm-dataset \
    --seq-len 1024 --stride 1024 --show-progress
```

Sau khi chạy xong, checkpoint sẽ nằm tại `/kaggle/working/model_output`.

