# 🧹 CHIẾN LƯỢC LÀM SẠCH TEXT - CHI TIẾT TỪNG BƯỚC

**Mục đích:** Xác định quy trình làm sạch text cho dữ liệu truyện tiếng Việt, đảm bảo chất lượng cao cho training LLM.

---

## 📋 TỔNG QUAN

### Dữ liệu hiện tại:
- **19,966 chapters** từ 11 truyện
- **246.67 MB** tổng dung lượng
- **Trung bình:** 9-18 KB/chapter
- **Encoding:** UTF-8
- **Vấn đề:** 7 file quá ngắn (< 10% trung bình)

### Mục tiêu làm sạch:
1. **Loại bỏ noise:** HTML tags, control characters, ký tự đặc biệt
2. **Chuẩn hóa format:** Whitespace, line breaks, encoding
3. **Giữ nguyên ngữ nghĩa:** Không thay đổi nội dung, chỉ format
4. **Tối ưu cho training:** Chia thành chunks hợp lý

---

## 🔹 BƯỚC 1: LÀM SẠCH CƠ BẢN (BASIC CLEANING)

### 1.1. Loại bỏ HTML/XML Tags

**Mục đích:** Xóa các tag HTML còn sót từ crawler

**Quy tắc:**
- Xóa tất cả tags: `<tag>`, `</tag>`, `<tag attr="value">`
- Giữ lại nội dung bên trong tags
- Xóa cả comments: `<!-- comment -->`

**Ví dụ:**
```
Input:  "Anh ấy <strong>rất</strong> mạnh mẽ. <!-- old text -->"
Output: "Anh ấy rất mạnh mẽ."
```

**Pattern:**
```python
# Xóa HTML tags
text = re.sub(r'<[^>]+>', '', text)
# Xóa comments
text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)
```

**Mức độ:** ⚠️ **AGGRESSIVE** - Xóa tất cả tags (có thể mất format nhưng giữ nội dung)

---

### 1.2. Loại bỏ Control Characters

**Mục đích:** Xóa các ký tự invisible, không in được

**Quy tắc:**
- **Giữ lại:** `\n` (newline), `\t` (tab), space
- **Xóa:** Tất cả control characters khác
  - `\x00-\x08` (NULL, SOH, STX, ...)
  - `\x0b-\x0c` (VT, FF)
  - `\x0e-\x1f` (SO, SI, DLE, ...)
  - `\x7f-\x9f` (DEL, padding, ...)

**Ví dụ:**
```
Input:  "Text\x00\x01\x02\x03\x04\x05"
Output: "Text"
```

**Pattern:**
```python
# Giữ \n, \t, space; xóa các control khác
text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x9f]', '', text)
```

**Mức độ:** ✅ **SAFE** - Chỉ xóa ký tự không in được

---

### 1.3. Chuẩn hóa Whitespace

**Mục đích:** Loại bỏ nhiều spaces/tabs liên tiếp

**Quy tắc:**
- Nhiều spaces liên tiếp → 1 space
- Nhiều tabs liên tiếp → 1 space
- Space + tab → 1 space
- **KHÔNG** xóa space ở đầu/cuối dòng (sẽ xử lý sau)

**Ví dụ:**
```
Input:  "Có    nhiều     space    và\t\t\ttab"
Output: "Có nhiều space và tab"
```

**Pattern:**
```python
# Nhiều whitespace → 1 space
text = re.sub(r'[ \t]+', ' ', text)
```

**Mức độ:** ✅ **SAFE** - Chỉ normalize, không mất nội dung

---

### 1.4. Chuẩn hóa Line Breaks

**Mục đích:** Normalize các loại line break khác nhau

**Quy tắc:**
- `\r\n` (Windows) → `\n`
- `\r` (Mac old) → `\n`
- Nhiều `\n` liên tiếp (3+) → 2 `\n` (giữ paragraph break)
- **KHÔNG** xóa tất cả line breaks (cần để phân đoạn)

**Ví dụ:**
```
Input:  "Đoạn 1\r\n\r\n\r\n\r\nĐoạn 2"
Output: "Đoạn 1\n\nĐoạn 2"
```

