# 🔄 CHIẾN LƯỢC DATA AUGMENTATION

**Mục đích:** Tăng cường dữ liệu training bằng cách tạo sinh thêm samples từ dữ liệu gốc.

---

## 📋 TỔNG QUAN

### Dữ liệu hiện tại:
- **19,966 chapters** (sau filter: ~19,959)
- **246.67 MB** tổng dung lượng
- **Trung bình:** 9-18 KB/chapter

### Mục tiêu augmentation:
1. **Tăng số lượng samples** cho training
2. **Tăng tính đa dạng** của dữ liệu
3. **Cải thiện generalization** của model
4. **Không làm mất ngữ nghĩa** gốc

---

## 🎯 CÁC PHƯƠNG PHÁP AUGMENTATION

### 1. **PARAPHRASING (Diễn đạt lại)**

**Mô tả:** Viết lại câu/đoạn với từ ngữ khác nhưng giữ nguyên nghĩa

**Ví dụ:**
```
Original: "Anh ấy rất mạnh mẽ và dũng cảm."
Paraphrased: "Người đó có sức mạnh và lòng dũng cảm phi thường."
```

**Cách thực hiện:**
- **Manual:** Không khả thi (quá nhiều dữ liệu)
- **LLM-based:** Dùng LLM (GPT, Claude) để paraphrase
  - **Ưu điểm:** Chất lượng cao, tự động
  - **Nhược điểm:** Tốn chi phí API, thời gian
- **Rule-based:** Thay thế từ đồng nghĩa
  - **Ưu điểm:** Nhanh, miễn phí
  - **Nhược điểm:** Chất lượng thấp hơn

**Khuyến nghị:** ⚠️ **KHÔNG NÊN** - Tốn chi phí, có thể làm mất ngữ nghĩa

---

### 2. **BACK-TRANSLATION (Dịch ngược)**

**Mô tả:** Dịch sang ngôn ngữ khác rồi dịch lại về tiếng Việt

**Ví dụ:**
```
Original (VI): "Anh ấy rất mạnh mẽ."
→ English: "He is very strong."
→ Vietnamese: "Anh ta có sức mạnh rất lớn."
```

**Cách thực hiện:**
- Dùng Google Translate API hoặc mô hình dịch
- Dịch: VI → EN → VI (hoặc VI → ZH → VI)

**Ưu điểm:**
- Tự động, nhanh
- Tạo ra cách diễn đạt khác
- Giữ nguyên ngữ nghĩa cơ bản

**Nhược điểm:**
- Có thể mất một số nuance
- Tốn chi phí API (nếu dùng dịch vụ)
- Cần mô hình dịch tốt

**Khuyến nghị:** ⚠️ **CÓ THỂ THỬ** - Nhưng cần test chất lượng trước

---

### 3. **SENTENCE SHUFFLING (Xáo trộn câu)**

**Mô tả:** Xáo trộn thứ tự các câu trong đoạn (chỉ áp dụng cho một số đoạn)

**Ví dụ:**
```
Original: 
  "Anh ấy thức dậy. Anh ấy ăn sáng. Anh ấy đi làm."

Shuffled:
  "Anh ấy ăn sáng. Anh ấy thức dậy. Anh ấy đi làm."
```

**Lưu ý:**
- **KHÔNG** áp dụng cho đoạn có thứ tự logic (mô tả hành động tuần tự)
- **CHỈ** áp dụng cho đoạn mô tả độc lập (ví dụ: mô tả nhân vật)

**Khuyến nghị:** ❌ **KHÔNG NÊN** - Dễ làm mất logic của truyện

---

### 4. **NOISE INJECTION (Thêm noise)**

**Mô tả:** Thêm một số lỗi nhỏ (typo, thêm/xóa space) để model học cách xử lý

**Ví dụ:**
```
Original: "Anh ấy rất mạnh mẽ."
Noisy:    "Anh ấy rất mạnh mẽ ."  (thêm space trước dấu chấm)
```

