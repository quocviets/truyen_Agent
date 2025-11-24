# Ghi Chú: Script Tokenize Dataset

- **Ngày tạo:** 2025-01-21  
- **Script mới:** `training/trainer/tokenize_dataset.py`  
- **Mục tiêu:** Chuyển `train/val/test.jsonl` thành JSONL token IDs bằng SentencePiece.

## Chức năng chính

1. **Đọc splits chuẩn**
   - `training/dataset/splits/train.jsonl`
   - `val.jsonl`, `test.jsonl`
2. **Tokenize từng record**
   - Dùng `SentencePieceProcessor.encode(text, out_type=int)`
   - Ghi `input_ids`, `token_count`, optional metadata.
3. **Xuất JSONL**
   - Mặc định lưu tại `training/dataset/tokenized/{split}_tokens.jsonl`
   - Có thể chỉ định `--output-dir`.
4. **CLI tham số**
   - `--splits`: chọn split cần xử lý
   - `--tokenizer-model`: đường dẫn `.model`
   - `--include-metadata`: ghi kèm novel/chapter info
   - `--show-progress`: hiển thị tiến độ đọc file

## Lý do thiết kế

- Giữ nguyên SentencePiece (đã train) → đảm bảo đồng bộ token IDs.
- JSONL giúp các bước downstream (training, inspection) dễ thao tác.
- Không chạy tokenization ngay vì user yêu cầu “chỉ viết script”.

## Việc cần làm tiếp theo

- Sau khi sẵn sàng, chạy:  
  `python -m training.trainer.tokenize_dataset --include-metadata --show-progress`
- Cân nhắc bổ sung tuỳ chọn packing hoặc lưu `.npz/.pt` trong tương lai.

