# Ghi chú bổ sung requirements

- **Ngày tạo:** 2025-01-21  
- **Thay đổi:** Thêm file `requirements.txt` ở root dự án.

## Lý do

1. Khi chạy các script trong `training/trainer/` cần hai thư viện ngoài chuẩn:
   - `tqdm`: hiển thị progress bar khi đọc JSONL lớn trong preprocessing/tokenization.
   - `sentencepiece`: sử dụng chung cho tokenizer builder và script tokenization.
2. Trước đây chỉ có `training/trainer/requirements_preprocessing.txt`, dễ bỏ sót khi setup venv cho toàn dự án.

## Nội dung file `requirements.txt`

```
tqdm>=4.65.0
sentencepiece>=0.2.1
```

Phiên bản chọn theo thực tế đã cài đặt (`sentencepiece 0.2.1`, `tqdm ≥ 4.65`), có thể mở rộng sau nếu thêm module mới (Agent, Distillation, v.v.).

## Hướng dẫn sử dụng

```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Sau khi cài xong có thể chạy toàn bộ pipeline data (preprocess, QA, split, tokenizer, tokenize). Nếu thêm dependency mới, cập nhật file này và ghi chú vào tài liệu tương ứng.