**Cách thực hiện:**
- Thêm/xóa space ngẫu nhiên (tỷ lệ thấp: 1-2%)
- Thêm typo nhỏ (thay đổi 1-2 ký tự)
- **KHÔNG** thêm quá nhiều (sẽ làm hỏng dữ liệu)

**Ưu điểm:**
- Giúp model robust với lỗi nhỏ
- Dễ thực hiện

**Nhược điểm:**
- Có thể làm hỏng dữ liệu nếu quá nhiều
- Cần kiểm soát chặt chẽ

**Khuyến nghị:** ⚠️ **CẨN THẬN** - Chỉ áp dụng với tỷ lệ rất thấp (0.5-1%)

---

### 5. **CONTEXT WINDOW SLIDING (Trượt cửa sổ ngữ cảnh)**

**Mô tả:** Tạo nhiều samples từ cùng một đoạn bằng cách trượt cửa sổ

**Ví dụ:**
```
Original paragraph (1000 ký tự):
  "Đoạn văn dài..."

Samples tạo ra (mỗi sample 512 tokens, overlap 256 tokens):
  - Sample 1: Ký tự 0-512
  - Sample 2: Ký tự 256-768
  - Sample 3: Ký tự 512-1024
```

**Cách thực hiện:**
- Chia đoạn dài thành nhiều chunks với overlap
- Mỗi chunk là một sample mới
- **Overlap:** 50% (khuyến nghị)

**Ưu điểm:**
- Tăng số lượng samples đáng kể
- Giữ nguyên ngữ nghĩa
- Dễ thực hiện

**Nhược điểm:**
- Tăng kích thước dataset (có thể gấp 2-3 lần)
- Cần nhiều storage và memory

**Khuyến nghị:** ✅ **NÊN DÙNG** - Hiệu quả, an toàn

---

### 6. **DIFFERENT CHUNK SIZES (Nhiều kích thước chunk)**

**Mô tả:** Tạo samples với nhiều kích thước khác nhau từ cùng dữ liệu

**Ví dụ:**
```
Original paragraph (2000 ký tự):
  "Đoạn văn dài..."

Samples:
  - Chunk 256 tokens: "Phần đầu..."
  - Chunk 512 tokens: "Phần giữa..."
  - Chunk 1024 tokens: "Toàn bộ..."
```

**Cách thực hiện:**
- Chia đoạn thành chunks với nhiều kích thước
- Mỗi kích thước phục vụ mục đích khác nhau:
  - 256 tokens: Training nhanh, test
  - 512 tokens: Training chuẩn
  - 1024 tokens: Training với context dài

**Ưu điểm:**
- Linh hoạt, có thể train với nhiều context lengths
- Tăng số lượng samples

**Nhược điểm:**
- Tăng kích thước dataset
- Cần quản lý nhiều kích thước

**Khuyến nghị:** ✅ **NÊN DÙNG** - Nếu muốn train với nhiều context lengths

---

### 7. **CROSS-NOVEL MIXING (Trộn giữa các truyện)**

**Mô tắc:** Tạo samples bằng cách kết hợp đoạn từ nhiều truyện khác nhau

**Ví dụ:**
```
Novel 1: "Anh ấy rất mạnh mẽ."
Novel 2: "Cô ấy rất xinh đẹp."

Mixed: "Anh ấy rất mạnh mẽ. Cô ấy rất xinh đẹp."
```

**Lưu ý:**
- **KHÔNG** áp dụng cho truyện có cốt truyện liên tục
- **CHỈ** áp dụng cho training language model (không cần logic)

**Khuyến nghị:** ✅ **CÓ THỂ** - Nếu training language model thuần túy

---

## 🎯 CHIẾN LƯỢC ĐỀ XUẤT

### **Option 1: MINIMAL (Tối thiểu) - ⭐ ĐỀ XUẤT CHO BẮT ĐẦU**

**Áp dụng:**
- ✅ Context Window Sliding (overlap 50%)
- ❌ Các phương pháp khác

