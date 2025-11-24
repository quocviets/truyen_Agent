# 📋 QUY TRÌNH PIPELINE CHI TIẾT - TỪNG BƯỚC CỤ THỂ

## 🎯 MỤC TIÊU TỔNG QUAN

Xây dựng Language Model để generate text tiếp theo từ prompt, train trên dữ liệu truyện tiếng Việt.

---

# 🔹 BƯỚC 1: TIỀN XỬ LÝ (PREPROCESSING)

## 📥 INPUT
```
truyenmoiii_output/
├── chapter_1.txt          (Ví dụ: "Đọc Từ Đầu\n\nNắng ấm xuyên qua...")
├── chapter_2.txt
├── chapter_3.txt
├── ...
├── chapter_580.txt
└── novel_summary.json    (Metadata: danh sách chương, URL, ...)
```

## 🔄 QUY TRÌNH CHI TIẾT

### Bước 1.1: Đọc dữ liệu
**Mục đích:** Load tất cả file chapter vào memory

**Công việc:**
1. Quét thư mục `truyenmoiii_output/`
2. Tìm tất cả file có pattern `chapter_*.txt`
3. Sắp xếp theo số thứ tự (chapter_1, chapter_2, ...)
4. Đọc từng file với encoding UTF-8
5. Lưu nội dung vào list: `raw_texts = [text1, text2, ...]`

**Ví dụ:**
```python
# Tìm files
files = ["chapter_1.txt", "chapter_2.txt", ..., "chapter_580.txt"]

# Đọc nội dung
raw_texts = []
for file in files:
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()
        raw_texts.append(content)
```

**Output:** List các string chứa nội dung raw text

---

### Bước 1.2: Làm sạch text cơ bản
**Mục đích:** Xóa các ký tự không cần thiết, chuẩn hóa format

**Công việc:**

**1.2.1. Xóa Control Characters**
- Tìm và xóa các ký tự invisible: `\x00-\x08`, `\x0b-\x0c`, `\x0e-\x1f`, `\x7f-\x9f`
- **Ví dụ:**
  - Input: `"Text\x00\x01\x02"`
  - Output: `"Text"`

**1.2.2. Chuẩn hóa khoảng trắng**
- Nhiều space liên tiếp → 1 space
- Nhiều tab → 1 space
- **Ví dụ:**
  - Input: `"Có    nhiều     space"`
  - Output: `"Có nhiều space"`

**1.2.3. Chuẩn hóa xuống dòng**
- Nhiều newline liên tiếp (3+) → 2 newlines (giữ paragraph break)
- **Ví dụ:**
  - Input: `"Đoạn 1\n\n\n\n\nĐoạn 2"`
  - Output: `"Đoạn 1\n\nĐoạn 2"`

**1.2.4. Xóa dòng quá ngắn**
- Các dòng có < 10 ký tự (có thể là lỗi format) → xóa
- **Ví dụ:**
  - Input: `"Đoạn văn dài\n\n\nNgắn\n\nĐoạn khác"`
  - Output: `"Đoạn văn dài\n\nĐoạn khác"`

**1.2.5. Xóa ký tự đặc biệt không cần thiết**
- Giữ lại:
  - Chữ cái tiếng Việt (a-z, A-Z, à-ỹ, À-Ỹ)
  - Số (0-9)
  - Dấu câu tiếng Việt: `. , ! ? ; : ( ) [ ] { } " ' - – — …`
  - Khoảng trắng, xuống dòng
- Xóa: Các ký tự khác (emoji, symbol đặc biệt, ...)
- **Ví dụ:**
  - Input: `"Nham Kiều 😊 đang đứng @#$%"`
  - Output: `"Nham Kiều đang đứng"`

**Output:** Text đã được làm sạch cơ bản

---

### Bước 1.3: Chia thành đoạn văn
**Mục đích:** Chia text thành các đoạn văn hợp lệ để training

**Công việc:**

