"""
Huấn luyện GPT-style LM trên dữ liệu đã pack (.pt) – tối ưu cho Kaggle GPU.

Pipeline:
1. Tokenize paragraphs → training/trainer/tokenize_dataset.py
2. Pack thành fixed-length sequences → training/trainer/pack_tokenized_dataset.py
3. Train model → script này (train_lm.py)
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Dict, Optional

import torch
from torch.utils.data import DataLoader, Dataset
from transformers import (
    GPT2Config,
    GPT2LMHeadModel,
    get_linear_schedule_with_warmup,
)

from .utils import ensure_dir, setup_encoding


class PackedTensorDataset(Dataset):
    """Dataset đọc tensor sequences (shape [N, seq_len]) và trả về causal labels."""

    def __init__(self, tensor_path: Path, pad_token_id: int = 0):
        if not tensor_path.exists():
            raise FileNotFoundError(f"Không tìm thấy tensor: {tensor_path}")
        payload = torch.load(tensor_path)
        if "input_ids" not in payload:
            raise KeyError(f"File {tensor_path} không chứa key 'input_ids'")
        self.input_ids = payload["input_ids"].long()
        self.meta = payload.get("meta", {})
        self.pad_token_id = pad_token_id

    def __len__(self) -> int:
        return self.input_ids.size(0)

    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        ids = self.input_ids[idx]
        attention_mask = (ids != self.pad_token_id).long()
        labels = ids.clone()
        labels[ids == self.pad_token_id] = -100  # bỏ padding khỏi loss
        return {
            "input_ids": ids,
            "labels": labels,
            "attention_mask": attention_mask,
        }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train GPT LM trên packed dataset (.pt).")
    parser.add_argument("--config", type=Path, default=Path("training/configs/training_config.json"))
    parser.add_argument("--train-bin", type=Path, help="Override đường dẫn train .pt")
    parser.add_argument("--val-bin", type=Path, help="Override đường dẫn val .pt")
    parser.add_argument("--output-dir", type=Path, help="Override output dir")
    parser.add_argument("--resume", type=Path, help="Checkpoint .pt để resume")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--device", type=str, default="cuda" if torch.cuda.is_available() else "cpu")
    return parser.parse_args()


def set_seed(seed: int) -> None:
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def load_config(path: Path) -> Dict:
    if not path.exists():
        raise FileNotFoundError(f"Không tìm thấy config: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_model(cfg: Dict) -> GPT2LMHeadModel:
    model_cfg = GPT2Config(
        vocab_size=cfg["vocab_size"],
        n_positions=cfg.get("n_positions", cfg.get("n_ctx", 1024)),
        n_ctx=cfg.get("n_ctx", 1024),
        n_embd=cfg.get("n_embd", 1024),
        n_layer=cfg.get("n_layer", 24),
        n_head=cfg.get("n_head", 16),
        layer_norm_epsilon=cfg.get("layer_norm_epsilon", 1e-5),
        resid_pdrop=cfg.get("resid_pdrop", 0.1),
        embd_pdrop=cfg.get("embd_pdrop", 0.1),
        attn_pdrop=cfg.get("attn_pdrop", 0.1),
    )
    return GPT2LMHeadModel(model_cfg)


def evaluate(model, dataloader, device) -> float:
    model.eval()
    loss_sum = 0.0
    total = 0
    with torch.no_grad():
        for batch in dataloader:
            batch = {k: v.to(device) for k, v in batch.items()}
            outputs = model(**batch)
            loss = outputs.loss
            bs = batch["input_ids"].size(0)
            loss_sum += loss.item() * bs
            total += bs
    model.train()
    return loss_sum / max(total, 1)


def save_checkpoint(model, optimizer, scheduler, step: int, output_dir: Path, tag: str) -> None:
    ensure_dir(output_dir)
    ckpt_path = output_dir / f"checkpoint_{tag}.pt"
    torch.save(
        {
            "model_state": model.state_dict(),
            "optimizer_state": optimizer.state_dict(),
            "scheduler_state": scheduler.state_dict() if scheduler else None,
            "step": step,
        },
        ckpt_path,
    )
    model.save_pretrained(output_dir / f"hf_{tag}")


def run_training(
    config_path: Path,
    train_bin_override: Optional[Path] = None,
    val_bin_override: Optional[Path] = None,
    output_dir_override: Optional[Path] = None,
    resume: Optional[Path] = None,
    seed: int = 42,
    device_str: Optional[str] = None,
) -> None:
    """Run LM training either from CLI or programmatic caller."""
    setup_encoding()
    config = load_config(config_path)

    model_cfg = config.get("model", {})
    train_cfg = config.get("training", {})
    path_cfg = config.get("paths", {})

    train_bin = Path(train_bin_override or path_cfg.get("train_bin", "train.pt"))
    val_bin = Path(val_bin_override or path_cfg.get("val_bin", "val.pt"))
    output_dir = Path(output_dir_override or path_cfg.get("output_dir", "training/model/output"))

    ensure_dir(output_dir)
    set_seed(seed)

    print(f"🔁 Loading datasets: {train_bin} / {val_bin}")
    pad_token_id = train_cfg.get("pad_token_id", 0)
    train_ds = PackedTensorDataset(train_bin, pad_token_id=pad_token_id)
    val_ds = PackedTensorDataset(val_bin, pad_token_id=pad_token_id)
    if train_ds.meta:
        print(
            f"📊 train meta → seq_len={train_ds.meta.get('seq_len')} | "
            f"num_sequences={train_ds.meta.get('num_sequences')} | pad_id={pad_token_id}"
        )
    if val_ds.meta:
        print(
            f"📊 val meta   → seq_len={val_ds.meta.get('seq_len')} | "
            f"num_sequences={val_ds.meta.get('num_sequences')}"
        )

    micro_batch_size = train_cfg.get("micro_batch_size", 1)
    train_loader = DataLoader(train_ds, batch_size=micro_batch_size, shuffle=True, pin_memory=True)
    val_loader = DataLoader(val_ds, batch_size=micro_batch_size, shuffle=False, pin_memory=True)

    if device_str is None:
        device_str = "cuda" if torch.cuda.is_available() else "cpu"
    device = torch.device(device_str)
    model = build_model(model_cfg).to(device)
    if not hasattr(model.config, "pad_token_id") or model.config.pad_token_id is None:
        model.config.pad_token_id = pad_token_id

    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=train_cfg.get("learning_rate", 3e-4),
        weight_decay=train_cfg.get("weight_decay", 0.1),
        betas=(0.9, 0.95),
    )

    max_steps = train_cfg.get("max_steps", 0)
    num_epochs = train_cfg.get("num_epochs", 1)
    grad_accum = train_cfg.get("gradient_accumulation_steps", 1)
    steps_per_epoch = math.ceil(len(train_loader) / max(grad_accum, 1))
    total_train_steps = max_steps or num_epochs * steps_per_epoch
    scheduler = get_linear_schedule_with_warmup(
        optimizer,
        num_warmup_steps=train_cfg.get("warmup_steps", 1000),
        num_training_steps=total_train_steps,
    )

    clip_norm = train_cfg.get("clip_grad_norm", 1.0)
    log_every = train_cfg.get("log_every", 50)
    eval_every = train_cfg.get("eval_every", 500)
    save_every = train_cfg.get("save_every", 1000)
    mixed_precision = train_cfg.get("mixed_precision", "").lower()

    use_amp = mixed_precision in {"fp16", "bf16"} and torch.cuda.is_available()
    amp_dtype = torch.float16 if mixed_precision == "fp16" else torch.bfloat16
    scaler = torch.cuda.amp.GradScaler(enabled=use_amp and mixed_precision == "fp16")

    global_step = 0
    best_val = float("inf")

    if resume:
        ckpt = torch.load(resume, map_location=device)
        model.load_state_dict(ckpt["model_state"])
        optimizer.load_state_dict(ckpt["optimizer_state"])
        if scheduler and ckpt.get("scheduler_state"):
            scheduler.load_state_dict(ckpt["scheduler_state"])
        global_step = ckpt.get("step", 0)
        print(f"🔄 Resumed from {resume} at step {global_step}")

    model.train()
    for epoch in range(num_epochs if max_steps == 0 else 10**9):
        for batch_idx, batch in enumerate(train_loader):
            batch = {k: v.to(device) for k, v in batch.items()}
            with torch.cuda.amp.autocast(enabled=use_amp, dtype=amp_dtype):
                outputs = model(**batch)
                loss = outputs.loss / grad_accum

            if use_amp and mixed_precision == "fp16":
                scaler.scale(loss).backward()
            else:
                loss.backward()

            if (batch_idx + 1) % grad_accum == 0:
                if clip_norm:
                    torch.nn.utils.clip_grad_norm_(model.parameters(), clip_norm)
                if use_amp and mixed_precision == "fp16":
                    scaler.step(optimizer)
                    scaler.update()
                else:
                    optimizer.step()
                scheduler.step()
                optimizer.zero_grad()

                global_step += 1
                if global_step % log_every == 0:
                    print(
                        f"[step {global_step}] loss={loss.item() * grad_accum:.4f} "
                        f"lr={scheduler.get_last_lr()[0]:.2e}"
                    )

                if eval_every and global_step % eval_every == 0:
                    val_loss = evaluate(model, val_loader, device)
                    print(f"🧪 Eval step {global_step}: val_loss={val_loss:.4f}")
                    if val_loss < best_val:
                        best_val = val_loss
                        save_checkpoint(model, optimizer, scheduler, global_step, output_dir, "best")

                if save_every and global_step % save_every == 0:
                    save_checkpoint(model, optimizer, scheduler, global_step, output_dir, f"step{global_step}")

                if max_steps and global_step >= max_steps:
                    save_checkpoint(model, optimizer, scheduler, global_step, output_dir, "final")
                    print(f"✅ Reached max_steps={max_steps}. Training finished.")
                    return

        if not max_steps:
            save_checkpoint(model, optimizer, scheduler, global_step, output_dir, f"epoch{epoch + 1}")
        if max_steps and global_step >= max_steps:
            break

    save_checkpoint(model, optimizer, scheduler, global_step, output_dir, "last")
    print(f"✅ Training hoàn tất. Checkpoints lưu tại {output_dir}")


def main() -> None:
    args = parse_args()
    run_training(
        config_path=args.config,
        train_bin_override=args.train_bin,
        val_bin_override=args.val_bin,
        output_dir_override=args.output_dir,
        resume=args.resume,
        seed=args.seed,
        device_str=args.device,
    )


if __name__ == "__main__":
    main()

