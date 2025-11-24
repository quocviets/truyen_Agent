# AI Agent Project

## 📁 Cấu trúc thư mục

```
project_root/
│
├── training/              # Training pipeline cho Language Model
│   ├── dataset/
│   │   ├── raw/           # Dữ liệu thô (truyenmoiii_output)
│   │   ├── preprocessed/  # Dữ liệu đã tiền xử lý
│   │   ├── tokenized/     # Dữ liệu đã tokenize
│   │   └── splits/        # Train/val/test splits
│   ├── tokenizer/         # Tokenizer models
│   ├── model/             # Trained models
│   ├── trainer/           # Training scripts
│   └── configs/           # Configuration files
│
├── agent/                 # AI Agent system
│   ├── runtime/
│   │   ├── prompts/       # Prompt templates
│   │   ├── actions/       # Action handlers
│   │   ├── tools/         # Tool definitions
│   │   ├── memory/        # Memory management
│   │   └── logs/          # Runtime logs
│   ├── controller/        # Agent controller
│   ├── execution/         # Execution engine
│   └── evaluator/         # Evaluation metrics
│
├── distillation/          # Knowledge distillation
│   ├── analyzer/          # Analysis tools
│   ├── synthesizer/       # Synthesis components
│   ├── skill_extractor/   # Skill extraction
│   └── knowledge_graph/   # Knowledge graph
│
├── skills/                # Agent skills
│   ├── core/              # Core skills
│   ├── emergent/          # Emergent skills
│   └── meta/              # Meta skills
│
└── system/                # System components
    ├── orchestrator/      # System orchestrator
    ├── persistence/       # Data persistence
    ├── cli/               # CLI interface
    └── configs/           # System configs
```

## 📊 Dữ liệu

Dữ liệu training được lưu trong `training/dataset/raw/truyenmoiii_output/`:
- **11 truyện** với tổng cộng **19,966 chapters**
- Xem chi tiết trong `training/configs/DANH_SACH_VAN_DE.md`

## 🚀 Bắt đầu

1. **Preprocessing:** Xử lý dữ liệu thô trong `training/dataset/raw/`
2. **Training:** Huấn luyện model trong `training/trainer/`
3. **Agent:** Sử dụng model đã train trong `agent/`

## 📝 Tài liệu

### Training
- `training/configs/QUY_TRINH_CHI_TIET.md` - Quy trình pipeline chi tiết
- `training/configs/BAO_CAO_DU_LIEU.md` - Báo cáo tổng hợp dữ liệu
- `training/configs/DANH_SACH_VAN_DE.md` - Danh sách vấn đề phát hiện

### System Architecture
- `system/configs/MODULE_ARCHITECTURE.md` - Kiến trúc chi tiết từng module
- `system/configs/SKELETON_TEMPLATES.md` - Templates, prompts, và checklists