**1.3.1. Chia theo paragraph break**
- Tách text theo pattern: `\n\s*\n` (2 newlines liên tiếp)
- **Ví dụ:**
  - Input: `"Đoạn 1\n\nĐoạn 2\n\nĐoạn 3"`
  - Output: `["Đoạn 1", "Đoạn 2", "Đoạn 3"]`

**1.3.2. Lọc đoạn hợp lệ**
- Kiểm tra độ dài mỗi đoạn:
  - **Quá ngắn (< 50 ký tự):** Bỏ qua (có thể là tiêu đề, lỗi format)
  - **Hợp lệ (50-2000 ký tự):** Giữ lại
  - **Quá dài (> 2000 ký tự):** Chia nhỏ (xem Bước 1.3.3)

**Ví dụ:**
```python
paragraphs = [
    "Đoạn ngắn",                    # < 50 → BỎ
    "Đoạn văn dài hợp lệ...",       # 50-2000 → GIỮ
    "Đoạn rất dài..." * 1000        # > 2000 → CHIA NHỎ
]
```

**1.3.3. Chia đoạn dài thành chunks**
- Nếu đoạn > 2000 ký tự → chia thành nhiều chunks
- Chia theo câu (dấu chấm, chấm hỏi, chấm than)
- Mỗi chunk tối đa ~512 tokens (ước tính: 1 token ≈ 4 ký tự tiếng Việt)
- **Ví dụ:**
  - Input: Đoạn 3000 ký tự
  - Output: Chunk 1 (2000 ký tự), Chunk 2 (1000 ký tự)

**Output:** List các đoạn văn hợp lệ: `valid_paragraphs = [para1, para2, ...]`

---

### Bước 1.4: Lưu kết quả
**Mục đích:** Lưu dữ liệu đã xử lý để sử dụng ở bước sau

**Công việc:**

**1.4.1. Tạo thư mục output**
- Tạo `data/preprocessed/` nếu chưa có

**1.4.2. Lưu dữ liệu**
- File: `all_novels_preprocessed.json`
- Format:
```json
{
  "novel_name": "all_novels",
  "num_paragraphs": 15000,
  "paragraphs": [
    "Đoạn văn 1...",
    "Đoạn văn 2...",
    ...
  ]
}
```

**1.4.3. Lưu thống kê**
- File: `preprocessing_summary.json`
- Format:
```json
{
  "total_novels": 1,
  "total_paragraphs": 15000,
  "total_characters": 5000000,
  "avg_paragraph_length": 333
}
```

## 📤 OUTPUT
```
data/preprocessed/
├── all_novels_preprocessed.json    (Dữ liệu đã xử lý)
└── preprocessing_summary.json      (Thống kê)
```

---

# 🔹 BƯỚC 2: CHUẨN BỊ DATASET (DATA PREPARATION)

## 📥 INPUT
```
data/preprocessed/
└── all_novels_preprocessed.json
```

## 🔄 QUY TRÌNH CHI TIẾT

### Bước 2.1: Load dữ liệu đã preprocess
**Mục đích:** Đọc dữ liệu từ Bước 1

**Công việc:**
1. Đọc file `all_novels_preprocessed.json`
2. Extract list paragraphs: `paragraphs = data['paragraphs']`
3. **Ví dụ:**
   - Input: File JSON với 15,000 paragraphs
   - Output: `paragraphs = ["para1", "para2", ..., "para15000"]`

**Output:** List các paragraphs (strings)

---

### Bước 2.2: Xây dựng Vocabulary
**Mục đích:** Tạo từ điển mapping từ → token ID

**Công việc:**

**2.2.1. Đếm tần suất từ**
- Chia mỗi paragraph thành từ (split theo space)
- Đếm số lần xuất hiện của mỗi từ trong toàn bộ dataset
- **Ví dụ:**
  ```python
  word_counts = {
    "Nham": 500,
    "Kiều": 450,
    "đang": 300,
    "đứng": 200,
    ...
  }
  ```

**2.2.2. Lấy top N từ phổ biến**
- Sắp xếp theo tần suất giảm dần
- Lấy top 50,000 từ (trừ special tokens)
- **Ví dụ:**
  ```python
  top_words = [
    ("Nham", 500),
    ("Kiều", 450),
    ("đang", 300),
    ...
  ]  # Top 50,000 từ
  ```

