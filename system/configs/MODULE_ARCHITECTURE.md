# 🏗️ KIẾN TRÚC MODULE CHI TIẾT

## 📋 MỤC LỤC

- [A. TRAINING (LLM Training Pipeline)](#a-training-llm-training-pipeline)
- [B. AGENT (Online Runtime System)](#b-agent-online-runtime-system)
- [C. DISTILLATION (Learning from Experience)](#c-distillation-learning-from-experience)
- [D. SKILLS (Accumulated Agent Skills)](#d-skills-accumulated-agent-skills)
- [E. SYSTEM (Điều phối toàn bộ hệ thống)](#e-system-điều-phối-toàn-bộ-hệ-thống)
- [Luồng hoạt động End-to-End](#luồng-hoạt-động-end-to-end)

---

## 🟦 A. TRAINING (LLM TRAINING PIPELINE)

### 📁 `/training/dataset/`

#### `raw/`
- **Mục đích:** Chứa chapters từ crawler
- **Nội dung:** 
  - File chapter gốc (chapter_*.txt)
  - novel_summary.json (metadata)
  - Cấu trúc: `raw/truyenmoiii_output/{novel_name}/chapter_*.txt`

#### `preprocessed/`
- **Mục đích:** File sạch, đã chuẩn hóa
- **Xử lý:**
  - Loại bỏ HTML tags
  - Chuẩn hóa whitespace
  - Loại bỏ ký tự đặc biệt không cần thiết
  - Filter chapter quá ngắn (< 500 bytes hoặc < 10% trung bình)
  - Normalize encoding (UTF-8)
  - Format: Một file text lớn hoặc nhiều file đã clean

#### `tokenized/`
- **Mục đích:** Data đã encoded
- **Nội dung:**
  - Token IDs thay vì text
  - Format: PyTorch tensors hoặc JSON arrays
  - Có thể chia thành chunks nếu cần

#### `splits/`
- **Mục đích:** Train/val/test splits
- **Cấu trúc:**
  - `train.txt` hoặc `train.pt`
  - `val.txt` hoặc `val.pt`
  - `test.txt` hoặc `test.pt`
  - Split ratio: 80/10/10 hoặc 90/5/5

---

### 📁 `/training/tokenizer/`

#### `tokenizer_config`
- **Mục đích:** Cấu hình tokenizer
- **Nội dung:**
  - Tokenizer type (BPE, WordPiece, SentencePiece)
  - Special tokens (PAD, UNK, BOS, EOS, SEP)
  - Max sequence length
  - Vocabulary size

#### `vocab`
- **Mục đích:** Vocabulary file
- **Format:**
  - `vocab.json` - mapping token → id
  - `merges.txt` - BPE merges (nếu dùng BPE)
  - Hoặc `vocab.txt` - word list

#### `vocabulary builder`
- **Mục đích:** Script/build tool để tạo vocabulary
- **Chức năng:**
  - Đọc từ preprocessed data
  - Tính toán frequency
  - Xây dựng vocabulary
  - Lưu vocab file

---

### 📁 `/training/model/`

#### `model architecture`
- **Mục đích:** Định nghĩa kiến trúc model
- **Nội dung:**
  - Transformer architecture (GPT-2, GPT-Neo, hoặc custom)
  - Layer definitions
  - Attention mechanisms
  - Position embeddings
  - File: `model.py` hoặc `architecture.py`

#### `checkpoint manager`
- **Mục đích:** Quản lý checkpoints
- **Chức năng:**
  - Lưu checkpoint định kỳ
  - Load checkpoint để resume
  - Quản lý version (best, latest, epoch_N)
  - Format: `.pt`, `.pth`, hoặc `.ckpt`

---

### 📁 `/training/trainer/`

#### `training loop skeleton`
- **Mục đích:** Vòng lặp training chính
- **Chức năng:**
  - Iterate qua batches
  - Forward pass
  - Loss calculation
  - Backward pass
  - Optimizer step
  - Learning rate scheduling

#### `validation loop`
- **Mục đích:** Đánh giá model trên validation set
- **Chức năng:**
  - Forward pass (no gradient)
  - Tính metrics (perplexity, loss)
  - So sánh với best model
  - Quyết định save checkpoint

#### `logging`
- **Mục đích:** Ghi log quá trình training
- **Nội dung:**
  - Loss per epoch/batch
  - Learning rate
  - Validation metrics
  - Training time
  - GPU usage
  - Format: TensorBoard, CSV, hoặc JSON

---

### 📁 `/training/configs/`

#### `training hyperparameters`
- **Mục đích:** Cấu hình training
- **Nội dung:**
  - Batch size
  - Learning rate
  - Number of epochs
  - Gradient accumulation
  - Warmup steps
  - Weight decay
  - Optimizer (Adam, AdamW)
  - File: `training_config.yaml` hoặc `training_config.json`

#### `tokenizer config`
- **Mục đích:** Cấu hình tokenizer
- **Nội dung:**
  - Vocabulary size
  - Max sequence length
  - Special tokens
  - File: `tokenizer_config.yaml` hoặc `tokenizer_config.json`

---

## 🟧 B. AGENT (ONLINE RUNTIME SYSTEM)

> **Lưu ý:** Đây là phần sẽ tương tác với người dùng hoặc job thực tế

### 📁 `/agent/runtime/prompts/`

#### `system_prompt.txt`
- **Mục đích:** System prompt chính cho agent
- **Nội dung:**
  - Role definition
  - Capabilities
  - Constraints
  - Behavior guidelines
  - Knowledge injection từ skills/

#### `rewrite_prompt.txt`
- **Mục đích:** Prompt cho task rewrite/paraphrase
- **Nội dung:**
  - Hướng dẫn rewrite text
  - Style guidelines
  - Quality criteria

#### `storytelling_prompt.txt`
- **Mục đích:** Prompt cho task storytelling
- **Nội dung:**
  - Hướng dẫn viết truyện
  - Story structure
  - Character development
  - Plot progression

#### `tool_usage_guidelines.txt`
- **Mục đích:** Hướng dẫn sử dụng tools
- **Nội dung:**
  - Khi nào dùng tool nào
  - Cách gọi tool
  - Error handling
  - Retry logic

---

### 📁 `/agent/runtime/actions/`

#### `action_scheduler`
- **Mục đích:** Quyết định bước tiếp theo
- **Chức năng:**
  - Phân tích current state
  - Đánh giá các action khả thi
  - Chọn action tốt nhất
  - File: `action_scheduler.py`

#### `action_graph`
- **Mục đích:** Luồng workflow khả thi
- **Nội dung:**
  - Graph các action có thể thực hiện
  - Dependencies giữa actions
  - State transitions
  - File: `action_graph.py` hoặc `action_graph.json`

---

### 📁 `/agent/runtime/tools/`

#### `tool definitions`
- **Mục đích:** Định nghĩa các tools
- **Tools:**
  - Crawler (web scraping)
  - Search (tìm kiếm)
  - File ops (đọc/ghi file)
  - Text processing
  - File: `tools.py` hoặc `tool_definitions.py`

#### `tool registry`
- **Mục đích:** Đăng ký và quản lý tools
- **Chức năng:**
  - Register tools
  - Lookup tool by name
  - Validate tool parameters
  - File: `tool_registry.py`

#### `tool permissions`
- **Mục đích:** Quản lý quyền truy cập tools
- **Nội dung:**
  - Tool nào agent được dùng
  - Security constraints
  - Rate limiting
  - File: `tool_permissions.py` hoặc `tool_permissions.json`

---

### 📁 `/agent/runtime/memory/`

#### `short-term memory`
- **Mục đích:** Bộ nhớ ngắn hạn cho conversation
- **Nội dung:**
  - Current conversation context
  - Recent actions
  - Recent tool calls
  - Format: In-memory (dict/list) hoặc temporary file

#### `long-term memory index`
- **Mục đích:** Index cho long-term memory
- **Nội dung:**
  - Vector embeddings của past experiences
  - Searchable index
  - Retrieval mechanism
  - Format: Vector database (FAISS, Chroma) hoặc SQLite

#### `retrieval logic`
- **Mục đích:** Logic tìm kiếm trong memory
- **Chức năng:**
  - Semantic search
  - Similarity matching
  - Context retrieval
  - File: `retrieval.py`

---

### 📁 `/agent/runtime/logs/`

#### `raw_logs/`
- **Mục đích:** True logs của agent
- **Nội dung:**
  - Mọi action agent thực hiện
  - Tool calls và results
  - Reasoning steps
  - Errors và retries
  - Format: JSON lines hoặc structured logs

#### `trace/`
- **Mục đích:** Trace chain
- **Nội dung:**
  - Execution trace
  - Call stack
  - Decision points
  - Format: JSON hoặc text

#### `metadata.json`
- **Mục đích:** Metadata về session
- **Nội dung:**
  - Session ID
  - Timestamp
  - User query
  - Final result
  - Success/failure
  - Duration

---

### 📁 `/agent/controller/`

#### `policy`
- **Mục đích:** Chọn hành động
- **Chức năng:**
  - Policy network hoặc rule-based
  - Action selection
  - Exploration vs exploitation
  - File: `policy.py`

#### `reasoner`
- **Mục đích:** Chain-of-thought simulation
- **Chức năng:**
  - Generate reasoning steps
  - Simulate outcomes
  - Evaluate options
  - File: `reasoner.py`

#### `error_handler`
- **Mục đích:** Fallback logic
- **Chức năng:**
  - Catch errors
  - Retry với strategy khác
  - Fallback to simpler approach
  - Log errors
  - File: `error_handler.py`

---

### 📁 `/agent/execution/`

#### `execution engine`
- **Mục đích:** Engine thực thi actions
- **Chức năng:**
  - Execute action sequence
  - Manage state
  - Handle interruptions
  - File: `execution_engine.py`

#### `tool calling engine`
- **Mục đích:** Engine gọi tools
- **Chức năng:**
  - Parse tool call từ LLM
  - Validate parameters
  - Execute tool
  - Handle errors
  - Return results
  - File: `tool_calling_engine.py`

#### `response compiler`
- **Mục đích:** Biên dịch response cuối cùng
- **Chức năng:**
  - Tổng hợp kết quả
  - Format response
  - Add metadata
  - File: `response_compiler.py`

---

### 📁 `/agent/evaluator/`

#### `evaluate good/bad steps`
- **Mục đích:** Đánh giá từng bước
- **Chức năng:**
  - Score mỗi action
  - Identify successful steps
  - Identify failed steps
  - File: `step_evaluator.py`

#### `score reasoning quality`
- **Mục đích:** Đánh giá chất lượng reasoning
- **Chức năng:**
  - Coherence score
  - Logical consistency
  - Completeness
  - File: `reasoning_evaluator.py`

#### `detect hallucination`
- **Mục đích:** Phát hiện hallucination
- **Chức năng:**
  - So sánh với ground truth (nếu có)
  - Fact checking
  - Consistency checking
  - File: `hallucination_detector.py`

#### `detect repetition`
- **Mục đích:** Phát hiện lặp lại
- **Chức năng:**
  - Detect repeated actions
  - Detect repeated outputs
  - Detect loops
  - File: `repetition_detector.py`

---

## 🟨 C. DISTILLATION (LEARNING FROM EXPERIENCE)

> **Lưu ý:** Đây là phần quan trọng nhất — transform logs thành kỹ năng

### 📁 `/distillation/analyzer/`

#### `phân tích log`
- **Mục đích:** Phân tích logs từ agent
- **Chức năng:**
  - Parse log files
  - Extract events
  - Identify patterns
  - File: `log_analyzer.py`

#### `phát hiện patterns`
- **Mục đích:** Tìm patterns trong behavior
- **Chức năng:**
  - Frequent action sequences
  - Successful strategies
  - Common mistakes
  - File: `pattern_detector.py`

#### `phát hiện lỗi`
- **Mục đích:** Tìm lỗi trong execution
- **Chức năng:**
  - Error patterns
  - Failure modes
  - Root cause analysis
  - File: `error_detector.py`

#### `tóm tắt behavior`
- **Mục đích:** Tóm tắt behavior của agent
- **Chức năng:**
  - Summarize session
  - Extract key decisions
  - Identify turning points
  - File: `behavior_summarizer.py`

#### `scoring signal (success/fail)`
- **Mục đích:** Đánh giá success/failure
- **Chức năng:**
  - Success criteria
  - Failure indicators
  - Score calculation
  - File: `scoring.py`

---

### 📁 `/distillation/synthesizer/`

#### `tạo synthetic samples`
- **Mục đích:** Tạo samples tổng hợp
- **Chức năng:**
  - Generate training examples từ logs
  - Create variations
  - Augment data
  - File: `synthetic_generator.py`

#### `tạo rule descriptions`
- **Mục đích:** Tạo mô tả rules
- **Chức năng:**
  - Extract rules từ behavior
  - Describe patterns
  - Format as text
  - File: `rule_generator.py`

#### `tạo generalized heuristics`
- **Mục đích:** Tạo heuristics tổng quát
- **Chức năng:**
  - Generalize từ specific cases
  - Create reusable heuristics
  - File: `heuristic_generator.py`

---

### 📁 `/distillation/skill_extractor/`

#### `tách hành vi lặp lại`
- **Mục đích:** Tìm hành vi lặp lại
- **Chức năng:**
  - Identify recurring patterns
  - Extract common sequences
  - File: `behavior_extractor.py`

#### `tạo skill file markdown (skill_x.md)`
- **Mục đích:** Tạo file skill
- **Format:**
  - Skill name
  - Description
  - When to use
  - How to apply
  - Examples
  - Dependencies
  - File: `skill_generator.py`

#### `compress chain-of-thought thành chiến lược`
- **Mục đích:** Nén reasoning thành strategy
- **Chức năng:**
  - Extract key reasoning steps
  - Remove redundant steps
  - Create concise strategy
  - File: `strategy_compressor.py`

---

### 📁 `/distillation/knowledge_graph/`

#### `graph quan hệ giữa skills`
- **Mục đích:** Mô hình hóa quan hệ skills
- **Nội dung:**
  - Skills và connections
  - Similarity relationships
  - Usage relationships
  - Format: Graph database hoặc JSON
  - File: `skill_graph.py`

#### `dependency mapping (kỹ năng nào cần kỹ năng nào)`
- **Mục đích:** Map dependencies
- **Nội dung:**
  - Skill A requires Skill B
  - Prerequisites
  - Ordering constraints
  - File: `dependency_mapper.py`

#### `versioning: skill_v1 → skill_v2 → skill_v3`
- **Mục đích:** Quản lý version skills
- **Chức năng:**
  - Track skill versions
  - Compare versions
  - Migration logic
  - File: `skill_versioning.py`

---

## 🟩 D. SKILLS (ACCUMULATED AGENT SKILLS)

> **Lưu ý:** Agent càng chạy càng giỏi — nhờ folder này

### 📁 `/skills/core/`

**Mục đích:** Kỹ năng gốc (logic cơ bản)

#### Ví dụ skills:

##### `reasoning basics`
- Basic logical reasoning
- Step-by-step thinking
- File: `reasoning_basics.md`

##### `anti-repetition`
- Detect và tránh lặp lại
- Break loops
- File: `anti_repetition.md`

##### `consistency checker`
- Check consistency
- Validate outputs
- File: `consistency_checker.md`

##### `pagination recognizer`
- Nhận diện pagination
- Navigate multi-page content
- File: `pagination_recognizer.md`

---

### 📁 `/skills/emergent/`

**Mục đích:** Kỹ năng phát sinh từ trải nghiệm

#### Ví dụ skills:

##### `skill_retry429.md`
- Retry khi gặp HTTP 429
- Exponential backoff
- Rate limiting handling

##### `skill_fix_xpath.md`
- Fix XPath khi selector fail
- Alternative selectors
- Fallback strategies

##### `skill_plot_structure.md`
- Nhận diện cấu trúc plot
- Extract story elements
- Analyze narrative

##### `skill_outline_generation.md`
- Generate outline từ content
- Structure information
- Create summaries

---

### 📁 `/skills/meta/`

**Mục đích:** Meta-skill (kỹ năng điều chỉnh kỹ năng)

#### Ví dụ skills:

##### `meta_error_repair.md`
- Repair errors tự động
- Self-correction
- Error recovery strategies

##### `meta_fallback_chain.md`
- Chain of fallbacks
- Progressive degradation
- Last resort strategies

##### `meta_self_reflection.md`
- Self-reflection
- Evaluate own performance
- Identify improvements

---

## 🟪 E. SYSTEM (ĐIỀU PHỐI TOÀN BỘ HỆ THỐNG)

### 📁 `/system/orchestrator/`

#### `orchestration pipeline`
- **Mục đích:** Điều phối pipeline
- **Chức năng:**
  - Chạy training → agent → distillation
  - Manage dependencies
  - Handle failures
  - File: `orchestrator.py`

#### `pipeline scheduling`
- **Mục đích:** Lên lịch chạy pipeline
- **Chức năng:**
  - Schedule training jobs
  - Schedule distillation jobs
  - Resource management
  - File: `scheduler.py`

---

### 📁 `/system/persistence/`

#### `ghi nhớ long-term`
- **Mục đích:** Lưu trữ dài hạn
- **Nội dung:**
  - Database (SQLite, PostgreSQL)
  - Hoặc local file storage
  - Skills, logs, models
  - File: `persistence.py`

#### `versioning of skills`
- **Mục đích:** Quản lý version skills
- **Chức năng:**
  - Track skill versions
  - Rollback capability
  - File: `skill_versioning.py`

---

### 📁 `/system/cli/`

**Mục đích:** CLI để chạy pipeline

#### Commands:

##### `train`
- Chạy training pipeline
- Usage: `python -m system.cli train [options]`

##### `run-agent`
- Chạy agent
- Usage: `python -m system.cli run-agent [query]`

##### `distill`
- Chạy distillation
- Usage: `python -m system.cli distill [log_path]`

##### `update-skills`
- Cập nhật skills
- Usage: `python -m system.cli update-skills`

##### `eval`
- Đánh giá model/agent
- Usage: `python -m system.cli eval [options]`

---

### 📁 `/system/configs/`

#### `cấu hình global`
- **Mục đích:** Cấu hình toàn hệ thống
- **Nội dung:**
  - Model paths
  - Data paths
  - Log paths
  - File: `global_config.yaml`

#### `API keys`
- **Mục đích:** Quản lý API keys
- **Nội dung:**
  - LLM API keys
  - External service keys
  - File: `.env` hoặc `api_keys.json` (gitignored)

#### `LLM provider`
- **Mục đích:** Cấu hình LLM provider
- **Nội dung:**
  - Provider (OpenAI, Anthropic, local)
  - Model name
  - Parameters
  - File: `llm_config.yaml`

#### `storage path`
- **Mục đích:** Đường dẫn lưu trữ
- **Nội dung:**
  - Model storage
  - Data storage
  - Log storage
  - File: `storage_config.yaml`

---

## 🧠 LUỒNG HOẠT ĐỘNG END TO END

### 1. TRAINING PHASE (Offline)

```
1. Load raw data
   └─> training/dataset/raw/truyenmoiii_output/

2. Preprocess
   └─> training/dataset/preprocessed/

3. Tokenize
   └─> training/dataset/tokenized/

4. Create dataset
   └─> training/dataset/splits/ (train/val/test)

5. Train LLM base
   └─> training/trainer/

6. Save model
   └─> training/model/base_model.pt
   └─> training/tokenizer/

Output: base_model.pt + tokenizer
```

### 2. AGENT PHASE (Online)

```
1. Load base model
   └─> training/model/base_model.pt

2. Load skills/
   └─> skills/core/
   └─> skills/emergent/
   └─> skills/meta/

3. Load system prompts
   └─> agent/runtime/prompts/

4. User request → Agent reasoning
   └─> agent/controller/reasoner.py

5. Tool calls, retries, fallback
   └─> agent/runtime/tools/
   └─> agent/controller/error_handler.py

6. Log every step
   └─> agent/runtime/logs/raw_logs/
   └─> agent/runtime/logs/trace/

Output: logs + task result
```

### 3. DISTILLATION PHASE

```
1. Read logs
   └─> agent/runtime/logs/raw_logs/

2. Detect patterns, mistakes, successful strategies
   └─> distillation/analyzer/

3. Generate new skills .md
   └─> distillation/skill_extractor/

4. Save to skills/emergent/
   └─> skills/emergent/skill_*.md

5. Update skill index
   └─> distillation/knowledge_graph/

Output: new skills files
```

### 4. NEXT RUN

```
1. Agent load new skill files
   └─> skills/emergent/skill_*.md

2. Context injected automatically
   └─> agent/runtime/prompts/ (updated)

3. Agent năng lực tăng lên 1 cấp

Effect: continual improvement without re-training
```

---

## 📝 GHI CHÚ QUAN TRỌNG

### Khi bắt đầu code:

1. **Training Module:**
   - Bắt đầu từ `training/dataset/raw/` (dữ liệu đã có)
   - Tạo preprocessing pipeline
   - Build tokenizer
   - Train model

2. **Agent Module:**
   - Load trained model
   - Implement runtime system
   - Create tool registry
   - Implement logging

3. **Distillation Module:**
   - Analyze logs
   - Extract patterns
   - Generate skills
   - Update knowledge graph

4. **Skills Module:**
   - Start với core skills
   - Emergent skills sẽ được tạo tự động
   - Meta skills cho advanced behavior

5. **System Module:**
   - Orchestrator để chạy toàn bộ pipeline
   - CLI để tương tác
   - Configs để quản lý settings

---

## 🔄 QUAN HỆ GIỮA CÁC MODULE

```
TRAINING (Offline)
    ↓
    └─> Model + Tokenizer
            ↓
        AGENT (Online)
            ↓
            └─> Logs
                    ↓
                DISTILLATION
                    ↓
                    └─> Skills
                            ↓
                        AGENT (Next Run)
                            └─> Improved Agent
```

---

**File này là tài liệu tham khảo chi tiết cho toàn bộ kiến trúc. Khi bắt đầu code, tham khảo từng module tương ứng.**

