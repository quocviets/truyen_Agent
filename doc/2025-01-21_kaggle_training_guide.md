# Hướng Dẫn Train Trên Kaggle

- **Ngày:** 2025-01-21  
- **Mục tiêu:** Chạy training pipeline (pack + train) trên Kaggle GPU.

## 1. Chuẩn bị

1. **Upload dữ liệu**: Copy thư mục `training/dataset/tokenized/*.jsonl` (output từ bước tokenization) vào Kaggle Dataset hoặc Kaggle Files.
2. **Clone repo**:  
   ```bash
   !git clone https://github.com/<your-org>/AI_Agent.git
   %cd AI_Agent
   ```
3. **Cài dependency** (Kaggle đã cài sẵn torch/cuDNN):  
   ```bash
   !pip install -r requirements.txt
   ```
4. **Chọn GPU**: Trong Kaggle Notebook → Settings → GPU (T4/P100/V100).

## 2. Pack tokenized JSONL thành .pt

Chạy cho từng split (ví dụ seq_len=1024):

```bash
python -m training.trainer.pack_tokenized_dataset \
    --input training/dataset/tokenized/train_tokens.jsonl \
    --output training/dataset/tokenized/train_1024.pt \
    --seq-len 1024 \
    --stride 1024 \
    --show-progress

python -m training.trainer.pack_tokenized_dataset \
    --input training/dataset/tokenized/val_tokens.jsonl \
    --output training/dataset/tokenized/val_1024.pt \
    --seq-len 1024 \
    --stride 1024 \
    --show-progress --drop-remainder
```

Output `.pt` chứa tensor `[num_sequences, seq_len]` + metadata.

## 3. Cấu hình training

- File mẫu: `training/configs/training_config.json`
- Có thể chỉnh:
  - `model`: `n_layer`, `n_head`, `n_embd`, `vocab_size`, `n_positions`.
  - `training`: `batch_size`, `micro_batch_size`, `gradient_accumulation_steps`, `mixed_precision`, `warmup_steps`, `eval_every`, `save_every`.
  - `paths`: cập nhật đường dẫn `.pt` và thư mục output (Kaggle lưu ở `/kaggle/working/...`).

Ví dụ sửa nhanh trong notebook:

```python
import json
cfg_path = "training/configs/training_config.json"
cfg = json.load(open(cfg_path))
cfg["paths"]["train_bin"] = "training/dataset/tokenized/train_1024.pt"
cfg["paths"]["val_bin"] = "training/dataset/tokenized/val_1024.pt"
cfg["paths"]["output_dir"] = "/kaggle/working/350m_model"
json.dump(cfg, open(cfg_path, "w"), indent=2)
```

## 4. Huấn luyện

```bash
python -m training.trainer.train_lm \
    --config training/configs/training_config.json \
    --device cuda
```

- Script sẽ:
  - Load `.pt` → DataLoader (pin_memory, shuffle).
  - Tạo model GPT2Config (theo config).
  - Dùng AdamW + scheduler + gradient accumulation.
  - Mixed precision (bf16/fp16) nếu `mixed_precision` = `bf16` hoặc `fp16`.
  - Log loss mỗi `log_every`, eval mỗi `eval_every`, save checkpoint mỗi `save_every`.
  - Checkpoint được lưu vào `output_dir`:
    - `checkpoint_stepXXXX.pt`
    - `checkpoint_best.pt`
    - `hf_stepXXXX/` (format HuggingFace, dùng cho inference/agent).

## 5. Resume / Inference

- Resume:
  ```bash
  python -m training.trainer.train_lm \
      --config training/configs/training_config.json \
      --resume /kaggle/working/350m_model/checkpoint_step1000.pt
  ```
- Inference: load từ `hf_last/` hoặc `hf_best/` bằng `GPT2LMHeadModel.from_pretrained`.

## 6. Tips

- **Lớp học 350M**: `n_layer=24`, `n_head=16`, `n_embd=1024` → chạy T4 16GB ổn với `micro_batch_size=1`, `grad_accum=8`.
- **Mixed precision**: ưu tiên `bf16` (nếu GPU hỗ trợ) → ổn định hơn fp16.
- **Packing stride < seq_len** nếu muốn overlap (ví dụ stride=512) → tăng dữ liệu nhưng lâu hơn.
- **Upload checkpoints**: Kaggle Notebook → `Add data` → `Upload output` để lưu model.

## 7. Liên kết các script

| Bước | Script | Mục đích |
| --- | --- | --- |
| Tokenize | `training/trainer/tokenize_dataset.py` | Paragraph → token IDs JSONL |
| Pack | `training/trainer/pack_tokenized_dataset.py` | JSONL → `.pt` fixed length |
| Train | `training/trainer/train_lm.py` | Huấn luyện GPT (Kaggle GPU) |

Sau khi có checkpoint tốt, chuyển sang phase Agent (runtime) hoặc Distillation theo kế hoạch ở `PIPELINE_OVERVIEW.md`.