**2.2.3. Tạo Special Tokens**
- `<UNK>` (ID: 0): Từ không có trong vocabulary
- `<PAD>` (ID: 1): Padding token
- `<BOS>` (ID: 2): Beginning of sequence
- `<EOS>` (ID: 3): End of sequence

**2.2.4. Tạo Mapping**
- `word_to_id`: Từ → Token ID
- `id_to_word`: Token ID → Từ
- **Ví dụ:**
  ```python
  word_to_id = {
    "<UNK>": 0,
    "<PAD>": 1,
    "<BOS>": 2,
    "<EOS>": 3,
    "Nham": 4,
    "Kiều": 5,
    ...
  }
  
  id_to_word = {
    0: "<UNK>",
    1: "<PAD>",
    2: "<BOS>",
    3: "<EOS>",
    4: "Nham",
    5: "Kiều",
    ...
  }
  ```

**Output:** Vocabulary với 50,000+ tokens

---

### Bước 2.3: Tạo Tokenizer
**Mục đích:** Công cụ encode/decode text ↔ tokens

**Công việc:**

**2.3.1. Implement encode()**
- Input: Text string
- Output: List of token IDs
- **Ví dụ:**
  ```python
  text = "Nham Kiều đang đứng"
  token_ids = [4, 5, 300, 200]  # [Nham, Kiều, đang, đứng]
  ```

**2.3.2. Implement decode()**
- Input: List of token IDs
- Output: Text string
- **Ví dụ:**
  ```python
  token_ids = [4, 5, 300, 200]
  text = "Nham Kiều đang đứng"
  ```

**2.3.3. Hỗ trợ padding/truncation**
- Nếu text quá dài → truncate đến max_length
- Nếu text quá ngắn → pad với `<PAD>` token
- **Ví dụ:**
  ```python
  # Truncate
  text = "Rất dài..." * 100
  tokens = encode(text, max_length=512)  # Chỉ lấy 512 tokens đầu
  
  # Padding
  text = "Ngắn"
  tokens = encode(text, max_length=512)  # [tokens..., 1, 1, 1, ...] (pad đến 512)
  ```

**Output:** Tokenizer object có thể encode/decode

---

### Bước 2.4: Tạo Samples
**Mục đích:** Chuyển paragraphs thành samples có độ dài cố định

**Công việc:**

**2.4.1. Xử lý từng paragraph**
- Với mỗi paragraph:
  - Ước tính số tokens (1 token ≈ 4 ký tự tiếng Việt)
  - Nếu < min_length (50 tokens) → Bỏ qua
  - Nếu > max_length (512 tokens) → Chia nhỏ
  - Nếu hợp lệ → Tạo sample

**2.4.2. Chia paragraph dài**
- Chia theo từ (word boundaries)
- Mỗi chunk ~512 tokens
- **Ví dụ:**
  ```python
  # Paragraph 2000 tokens
  chunks = [
    "Chunk 1 (512 tokens)",
    "Chunk 2 (512 tokens)",
    "Chunk 3 (512 tokens)",
    "Chunk 4 (464 tokens)"
  ]
  ```

**2.4.3. Tạo sample format**
- Mỗi sample là một dict:
  ```python
  {
    "text": "Nội dung đoạn văn...",
    "length": 512  # Số ký tự
  }
  ```

**Output:** List các samples: `samples = [sample1, sample2, ...]`

---

### Bước 2.5: Chia Dataset
**Mục đích:** Chia thành train/val/test sets

**Công việc:**

**2.5.1. Shuffle samples**
- Trộn ngẫu nhiên với random seed = 42 (để reproducible)
- **Ví dụ:**
  ```python
  # Trước shuffle: [1, 2, 3, ..., 10000]
  # Sau shuffle: [5234, 123, 7890, ..., 456]
  ```