**Lý do:**
- An toàn, không làm mất ngữ nghĩa
- Tăng số lượng samples đáng kể
- Dễ thực hiện

**Kết quả dự kiến:**
- Tăng dataset lên ~2-3 lần
- Giữ nguyên chất lượng

---

### **Option 2: MODERATE (Vừa phải)**

**Áp dụng:**
- ✅ Context Window Sliding
- ✅ Different Chunk Sizes (256, 512, 1024)
- ⚠️ Noise Injection (tỷ lệ thấp: 0.5%)

**Lý do:**
- Tăng tính đa dạng
- Giúp model robust hơn

**Kết quả dự kiến:**
- Tăng dataset lên ~3-4 lần
- Chất lượng vẫn tốt

---

### **Option 3: AGGRESSIVE (Mạnh)**

**Áp dụng:**
- ✅ Context Window Sliding
- ✅ Different Chunk Sizes
- ✅ Back-Translation (một phần)
- ⚠️ Noise Injection

**Lý do:**
- Tăng tối đa số lượng samples
- Tăng tính đa dạng

**Nhược điểm:**
- Tốn chi phí (nếu dùng dịch vụ)
- Cần test chất lượng kỹ

**Kết quả dự kiến:**
- Tăng dataset lên ~4-5 lần
- Cần validate chất lượng

---

## 📊 SO SÁNH CÁC PHƯƠNG PHÁP

| Phương pháp | Tăng số lượng | Chất lượng | Chi phí | Độ khó | Khuyến nghị |
|-------------|---------------|------------|---------|--------|-------------|
| Paraphrasing | ⭐⭐⭐ | ⭐⭐⭐ | 💰💰💰 | 🔴🔴🔴 | ❌ |
| Back-Translation | ⭐⭐ | ⭐⭐ | 💰💰 | 🟡🟡 | ⚠️ |
| Sentence Shuffling | ⭐ | ⭐ | 💰 | 🟢 | ❌ |
| Noise Injection | ⭐ | ⭐⭐ | 💰 | 🟢 | ⚠️ |
| Context Sliding | ⭐⭐⭐ | ⭐⭐⭐ | 💰 | 🟢 | ✅ |
| Different Chunk Sizes | ⭐⭐ | ⭐⭐⭐ | 💰 | 🟢 | ✅ |
| Cross-Novel Mixing | ⭐⭐ | ⭐⭐ | 💰 | 🟢 | ✅ |

---

## 🔄 QUY TRÌNH THỰC HIỆN

### **Bước 1: Preprocessing**
- Làm sạch text (theo `CHIEN_LUOC_LAM_SACH_TEXT.md`)
- Chia thành paragraphs

### **Bước 2: Augmentation**
- Áp dụng các phương pháp đã chọn
- Lưu metadata (đánh dấu sample nào là augmented)

### **Bước 3: Validation**
- Kiểm tra chất lượng samples
- So sánh với dữ liệu gốc

### **Bước 4: Lưu kết quả**
- Lưu vào `training/dataset/augmented/`
- Ghi log augmentation statistics

---

## 📝 LƯU Ý QUAN TRỌNG

1. **Giữ nguyên ngữ nghĩa:** Không làm mất nghĩa gốc
2. **Validate chất lượng:** Kiểm tra samples sau augmentation
3. **Logging:** Ghi log tất cả samples được tạo
4. **Metadata:** Đánh dấu sample nào là augmented
5. **Không quá nhiều:** Tránh làm hỏng dữ liệu

---

## 🎯 KẾT LUẬN

**Khuyến nghị cho dự án này:**
- **Bắt đầu:** Option 1 (MINIMAL) - Context Window Sliding
- **Sau đó:** Có thể thêm Different Chunk Sizes nếu cần
- **Tránh:** Paraphrasing, Back-Translation (tốn chi phí, không cần thiết)

**Lý do:**
- Dữ liệu đã đủ lớn (19,966 chapters)
- Context Sliding đã tăng đáng kể số lượng
- Không cần augmentation phức tạp


