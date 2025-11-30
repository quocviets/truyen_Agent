# Khắc phục lỗi đầy đĩa khi training Kaggle

## Nguyên nhân

- `save_checkpoint` trước đây gọi `model.save_pretrained(...)` *mỗi lần* lưu.
- Mỗi checkpoint tạo thêm thư mục `hf_*` vài trăm MB → nhanh chóng đầy `/kaggle/working`.
- Log lỗi: `No space left on device` (safetensors, OSError 28).

## Thay đổi chính

1. `save_checkpoint` giờ chỉ lưu payload `.pt` (model/optimizer/scheduler/state).
2. Luôn cập nhật `checkpoint_latest.pt` để resume nhanh.
3. Chỉ khi val_loss tốt hơn mới gọi `model.save_pretrained("hf_best")`.

Code mới:

```
save_checkpoint(..., save_hf=True)  # chỉ cho checkpoint best
save_checkpoint(..., save_hf=False) # các checkpoint còn lại
```

## Hướng dẫn sử dụng

- Nếu muốn tải mô hình HF: dùng thư mục `hf_best` (chỉ có 1 bản nhẹ hơn).
- Nếu cần thêm bản HF cuối cùng, có thể gọi `save_checkpoint(..., save_hf=True)` ở đoạn cuối.
- Trước khi rerun Kaggle: `rm -rf /kaggle/working/model_output` để dọn cũ.

## Lợi ích

- Giảm số file lớn trong `/kaggle/working`, tránh bị kill giữa chừng.
- Vẫn đảm bảo resume được (`checkpoint_latest.pt`).
- Vẫn có checkpoint tốt nhất để down và convert HF.