**2.5.2. Chia theo tỷ lệ**
- Tính số samples cho mỗi set:
  - Train: 80% = 8,000 samples
  - Val: 10% = 1,000 samples
  - Test: 10% = 1,000 samples
- **Ví dụ:**
  ```python
  total = 10000
  train = shuffled[:8000]      # 80%
  val = shuffled[8000:9000]   # 10%
  test = shuffled[9000:]       # 10%
  ```

**2.5.3. Lưu datasets**
- `train.json`: 8,000 samples
- `val.json`: 1,000 samples
- `test.json`: 1,000 samples

**Output:** 3 files JSON chứa datasets

---

### Bước 2.6: Lưu Tokenizer và Metadata
**Mục đích:** Lưu tokenizer và thông tin dataset

**Công việc:**

**2.6.1. Lưu tokenizer**
- File: `tokenizer.pkl` (pickle format)
- Chứa: `word_to_id`, `id_to_word`, `vocab_size`, `special_tokens`

**2.6.2. Lưu metadata**
- File: `dataset_metadata.json`
- Format:
  ```json
  {
    "vocab_size": 50000,
    "train_samples": 8000,
    "val_samples": 1000,
    "test_samples": 1000,
    "total_samples": 10000
  }
  ```

## 📤 OUTPUT
```
data/dataset/
├── train.json              (8,000 samples)
├── val.json                (1,000 samples)
├── test.json               (1,000 samples)
├── tokenizer.pkl           (Tokenizer object)
└── dataset_metadata.json    (Metadata)
```

---

# 🔹 BƯỚC 3: TRAINING MODEL

## 📥 INPUT
```
data/dataset/
├── train.json
├── val.json
├── tokenizer.pkl
└── dataset_metadata.json
```

## 🔄 QUY TRÌNH CHI TIẾT

### Bước 3.1: Khởi tạo Model
**Mục đích:** Tạo model architecture

**Công việc:**

**3.1.1. Chọn architecture**
- **Option 1: GPT-2 từ HuggingFace** (Recommended)
  - Pre-trained, dễ sử dụng
  - Có thể fine-tune từ checkpoint
- **Option 2: Custom Transformer**
  - Tự implement từ đầu
  - Kiểm soát hoàn toàn architecture

**3.1.2. Cấu hình model**
```python
config = {
    "vocab_size": 50000,           # Từ vocabulary
    "hidden_size": 768,            # Kích thước hidden layer
    "num_layers": 12,              # Số transformer layers
    "num_heads": 12,               # Số attention heads
    "max_seq_length": 512,         # Độ dài tối đa sequence
    "dropout": 0.1                 # Dropout rate
}
```

**3.1.3. Khởi tạo model**
- Tạo model object với config trên
- Move model to device (GPU nếu có)

**Output:** Model object sẵn sàng để train

---

### Bước 3.2: Setup Training Environment
**Mục đích:** Chuẩn bị môi trường training

**Công việc:**

**3.2.1. Chọn device**
- Kiểm tra GPU có sẵn không
- Nếu có → dùng GPU (cuda:0)
- Nếu không → dùng CPU

**3.2.2. Tạo DataLoaders**
- **Train DataLoader:**
  - Batch size: 8
  - Shuffle: True
  - Num workers: 0 (Windows) hoặc 4+ (Linux)
- **Val DataLoader:**
  - Batch size: 8
  - Shuffle: False
  - Num workers: 0

**3.2.3. Setup Optimizer**
- Type: AdamW
- Learning rate: 5e-5
- Weight decay: 0.01
- Beta1: 0.9, Beta2: 0.999

**3.2.4. Setup Scheduler**
- Type: Cosine Annealing với Warmup
- Warmup steps: 10% tổng số steps
- T_max: Total steps - warmup steps

**Output:** Optimizer, Scheduler, DataLoaders sẵn sàng

---

### Bước 3.3: Training Loop
**Mục đích:** Train model qua nhiều epochs

**Công việc:**

**Cho mỗi epoch (1 → 3):**

