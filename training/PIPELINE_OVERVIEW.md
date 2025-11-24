## PIPELINE TỔNG QUAN

### Phase 0 – Data Check
- Xác nhận raw chapters đầy đủ; bỏ qua lỗi JSON nhỏ.
- Log tình trạng dữ liệu trước khi xử lý.

### Phase 1 – Offline Learning
- Preprocess chapters: clean text, filter short.
- Build dataset + tokenizer.
- Train StoryBaseModel (LM).
- Evaluate via perplexity + sample generations.

### Phase 2 – Writer Agent
- Writer Agent (API + Memory + Vector Store).
- Tạo đề cương: world, characters, arcs, chapter plan.
- Viết chương: outline + context + model → draft.
- Lưu chương + summary + metadata.

### Phase 3 – Distillation (Karpathy)
- Log prompt, model_output, user edits, scores.
- Xây Distillation Dataset từ feedback.
- Fine-tune StorySkillModel trên data mới.
- Cập nhật Agent dùng StorySkillModel để cải thiện chất lượng.

### Phase 4 – Vận Hành
- Versioning cho models, datasets, agents.
- Config per project.
- Export truyện + metadata.

