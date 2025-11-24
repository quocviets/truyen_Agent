# 📊 SO SÁNH FORMAT OUTPUT - GỘP HAY TÁCH RIÊNG?

**Câu hỏi:** Có cần gộp tất cả truyện thành 1 file duy nhất không, hay giữ riêng từng truyện?

---

## 🎯 HAI LỰA CHỌN

### **Option 1: TÁCH RIÊNG (1 file/truyện) - ⭐ ĐỀ XUẤT**

```
training/dataset/preprocessed/
├── van-co-than-de_preprocessed.txt
├── van-co-than-de_metadata.json
├── than-dao-de-ton_preprocessed.txt
├── than-dao-de-ton_metadata.json
├── ...
└── preprocessing_summary.json
```

**Đặc điểm:**
- Mỗi truyện = 1 file riêng
- Dễ quản lý, debug
- Có thể xử lý song song

---

### **Option 2: GỘP TẤT CẢ (1 file cho tất cả)**

```
training/dataset/preprocessed/
├── all_novels_preprocessed.txt
├── all_novels_metadata.json
└── preprocessing_summary.json
```

**Đặc điểm:**
- Tất cả truyện = 1 file duy nhất
- Đơn giản hơn về mặt số lượng file
- File rất lớn (có thể vài GB)

---

## 📊 SO SÁNH CHI TIẾT

| Tiêu chí | Tách riêng (1 file/truyện) | Gộp tất cả (1 file) |
|----------|---------------------------|---------------------|
| **Số lượng file** | 11 files (11 truyện) | 1 file |
| **Kích thước file** | ~20-70 MB/file | ~500 MB - 2 GB |
| **Dễ quản lý** | ✅ Dễ (mỗi truyện riêng) | ⚠️ Khó (file quá lớn) |
| **Dễ debug** | ✅ Dễ (tìm lỗi theo truyện) | ❌ Khó (phải tìm trong file lớn) |
| **Xử lý song song** | ✅ Dễ (mỗi file độc lập) | ❌ Khó (phải đọc tuần tự) |
| **Memory usage** | ✅ Thấp (load từng file) | ❌ Cao (load toàn bộ) |
| **Error recovery** | ✅ Tốt (lỗi 1 file không ảnh hưởng khác) | ❌ Kém (lỗi 1 phần ảnh hưởng toàn bộ) |
| **Version control** | ✅ Dễ (track thay đổi từng truyện) | ❌ Khó (file quá lớn) |
| **Training** | ✅ Linh hoạt (có thể chọn truyện) | ⚠️ Phải dùng tất cả |
| **Độ phức tạp code** | ✅ Đơn giản | ✅ Đơn giản |

---

## 🎯 PHÂN TÍCH THEO USE CASE

### **1. PREPROCESSING**

**Tách riêng:**
- ✅ Dễ xử lý từng truyện độc lập
- ✅ Có thể resume nếu lỗi
- ✅ Dễ kiểm tra chất lượng từng truyện

**Gộp tất cả:**
- ⚠️ Phải xử lý toàn bộ một lúc
- ❌ Lỗi 1 truyện ảnh hưởng toàn bộ
- ❌ Khó kiểm tra chất lượng

**→ Khuyến nghị: TÁCH RIÊNG**

---

### **2. TOKENIZATION**

**Tách riêng:**
- ✅ Có thể tokenize từng truyện song song
- ✅ Dễ quản lý memory
- ✅ Dễ debug lỗi tokenization

**Gộp tất cả:**
- ⚠️ Phải load toàn bộ vào memory
- ❌ Khó xử lý song song
- ❌ Memory có thể không đủ

**→ Khuyến nghị: TÁCH RIÊNG**

---

### **3. TRAINING**

**Tách riêng:**
- ✅ Có thể chọn truyện để train
- ✅ Có thể balance dataset (thêm/bớt truyện)
- ✅ Dễ track performance theo truyện