**3.3.1. Training Phase**
```
For mỗi batch trong train_loader:
    1. Load batch:
       - input_ids: [batch_size, seq_length]
       - labels: [batch_size, seq_length]
    
    2. Forward pass:
       - output = model(input_ids)
       - logits = output.logits  # [batch_size, seq_length, vocab_size]
       - loss = CrossEntropyLoss(logits, labels)
    
    3. Backward pass:
       - loss.backward()
       - Tính gradients
    
    4. Gradient clipping:
       - clip_grad_norm_(max_norm=1.0)
       - Tránh gradient explosion
    
    5. Update weights:
       - optimizer.step()
       - Cập nhật model parameters
    
    6. Update learning rate:
       - scheduler.step()
       - Điều chỉnh LR theo schedule
    
    7. Reset gradients:
       - optimizer.zero_grad()
    
    8. Log (mỗi 100 steps):
       - In ra: step, loss, learning_rate
```

**Ví dụ một batch:**
```python
# Batch 1
input_ids = [[4, 5, 300, 200, ...],  # Sample 1
             [10, 20, 30, 40, ...],  # Sample 2
             ...]  # 8 samples

labels = [[5, 300, 200, 1, ...],     # Shift 1 position
          [20, 30, 40, 1, ...],
          ...]

# Forward
logits = model(input_ids)  # [8, 512, 50000]
loss = compute_loss(logits, labels)  # Scalar

# Backward & Update
loss.backward()
optimizer.step()
```

**3.3.2. Validation Phase (sau mỗi epoch)**
```
1. Set model.eval()  # Tắt dropout, batch norm

2. For mỗi batch trong val_loader:
    - Forward pass (không tính gradient)
    - Tính validation loss
    - Accumulate loss

3. Tính average validation loss
4. Tính perplexity = exp(avg_loss)

5. So sánh với best loss:
   - Nếu tốt hơn → Lưu best model
   - Cập nhật best_loss

6. In ra: epoch, train_loss, val_loss, perplexity
```

**3.3.3. Lưu Checkpoint**
- Sau mỗi epoch, lưu checkpoint:
  ```python
  checkpoint = {
      'epoch': epoch,
      'model_state_dict': model.state_dict(),
      'optimizer_state_dict': optimizer.state_dict(),
      'val_loss': val_loss,
      'perplexity': perplexity
  }
  torch.save(checkpoint, f'checkpoint-epoch-{epoch}/checkpoint.pt')
  ```

**Output:** 
- Checkpoints sau mỗi epoch
- Best model (dựa trên validation loss)

---

### Bước 3.4: Monitor Training
**Mục đích:** Theo dõi quá trình training

**Metrics cần theo dõi:**

**3.4.1. Training Loss**
- Giảm dần theo thời gian
- **Ví dụ:**
  - Epoch 1: 5.2 → 4.8
  - Epoch 2: 4.8 → 4.3
  - Epoch 3: 4.3 → 3.9

**3.4.2. Validation Loss**
- Giảm dần, không tăng (nếu tăng → overfitting)
- **Ví dụ:**
  - Epoch 1: 4.5
  - Epoch 2: 4.0
  - Epoch 3: 3.7

**3.4.3. Perplexity**
- Giảm dần (càng thấp càng tốt)
- **Ví dụ:**
  - Epoch 1: 90.0
  - Epoch 2: 54.6
  - Epoch 3: 40.5

**3.4.4. Learning Rate**
- Tăng trong warmup phase
- Giảm dần sau warmup (cosine schedule)

## 📤 OUTPUT
```
models/
├── checkpoint-epoch-1/
│   └── checkpoint.pt
├── checkpoint-epoch-2/
│   └── checkpoint.pt
├── checkpoint-epoch-3/
│   └── checkpoint.pt
└── best_model/
    └── model.pt          (Model với validation loss thấp nhất)
```

---

# 🔹 BƯỚC 4: ĐÁNH GIÁ (EVALUATION)

## 📥 INPUT
```
models/best_model/model.pt
data/dataset/test.json
data/dataset/tokenizer.pkl
```

## 🔄 QUY TRÌNH CHI TIẾT

### Bước 4.1: Load Model
**Mục đích:** Load model đã train để đánh giá