**Pattern:**
```python
# Normalize line breaks
text = text.replace('\r\n', '\n')
text = text.replace('\r', '\n')
# Nhiều newlines → tối đa 2
text = re.sub(r'\n{3,}', '\n\n', text)
```

**Mức độ:** ✅ **SAFE** - Giữ paragraph structure

---

### 1.5. Loại bỏ Ký tự Đặc biệt Không Cần thiết

**Mục đích:** Xóa emoji, symbol lạ, nhưng giữ dấu câu tiếng Việt

**Quy tắc:**

**GIỮ LẠI:**
- Chữ cái: `a-z`, `A-Z`, `à-ỹ`, `À-Ỹ` (tiếng Việt đầy đủ)
- Số: `0-9`
- Dấu câu tiếng Việt:
  - `. , ! ? ; :` (dấu câu cơ bản)
  - `( ) [ ] { }` (ngoặc)
  - `" ' - – —` (dấu ngoặc kép, gạch ngang)
  - `…` (ellipsis)
- Whitespace: ` ` (space), `\n` (newline), `\t` (tab)

**XÓA:**
- Emoji: 😊 🎉 ❤️ ...
- Symbol đặc biệt: @ # $ % ^ & * + = | \ ~ ` ...
- Unicode symbols: © ® ™ ...
- Các ký tự khác không thuộc danh sách trên

**Ví dụ:**
```
Input:  "Nham Kiều 😊 đang đứng @#$% và nói 'Xin chào!'"
Output: "Nham Kiều đang đứng và nói 'Xin chào!'"
```

**Pattern:**
```python
# Giữ lại: chữ, số, dấu câu tiếng Việt, whitespace
allowed_pattern = r'[a-zA-ZàáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐ0-9\.\,\!\?\;\:\(\)\[\]\{\}\"\'\-–—…\s]'
text = re.sub(f'[^{allowed_pattern}]', '', text)
```

**Mức độ:** ⚠️ **MODERATE** - Có thể mất một số ký tự đặc biệt nhưng giữ nội dung chính

---

### 1.6. Xóa Dòng Quá Ngắn

**Mục đích:** Loại bỏ dòng có thể là lỗi format hoặc tiêu đề không cần thiết

**Quy tắc:**
- Dòng có < 10 ký tự (sau khi strip) → Xóa
- **TRỪ:** Dòng chỉ có số (có thể là số chương) → Giữ lại
- **TRỪ:** Dòng có dấu câu quan trọng (`. ! ?`) → Giữ lại

**Ví dụ:**
```
Input:  "Đoạn văn dài\n\n\nNgắn\n\nĐoạn khác\n\n123\n\nCâu hỏi?"
Output: "Đoạn văn dài\n\nĐoạn khác\n\n123\n\nCâu hỏi?"
```

**Pattern:**
```python
lines = text.split('\n')
filtered_lines = []
for line in lines:
    stripped = line.strip()
    if len(stripped) >= 10:
        filtered_lines.append(line)
    elif stripped.isdigit() or any(c in stripped for c in '.!?'):
        filtered_lines.append(line)
    # else: bỏ qua
text = '\n'.join(filtered_lines)
```

**Mức độ:** ⚠️ **MODERATE** - Có thể mất một số dòng ngắn hợp lệ

---

### 1.7. Trim Whitespace

**Mục đích:** Xóa space ở đầu/cuối mỗi dòng và toàn bộ text

**Quy tắc:**
- Xóa space ở đầu/cuối mỗi dòng
- Xóa space ở đầu/cuối toàn bộ text
- **GIỮ** line breaks (không xóa `\n`)

**Ví dụ:**
```
Input:  "  Đoạn 1  \n  Đoạn 2  \n  "
Output: "Đoạn 1\nĐoạn 2"
```

**Pattern:**
```python
# Trim từng dòng
lines = [line.strip() for line in text.split('\n')]
text = '\n'.join(lines)
# Trim toàn bộ
text = text.strip()
```

**Mức độ:** ✅ **SAFE** - Chỉ xóa whitespace thừa