**Gộp tất cả:**
- ✅ Đơn giản hơn (1 file)
- ⚠️ Phải dùng tất cả
- ❌ Khó chọn lọc

**→ Khuyến nghị: TÁCH RIÊNG (linh hoạt hơn)**

---

### **4. STORAGE & I/O**

**Tách riêng:**
- ✅ Đọc/ghi nhanh hơn (file nhỏ)
- ✅ Dễ backup từng phần
- ✅ Dễ chia sẻ (có thể share 1 truyện)

**Gộp tất cả:**
- ⚠️ Đọc/ghi chậm hơn (file lớn)
- ❌ Backup phải toàn bộ
- ❌ Khó chia sẻ (file quá lớn)

**→ Khuyến nghị: TÁCH RIÊNG**

---

## 🔄 QUY TRÌNH THỰC TẾ

### **Nếu TÁCH RIÊNG:**

```python
# Preprocessing
for novel in novels:
    preprocess_novel(novel)  # → {novel}_preprocessed.txt

# Tokenization
for novel in novels:
    tokenize_novel(novel)  # → {novel}_tokenized.pt

# Training
dataset = combine_all_novels()  # Combine khi load vào DataLoader
```

**Ưu điểm:**
- Xử lý song song dễ dàng
- Có thể chọn truyện để train
- Dễ debug và kiểm tra

---

### **Nếu GỘP TẤT CẢ:**

```python
# Preprocessing
all_text = ""
for novel in novels:
    all_text += preprocess_novel(novel)
save_all_novels(all_text)  # → all_novels_preprocessed.txt

# Tokenization
tokenize_all(all_text)  # → all_novels_tokenized.pt

# Training
dataset = load_all_novels()  # Load toàn bộ
```

**Nhược điểm:**
- Phải xử lý tuần tự
- Khó xử lý song song
- Memory có thể không đủ

---

## 🎯 KHUYẾN NGHỊ

### **⭐ ĐỀ XUẤT: TÁCH RIÊNG (1 file/truyện)**

**Lý do:**
1. **Linh hoạt:** Có thể chọn truyện để train
2. **Dễ quản lý:** Debug, kiểm tra chất lượng dễ hơn
3. **Xử lý song song:** Tokenization, preprocessing nhanh hơn
4. **Memory:** Không cần load toàn bộ vào memory
5. **Error recovery:** Lỗi 1 truyện không ảnh hưởng khác

**Khi nào cần gộp:**
- **Chỉ khi training:** Gộp khi load vào DataLoader (không cần lưu file gộp)
- **Hoặc:** Tạo script riêng để gộp khi cần (không bắt buộc)

---

## 📝 KẾT LUẬN

### **Preprocessing Output:**
- ✅ **TÁCH RIÊNG** - 1 file/truyện
- ❌ **KHÔNG CẦN** gộp thành 1 file

### **Khi nào gộp:**
- **Chỉ khi training:** Combine trong DataLoader (in-memory)
- **Hoặc:** Tạo script `combine_novels.py` để gộp khi cần (optional)

### **Cấu trúc đề xuất:**

```
training/dataset/preprocessed/
├── van-co-than-de_preprocessed.txt      ← Giữ riêng
├── van-co-than-de_metadata.json
├── than-dao-de-ton_preprocessed.txt    ← Giữ riêng
├── than-dao-de-ton_metadata.json
├── ...
└── preprocessing_summary.json           ← Tổng hợp thống kê
```

**Khi training:**
```python
# Combine khi load (không cần lưu file gộp)
novels = load_all_preprocessed_novels()
combined_text = "\n\n".join(novels)
# Hoặc load vào DataLoader trực tiếp
```

---

## ✅ QUYẾT ĐỊNH CUỐI CÙNG

**GIỮ RIÊNG TỪNG TRUYỆN - KHÔNG CẦN GỘP!**

**Lý do:**
- Linh hoạt hơn
- Dễ quản lý hơn
- Xử lý nhanh hơn
- Gộp chỉ khi cần (in-memory khi training)