**Công việc:**
1. Load tokenizer từ `tokenizer.pkl`
2. Load model weights từ `model.pt`
3. Set model.eval() (tắt dropout, batch norm)
4. Move model to device (GPU/CPU)

**Output:** Model sẵn sàng để evaluate

---

### Bước 4.2: Tính Perplexity
**Mục đích:** Đo độ "bất ngờ" của model

**Công việc:**

**4.2.1. Load test dataset**
- Đọc `test.json`
- Tạo test DataLoader

**4.2.2. Tính loss trên test set**
```
total_loss = 0
total_tokens = 0

For mỗi batch trong test_loader:
    - Forward pass (không gradient)
    - Tính loss
    - Đếm số tokens (không tính padding)
    - Accumulate: total_loss += loss * num_tokens
    - Accumulate: total_tokens += num_tokens

avg_loss = total_loss / total_tokens
perplexity = exp(avg_loss)
```

**Ví dụ:**
```python
# Batch 1: loss=3.5, tokens=4000
# Batch 2: loss=3.6, tokens=4000
# ...
# Batch 10: loss=3.4, tokens=4000

avg_loss = (3.5*4000 + 3.6*4000 + ... + 3.4*4000) / 40000
          = 3.5
perplexity = exp(3.5) = 33.1
```

**4.2.3. Đánh giá kết quả**
- **Tốt:** Perplexity < 50
- **Khá:** Perplexity 50-100
- **Chưa tốt:** Perplexity > 100

**Output:** Perplexity score (số thực)

---

### Bước 4.3: Generate Text Samples
**Mục đích:** Tạo text mẫu để đánh giá chất lượng

**Công việc:**

**4.3.1. Lấy prompts từ test set**
- Lấy 10 samples từ test set
- Lấy 100 ký tự đầu của mỗi sample làm prompt
- **Ví dụ:**
  ```python
  prompt = "Nham Kiều đang đứng trên tường thành, nhìn xuống..."
  ```

**4.3.2. Generate text cho mỗi prompt**
```
For mỗi prompt:
    1. Encode prompt → token_ids
    
    2. Initialize generated = prompt_tokens
    
    3. Loop (max 200 tokens):
       a. Forward pass: model(generated) → logits
       b. Lấy logits của token cuối cùng
       c. Apply temperature, top-k, top-p filtering
       d. Sample token tiếp theo (multinomial)
       e. Append token vào generated
       f. Nếu gặp <EOS> → break
    
    4. Decode generated → text
    
    5. Loại bỏ prompt khỏi kết quả
```

**Ví dụ:**
```python
# Prompt
prompt = "Nham Kiều đang đứng"

# Generated (200 tokens)
generated = "Nham Kiều đang đứng trên tường thành, nhìn xuống phía dưới. Hắn thấy những cư dân đang cần cù trồng trọt. Một cảm giác hài lòng dâng trào trong lòng hắn. Cuối cùng cũng có được lãnh địa của riêng mình..."
```

**4.3.3. Lưu samples**
- Lưu prompt, generated text, original text (để so sánh)

**Output:** List các generated samples

---

### Bước 4.4: Đánh giá chất lượng
**Mục đích:** Đánh giá chất lượng generated text

**Tiêu chí đánh giá:**

**4.4.1. Coherence (Mạch lạc)**
- Text có mạch lạc, logic không?
- Các câu liên kết với nhau không?
- **Ví dụ tốt:** "Nham Kiều đứng trên tường. Hắn nhìn xuống. Thấy cư dân đang làm việc."
- **Ví dụ xấu:** "Nham Kiều đứng. Mưa rơi. Xe hơi chạy." (không liên quan)

**4.4.2. Relevance (Liên quan)**
- Generated text có liên quan đến prompt không?
- **Ví dụ tốt:** Prompt về "Nham Kiều" → Generated về "Nham Kiều"
- **Ví dụ xấu:** Prompt về "Nham Kiều" → Generated về "Hôm nay trời đẹp"