---

## 🔹 BƯỚC 2: CHIA THÀNH ĐOẠN VĂN (PARAGRAPH SEGMENTATION)

### 2.1. Chia theo Paragraph Break

**Mục đích:** Tách text thành các đoạn văn hợp lệ

**Quy tắc:**
- Tách theo pattern: `\n\s*\n` (2 newlines liên tiếp)
- Mỗi đoạn là một paragraph độc lập

**Ví dụ:**
```
Input:  "Đoạn 1\n\nĐoạn 2\n\nĐoạn 3"
Output: ["Đoạn 1", "Đoạn 2", "Đoạn 3"]
```

**Pattern:**
```python
paragraphs = re.split(r'\n\s*\n', text)
paragraphs = [p.strip() for p in paragraphs if p.strip()]
```

**Mức độ:** ✅ **SAFE** - Giữ nguyên cấu trúc

---

### 2.2. Lọc Đoạn Hợp lệ

**Mục đích:** Chỉ giữ lại các đoạn có độ dài hợp lý

**Quy tắc:**
- **Quá ngắn (< 50 ký tự):** Bỏ qua (có thể là tiêu đề, lỗi format)
- **Hợp lệ (50-2000 ký tự):** Giữ lại
- **Quá dài (> 2000 ký tự):** Chia nhỏ (xem 2.3)

**Ví dụ:**
```python
paragraphs = [
    "Đoạn ngắn",                    # < 50 → BỎ
    "Đoạn văn dài hợp lệ...",       # 50-2000 → GIỮ
    "Đoạn rất dài..." * 1000        # > 2000 → CHIA NHỎ
]
```

**Pattern:**
```python
valid_paragraphs = []
for para in paragraphs:
    length = len(para)
    if length < 50:
        continue  # Bỏ qua
    elif length <= 2000:
        valid_paragraphs.append(para)
    else:
        # Chia nhỏ (xem 2.3)
        chunks = split_long_paragraph(para)
        valid_paragraphs.extend(chunks)
```

**Mức độ:** ✅ **SAFE** - Chỉ filter đoạn quá ngắn/dài

---

### 2.3. Chia Đoạn Dài thành Chunks

**Mục đích:** Chia đoạn > 2000 ký tự thành nhiều chunks nhỏ hơn

**Quy tắc:**
- Chia theo câu (dấu chấm `.`, chấm hỏi `?`, chấm than `!`)
- Mỗi chunk tối đa ~2000 ký tự
- **Ưu tiên:** Chia ở vị trí câu hoàn chỉnh
- **Fallback:** Nếu không có câu, chia ở space

**Ví dụ:**
```
Input:  Đoạn 3000 ký tự (nhiều câu)
Output: 
  - Chunk 1: "Câu 1. Câu 2. ..." (2000 ký tự)
  - Chunk 2: "Câu tiếp. ..." (1000 ký tự)
```

**Pattern:**
```python
def split_long_paragraph(text, max_length=2000):
    if len(text) <= max_length:
        return [text]
    
    chunks = []
    current_chunk = ""
    
    # Chia theo câu
    sentences = re.split(r'([.!?]+)', text)
    
    for i in range(0, len(sentences), 2):
        sentence = sentences[i] + (sentences[i+1] if i+1 < len(sentences) else '')
        
        if len(current_chunk) + len(sentence) <= max_length:
            current_chunk += sentence
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = sentence
    
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks
```

**Mức độ:** ✅ **SAFE** - Chia nhỏ nhưng giữ nguyên nội dung

---

## 🔹 BƯỚC 3: FILTER CHAPTER (CHAPTER FILTERING)

### 3.1. Filter theo Độ dài Tuyệt đối

**Mục đích:** Loại bỏ chapter quá ngắn (có thể là lỗi)

**Quy tắc:**
- Chapter < 500 bytes → Bỏ qua
- **Lý do:** Chapter quá ngắn thường là lỗi crawler hoặc nội dung không hợp lệ

**Ví dụ:**
```python
if len(content.encode('utf-8')) < 500:
    continue  # Bỏ qua chapter này
```

