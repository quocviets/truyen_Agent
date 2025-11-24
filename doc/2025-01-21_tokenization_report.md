# Báo Cáo Tokenization (Text → Token IDs)

- **Ngày thực hiện:** 2025-01-21  
- **Thực hiện bởi:** GPT-5.1 Codex  
- **Script sử dụng:** `training/trainer/tokenize_dataset.py`

## 1. Lệnh đã chạy

```
python -m training.trainer.tokenize_dataset \
    --include-metadata \
    --show-progress
```

- Tokenizer: `training/tokenizer/sp_model.model` (SentencePiece BPE, vocab 32k).  
- Chạy trong venv sau khi cài `sentencepiece` và `tqdm` (theo `requirements.txt`).

## 2. Kết quả đầu ra

| Split | File output | Số bản ghi | Avg tokens | Max tokens |
| --- | --- | ---:| ---:| ---:|
| train | `training/dataset/tokenized/train_tokens.jsonl` | 100,259 | 438.8 | 1,138 |
| val   | `training/dataset/tokenized/val_tokens.jsonl`   | 5,583   | 439.4 | 559 |
| test  | `training/dataset/tokenized/test_tokens.jsonl`  | 5,605   | 437.7 | 557 |

- Mỗi dòng JSONL gồm:
  ```json
  {
    "input_ids": [...],
    "token_count": N,
    "split": "train|val|test",
    "novel_name": "...",
    "chapter_index": ...,
    "paragraph_index_in_chapter": ...,
    "original_paragraph_index": ...,
    "global_paragraph_index": ...
  }
  ```
- Metadata được giữ do dùng `--include-metadata`, thuận tiện cho debug/lọc theo truyện.

## 3. Nhận xét

1. **Chiều dài trung bình ~439 tokens** ⇒ dễ chọn context length 1024 hoặc 2048 cho training; max train là 1,138 nên 1,280/1,536 cũng đủ an toàn.
2. **JSONL thuần token IDs** ⇒ có thể dùng trực tiếp cho training loop (đọc line-by-line, pack theo batch) hoặc chuyển sang `.npz/.pt` nếu cần.
3. **Tốc độ**: train split ~4 phút (100k đoạn) khi bật progress bar; val/test mỗi cái <15 giây.

## 4. Việc tiếp theo gợi ý

- Nếu muốn giảm I/O khi training: cân nhắc chuyển `train_tokens.jsonl` sang `.npz` hoặc `.pt` với sequence packing.
- Bổ sung log token distribution (histogram) vào QA doc nếu cần theo dõi drift sau này.
- Khi update tokenizer (vocab size, model type), chạy lại script và cập nhật báo cáo này để theo dõi thay đổi.