**4.4.3. Repetition (Lặp lại)**
- Có lặp lại quá nhiều không?
- **Ví dụ xấu:** "Nham Kiều Nham Kiều Nham Kiều đứng đứng đứng..."

**4.4.4. Grammar (Ngữ pháp)**
- Đúng ngữ pháp tiếng Việt không?
- Dấu câu đúng không?

**4.4.5. Length (Độ dài)**
- Generated text có đủ dài không? (không bị cắt ngắn)

**Output:** Đánh giá chất lượng (tốt/khá/chưa tốt) + nhận xét

---

### Bước 4.5: Lưu kết quả
**Mục đích:** Lưu kết quả đánh giá

**Công việc:**
1. Tạo file `evaluation_results.json`
2. Format:
```json
{
  "perplexity": 33.1,
  "test_loss": 3.5,
  "generated_samples": [
    {
      "prompt": "Nham Kiều đang đứng...",
      "generated": "Nham Kiều đang đứng trên tường thành...",
      "original": "Nham Kiều đang đứng trên tường thành, nhìn xuống..."
    },
    ...
  ],
  "quality_assessment": {
    "coherence": "Tốt",
    "relevance": "Tốt",
    "repetition": "Không có",
    "grammar": "Đúng"
  }
}
```

## 📤 OUTPUT
```
results/
└── evaluation_results.json
```

---

# 🔹 BƯỚC 5: INFERENCE (SỬ DỤNG MODEL)

## 📥 INPUT
```
models/best_model/model.pt
data/dataset/tokenizer.pkl
User prompt (text)
```

## 🔄 QUY TRÌNH CHI TIẾT

### Bước 5.1: Load Model
**Mục đích:** Load model đã train

**Công việc:**
1. Load tokenizer từ `tokenizer.pkl`
2. Load model weights từ `model.pt`
3. Set model.eval()
4. Move to device

**Output:** Model sẵn sàng để generate

---

### Bước 5.2: Nhận Prompt
**Mục đích:** Lấy prompt từ user

**Các chế độ:**

**5.2.1. Interactive Mode**
```
Loop:
    1. Print: "Nhập prompt (hoặc 'quit' để thoát):"
    2. User nhập prompt
    3. Nếu 'quit' → break
    4. Nếu prompt rỗng → continue
    5. Generate text từ prompt
    6. In kết quả
    7. Lặp lại
```

**5.2.2. Single Generation**
```
1. Prompt từ command line: --prompt "Nham Kiều đang đứng"
2. Generate text
3. In kết quả
4. Exit
```

**5.2.3. Batch Generation**
```
1. Đọc file prompts.txt (mỗi dòng một prompt)
2. For mỗi prompt:
   - Generate text
   - Lưu vào results
3. Lưu tất cả results vào file JSON
```

**Output:** Prompt text (string)

---

### Bước 5.3: Encode Prompt
**Mục đích:** Chuyển prompt thành tokens

**Công việc:**
1. Format prompt (nếu có template):
   ```python
   formatted = f"Tiếp theo câu chuyện:\n\n{prompt}\n\n"
   ```
2. Encode: `token_ids = tokenizer.encode(formatted)`
3. Convert to tensor
4. Move to device

**Ví dụ:**
```python
prompt = "Nham Kiều đang đứng"
formatted = "Tiếp theo câu chuyện:\n\nNham Kiều đang đứng\n\n"
token_ids = [2, 4, 5, 300, 200, ...]  # [<BOS>, Nham, Kiều, đang, đứng, ...]
tensor = torch.tensor([token_ids]).to(device)
```

**Output:** Token tensor: `[1, seq_length]`

---

### Bước 5.4: Generate Text
**Mục đích:** Generate text tiếp theo từ prompt

**Công việc:**

**5.4.1. Initialize**
```python
generated = prompt_tokens.clone()  # Bắt đầu từ prompt
```

