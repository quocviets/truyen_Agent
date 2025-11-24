# 📝 HƯỚNG DẪN PREPROCESSING

## 🎯 Mục đích

Script `preprocessing.py` xử lý dữ liệu raw từ crawler, làm sạch và chuẩn hóa text để sẵn sàng cho tokenization và training.

## 📋 Chức năng

1. **Đọc dữ liệu raw** từ `training/dataset/raw/truyenmoiii_output/`
2. **Làm sạch text:**
   - Loại bỏ HTML tags (nếu còn)
   - Chuẩn hóa whitespace
   - Loại bỏ ký tự control
   - Normalize line breaks
3. **Filter chapters:**
   - Loại bỏ chapter quá ngắn (< 500 bytes)
   - Loại bỏ chapter < 10% trung bình
4. **Lưu output** vào `training/dataset/preprocessed/`

## 🚀 Cách sử dụng

### Cách 1: Chạy với default settings

```bash
python training/trainer/preprocessing.py
```

### Cách 2: Chỉ định thư mục

```bash
python training/trainer/preprocessing.py \
    --raw-dir training/dataset/raw/truyenmoiii_output \
    --output-dir training/dataset/preprocessed
```

### Cách 3: Tùy chỉnh filter

```bash
python training/trainer/preprocessing.py \
    --min-length 500 \
    --min-ratio 0.1
```

### Cách 4: Chọn format output

```bash
# Combined: 1 file lớn cho mỗi truyện
python training/trainer/preprocessing.py --format combined

# Separate: Nhiều file riêng cho mỗi chapter
python training/trainer/preprocessing.py --format separate
```

## 📊 Output

### Format: Combined (mặc định)

```
training/dataset/preprocessed/
├── van-co-than-de_preprocessed.txt
├── van-co-than-de_metadata.json
├── than-dao-de-ton_preprocessed.txt
├── than-dao-de-ton_metadata.json
├── ...
└── preprocessing_summary.json
```

### Format: Separate

```
training/dataset/preprocessed/
├── van-co-than-de/
│   ├── chapter_00001.txt
│   ├── chapter_00002.txt
│   └── ...
├── van-co-than-de_metadata.json
├── than-dao-de-ton/
│   ├── chapter_00001.txt
│   └── ...
└── preprocessing_summary.json
```

## 📈 Metadata

Mỗi truyện có file `{novel_name}_metadata.json` chứa:
- Tổng số chapters
- Số chapters đã xử lý
- Số chapters đã filter
- Tổng ký tự
- Tổng bytes
- Trung bình ký tự/chapter

## ⚙️ Tham số

| Tham số | Mặc định | Mô tả |
|---------|----------|-------|
| `--raw-dir` | `training/dataset/raw/truyenmoiii_output` | Thư mục input |
| `--output-dir` | `training/dataset/preprocessed` | Thư mục output |
| `--format` | `combined` | Format: `combined` hoặc `separate` |
| `--min-length` | `500` | Độ dài tối thiểu (bytes) |
| `--min-ratio` | `0.1` | Tỷ lệ tối thiểu so với trung bình (10%) |

## 🔍 Filter Logic

Chapter sẽ bị filter nếu:
1. Độ dài < `min-length` (mặc định 500 bytes), HOẶC
2. Độ dài < `min-ratio` * trung bình (mặc định 10% trung bình)

**Ví dụ:**
- Truyện có trung bình 10 KB/chapter
- Chapter 1: 8 KB → ✅ Giữ (80% trung bình)
- Chapter 2: 0.5 KB → ❌ Filter (< 500 bytes)
- Chapter 3: 0.8 KB → ❌ Filter (< 10% trung bình = 1 KB)

## 📝 Lưu ý

1. **Encoding:** Tất cả file đều dùng UTF-8
2. **Whitespace:** Đã được chuẩn hóa (loại bỏ nhiều spaces, line breaks)
3. **HTML:** Nếu còn HTML tags sẽ bị loại bỏ
4. **Filter:** 7 file bất thường sẽ bị filter (theo DANH_GIA_DU_LIEU_FINAL.md)

## ✅ Checklist trước khi chạy

- [ ] Dữ liệu raw đã có trong `training/dataset/raw/truyenmoiii_output/`
- [ ] Đã cài đặt dependencies: `tqdm`
- [ ] Đã kiểm tra dữ liệu (xem `training/configs/DANH_GIA_DU_LIEU_FINAL.md`)

## 🐛 Troubleshooting

### Lỗi: Không tìm thấy thư mục
```
❌ Không tìm thấy folder truyện nào trong ...
```
**Giải pháp:** Kiểm tra đường dẫn `--raw-dir` có đúng không

### Lỗi: Permission denied
**Giải pháp:** Kiểm tra quyền ghi vào `--output-dir`

### Lỗi: Encoding error
**Giải pháp:** Đảm bảo file input là UTF-8

## 📚 Xem thêm

- `training/configs/QUY_TRINH_CHI_TIET.md` - Quy trình chi tiết
- `training/configs/DANH_GIA_DU_LIEU_FINAL.md` - Đánh giá dữ liệu