**Mức độ:** ✅ **SAFE** - Chỉ filter chapter rõ ràng là lỗi

---

### 3.2. Filter theo Tỷ lệ Trung bình

**Mục đích:** Loại bỏ chapter bất thường so với trung bình

**Quy tắc:**
- Tính độ dài trung bình của tất cả chapters trong truyện
- Chapter < 10% trung bình → Bỏ qua
- **Lý do:** Chapter quá ngắn so với trung bình có thể là lỗi

**Ví dụ:**
```python
avg_size = sum(all_chapter_sizes) / len(all_chapter_sizes)
min_size = avg_size * 0.1  # 10% trung bình

if chapter_size < min_size:
    continue  # Bỏ qua
```

**Mức độ:** ⚠️ **MODERATE** - Có thể mất một số chapter ngắn hợp lệ

---

## 📊 MỨC ĐỘ LÀM SẠCH - TỔNG KẾT

### ✅ SAFE (An toàn - Không mất nội dung)
1. Loại bỏ Control Characters
2. Chuẩn hóa Whitespace
3. Chuẩn hóa Line Breaks
4. Trim Whitespace
5. Chia theo Paragraph Break
6. Filter theo Độ dài Tuyệt đối (< 500 bytes)

### ⚠️ MODERATE (Vừa phải - Có thể mất một số nội dung)
1. Loại bỏ Ký tự Đặc biệt (emoji, symbol)
2. Xóa Dòng Quá Ngắn (< 10 ký tự)
3. Filter theo Tỷ lệ Trung bình (< 10%)

### ⚠️ AGGRESSIVE (Mạnh - Có thể mất format)
1. Loại bỏ HTML/XML Tags

---

## 🎯 CHIẾN LƯỢC ĐỀ XUẤT

### **Option 1: CONSERVATIVE (Bảo thủ)**
- Áp dụng: Tất cả bước SAFE + MODERATE (trừ xóa emoji)
- **Ưu điểm:** Giữ tối đa nội dung
- **Nhược điểm:** Có thể còn một số noise
- **Phù hợp:** Khi muốn giữ nguyên tối đa

### **Option 2: BALANCED (Cân bằng) - ⭐ ĐỀ XUẤT**
- Áp dụng: Tất cả bước SAFE + MODERATE
- **Ưu điểm:** Cân bằng giữa chất lượng và giữ nội dung
- **Nhược điểm:** Có thể mất một số ký tự đặc biệt
- **Phù hợp:** Training LLM tiếng Việt (khuyến nghị)

### **Option 3: AGGRESSIVE (Mạnh)**
- Áp dụng: Tất cả bước (bao gồm AGGRESSIVE)
- **Ưu điểm:** Text rất sạch, không có noise
- **Nhược điểm:** Có thể mất format và một số nội dung
- **Phù hợp:** Khi muốn text cực kỳ sạch

---

## 📝 LƯU Ý QUAN TRỌNG

1. **Giữ nguyên ngữ nghĩa:** Không thay đổi nội dung, chỉ format
2. **Không normalize dấu:** Giữ nguyên dấu tiếng Việt (à, á, ả, ...)
3. **Giữ paragraph structure:** Không xóa tất cả line breaks
4. **Filter có chọn lọc:** Chỉ filter chapter rõ ràng là lỗi
5. **Logging:** Ghi log tất cả chapter bị filter để review sau

---

## 🔄 QUY TRÌNH THỰC HIỆN

1. **Bước 1:** Làm sạch cơ bản (1.1 → 1.7)
2. **Bước 2:** Chia thành đoạn văn (2.1 → 2.3)
3. **Bước 3:** Filter chapter (3.1 → 3.2)
4. **Bước 4:** Lưu kết quả

---

## 📈 KẾT QUẢ DỰ KIẾN

Sau khi làm sạch:
- **Số chapters:** ~19,959 (filter 7 chapter quá ngắn)
- **Chất lượng:** Text sạch, không có HTML, control characters
- **Cấu trúc:** Chia thành paragraphs hợp lệ
- **Sẵn sàng:** Cho tokenization và training