**5.4.2. Generation Loop**
```
For i in range(max_length):
    1. Forward pass:
       - output = model(generated)
       - logits = output.logits[:, -1, :]  # Lấy logits của token cuối
    
    2. Apply temperature:
       - logits = logits / temperature
       - Temperature cao → random hơn
       - Temperature thấp → deterministic hơn
    
    3. Top-k filtering:
       - Lấy top 50 tokens có logits cao nhất
       - Set các tokens khác = -inf
    
    4. Top-p (nucleus) filtering:
       - Sort tokens theo probability
       - Lấy tokens có cumulative prob <= 0.9
       - Set các tokens khác = -inf
    
    5. Sample:
       - probs = softmax(logits)
       - next_token = multinomial(probs)
    
    6. Append:
       - generated = concat([generated, next_token])
    
    7. Check stop condition:
       - Nếu next_token == <EOS> → break
       - Nếu len(generated) >= max_length → break
```

**Ví dụ một iteration:**
```python
# Current generated: [2, 4, 5, 300, 200]  # [<BOS>, Nham, Kiều, đang, đứng]

# Forward
logits = model(generated)  # [1, 5, 50000]
last_logits = logits[0, -1, :]  # [50000] - logits cho token tiếp theo

# Apply filters
filtered_logits = apply_topk_topp(last_logits, top_k=50, top_p=0.9)

# Sample
probs = softmax(filtered_logits / 0.8)  # temperature=0.8
next_token = sample(probs)  # Ví dụ: 150 (token ID của "trên")

# Append
generated = [2, 4, 5, 300, 200, 150]  # Thêm "trên"
```

**5.4.3. Decode**
```python
# Generated tokens: [2, 4, 5, 300, 200, 150, ...]
# Decode
text = tokenizer.decode(generated)
# "Tiếp theo câu chuyện:\n\nNham Kiều đang đứng trên..."
```

**5.4.4. Post-process**
- Loại bỏ prompt khỏi kết quả
- Loại bỏ special tokens
- Format output

**Ví dụ:**
```python
# Full generated
full = "Tiếp theo câu chuyện:\n\nNham Kiều đang đứng trên tường thành..."

# Remove prompt
result = "trên tường thành, nhìn xuống phía dưới. Hắn thấy những cư dân đang cần cù trồng trọt..."
```

**Output:** Generated text (string)

---

### Bước 5.5: Trả về kết quả
**Mục đích:** Hiển thị/lưu kết quả

**Công việc:**

**5.5.1. Interactive Mode**
```python
print("\n📝 Kết quả:")
print("-" * 60)
print(generated_text)
print("-" * 60)
print()
```

**5.5.2. Single Generation**
```python
print(f"\n📝 Generated text:")
print("-" * 60)
print(generated_text)
print("-" * 60)
```

**5.5.3. Batch Generation**
```python
results = []
for prompt in prompts:
    generated = generate(prompt)
    results.append({
        "prompt": prompt,
        "generated": generated
    })

# Lưu vào file
with open("batch_results.json", 'w') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
```

## 📤 OUTPUT
- **Interactive/Single:** Text in ra console
- **Batch:** File JSON chứa tất cả results

---

## 📊 TỔNG KẾT QUY TRÌNH

### Input → Output của từng bước:

```
Bước 1: Raw text files → Cleaned paragraphs
Bước 2: Cleaned paragraphs → Train/Val/Test datasets + Tokenizer
Bước 3: Datasets → Trained model + Checkpoints
Bước 4: Trained model → Evaluation metrics + Generated samples
Bước 5: Trained model + User prompt → Generated text
```

### Thời gian ước tính (với dataset ~10,000 samples):

- **Bước 1:** 5-10 phút
- **Bước 2:** 10-15 phút
- **Bước 3:** 2-6 giờ (tùy GPU/CPU)
- **Bước 4:** 5-10 phút
- **Bước 5:** < 1 giây mỗi generation

### Dung lượng ước tính:

- **Preprocessed data:** ~50-100 MB
- **Dataset:** ~100-200 MB
- **Model:** ~300-500 MB (tùy size)
- **Checkpoints:** ~1-2 GB (nếu lưu nhiều)

---

**Quy trình này đã được mô tả rất chi tiết, từng bước cụ thể! 🎯**

