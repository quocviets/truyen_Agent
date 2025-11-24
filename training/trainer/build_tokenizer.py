"""
Build SentencePiece tokenizer từ train split cho tiếng Việt.

Chiến lược:
    1. Đọc training/dataset/splits/train.jsonl (chỉ dùng train để train tokenizer).
    2. Extract text từ mỗi paragraph, ghi vào file tạm (1 dòng = 1 paragraph).
    3. Train SentencePiece tokenizer với vocab size 32k-50k (phù hợp model 1-3B).
    4. Lưu model + vocab vào training/tokenizer/.
    5. Test tokenizer trên sample text để verify.

Yêu cầu:
    pip install sentencepiece
    python training/trainer/build_tokenizer.py \
        --input-jsonl training/dataset/splits/train.jsonl \
        --output-dir training/tokenizer \
        --vocab-size 32000 \
        --model-type bpe
"""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path
from typing import List

import sentencepiece as spm

from .config import Paths, TokenizerConfig
from .utils import setup_encoding, save_json

# Setup encoding for Windows
setup_encoding()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build SentencePiece tokenizer từ train split")
    parser.add_argument(
        "--input-jsonl",
        type=Path,
        default=Paths.TRAIN_JSONL,
        help="File train.jsonl chứa paragraphs để train tokenizer"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Paths.TOKENIZER_DIR,
        help="Thư mục lưu tokenizer model và vocab"
    )
    parser.add_argument(
        "--vocab-size",
        type=int,
        default=32000,
        help="Vocab size cho tokenizer (default: 32000, phù hợp model 1-3B)"
    )
    parser.add_argument(
        "--model-type",
        choices=["bpe", "unigram"],
        default="bpe",
        help="Loại SentencePiece model: bpe (Byte Pair Encoding) hoặc unigram (default: bpe)"
    )
    parser.add_argument(
        "--character-coverage",
        type=float,
        default=0.9995,
        help="Character coverage cho tiếng Việt (default: 0.9995, cao hơn tiếng Anh vì có dấu)"
    )
    parser.add_argument(
        "--test-samples",
        type=int,
        default=5,
        help="Số sample text để test tokenizer sau khi train (default: 5)"
    )
    return parser.parse_args()


def load_train_texts(input_jsonl: Path) -> List[str]:
    """
    Đọc file train.jsonl và extract text từ mỗi paragraph.
    
    Args:
        input_jsonl: Đường dẫn đến file train.jsonl
        
    Returns:
        List các đoạn text (mỗi đoạn = 1 paragraph)
    """
    from .utils import read_jsonl
    
    texts = []
    print(f"📖 Đang đọc {input_jsonl}...")
    
    for record in read_jsonl(input_jsonl):
        text = record.get('text', '').strip()
        if text:
            texts.append(text)
    
    print(f"✅ Đã đọc {len(texts):,} paragraphs")
    
    # Cảnh báo nếu data quá ít
    if len(texts) < 10000:
        print(f"⚠️  Warning: Số paragraph train hơi ít ({len(texts):,}), tokenizer có thể không ổn định.")
    
    return texts


def train_tokenizer(
    texts: List[str],
    output_dir: Path,
    vocab_size: int,
    model_type: str,
    character_coverage: float
) -> Path:
    """
    Train SentencePiece tokenizer từ danh sách texts.
    
    Args:
        texts: List các đoạn text để train
        output_dir: Thư mục lưu tokenizer
        vocab_size: Kích thước vocab
        model_type: "bpe" hoặc "unigram"
        character_coverage: Character coverage (0.9995 cho tiếng Việt)
        
    Returns:
        Đường dẫn đến file model đã train
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Tạo file tạm chứa text (SentencePiece yêu cầu file input)
    print("📝 Đang tạo file tạm cho SentencePiece...")
    with tempfile.NamedTemporaryFile(
        mode='w',
        encoding='utf-8',
        suffix='.txt',
        delete=False
    ) as tmp_file:
        tmp_path = Path(tmp_file.name)
        for text in texts:
            # Ghi mỗi paragraph trên 1 dòng
            tmp_file.write(text + '\n')
    
    print(f"✅ Đã ghi {len(texts):,} paragraphs vào file tạm")
    
    # Đường dẫn output model
    model_prefix = output_dir / "sp_model"
    model_path = model_prefix.with_suffix('.model')
    vocab_path = model_prefix.with_suffix('.vocab')
    
    print(f"\n🔧 Đang train SentencePiece tokenizer...")
    print(f"   Model type: {model_type}")
    print(f"   Vocab size: {vocab_size:,}")
    print(f"   Character coverage: {character_coverage}")
    print(f"   Input file: {tmp_path}")
    print(f"   Output model: {model_path}")
    
    # Train SentencePiece
    spm.SentencePieceTrainer.train(
        input=str(tmp_path),
        model_prefix=str(model_prefix),
        vocab_size=vocab_size,
        model_type=model_type,
        character_coverage=character_coverage,
        # Thêm các tham số tối ưu cho tiếng Việt
        normalization_rule_name='nmt_nfkc_cf',  # Normalize Unicode
        remove_extra_whitespaces=True,
        # Chỉ thêm các special tokens không có sẵn trong SentencePiece
        # (<unk>, <s>, </s> đã có sẵn, không cần khai báo lại)
        user_defined_symbols=['<pad>', '<mask>'],
        # Shuffle input để training ổn định hơn
        shuffle_input_sentence=True,
        # Số threads (1 = single thread, hoặc bỏ để dùng default)
        num_threads=1,
        # Input sentence size limit (0 = no limit)
        input_sentence_size=0,
        # Tối ưu cho text dài (truyện)
        max_sentence_length=4192,
    )
    
    # Xóa file tạm
    tmp_path.unlink()
    
    print(f"✅ Tokenizer đã được train và lưu tại:")
    print(f"   Model: {model_path}")
    print(f"   Vocab: {vocab_path}")
    
    return model_path


def test_tokenizer(model_path: Path, texts: List[str], num_samples: int = 5):
    """
    Test tokenizer trên một số sample text để verify.
    
    Args:
        model_path: Đường dẫn đến file model
        texts: List các đoạn text để test
        num_samples: Số sample để test
    """
    print(f"\n🧪 Đang test tokenizer trên {num_samples} samples...")
    
    sp = spm.SentencePieceProcessor()
    sp.load(str(model_path))
    
    # Lấy một số sample ngẫu nhiên
    import random
    random.seed(42)
    samples = random.sample(texts, min(num_samples, len(texts)))
    
    for i, text in enumerate(samples, 1):
        print(f"\n--- Sample {i} ---")
        print(f"Original text (first 200 chars):")
        print(f"  {text[:200]}...")
        
        # Encode
        tokens = sp.encode(text, out_type=str)
        token_ids = sp.encode(text, out_type=int)
        
        print(f"\nTokens ({len(tokens)} tokens):")
        print(f"  {tokens[:20]}..." if len(tokens) > 20 else f"  {tokens}")
        
        # Decode để verify
        decoded = sp.decode(tokens)
        print(f"\nDecoded (first 200 chars):")
        print(f"  {decoded[:200]}...")
        
        # Kiểm tra round-trip
        if text.strip() == decoded.strip():
            print("  ✅ Round-trip OK")
        else:
            print("  ⚠️  Round-trip có khác biệt (có thể do normalization)")
        
        # Thống kê
        print(f"\nStats:")
        print(f"  Original length: {len(text)} chars")
        print(f"  Token count: {len(tokens)}")
        print(f"  Compression ratio: {len(text) / len(tokens):.2f} chars/token")


def save_tokenizer_info(
    output_dir: Path,
    vocab_size: int,
    model_type: str,
    character_coverage: float,
    total_texts: int,
    model_path: Path
):
    """
    Lưu metadata về tokenizer vào file JSON.
    
    Args:
        output_dir: Thư mục output
        vocab_size: Vocab size
        model_type: Model type
        character_coverage: Character coverage
        total_texts: Tổng số texts đã train
        model_path: Đường dẫn đến model
    """
    info = {
        "tokenizer_type": "sentencepiece",
        "model_type": model_type,
        "vocab_size": vocab_size,
        "character_coverage": character_coverage,
        "training_samples": total_texts,
        "model_path": str(model_path),
        "vocab_path": str(model_path.with_suffix('.vocab')),
        "notes": [
            "Tokenizer được train từ train split (90% data)",
            "Phù hợp cho model 1-3B parameters",
            "Sử dụng BPE với character coverage cao cho tiếng Việt"
        ]
    }
    
    info_path = Paths.TOKENIZER_INFO_JSON
    save_json(info_path, info)
    
    print(f"\n📄 Đã lưu tokenizer info: {info_path}")


def main():
    args = parse_args()
    
    input_jsonl = Path(args.input_jsonl)
    output_dir = Path(args.output_dir)
    
    if not input_jsonl.exists():
        print(f"❌ File không tồn tại: {input_jsonl}")
        return 1
    
    # Load texts từ train split
    texts = load_train_texts(input_jsonl)
    
    if not texts:
        print("❌ Không có text nào để train tokenizer")
        return 1
    
    # Train tokenizer
    model_path = train_tokenizer(
        texts=texts,
        output_dir=output_dir,
        vocab_size=args.vocab_size,
        model_type=args.model_type,
        character_coverage=args.character_coverage
    )
    
    # Test tokenizer
    test_tokenizer(model_path, texts, num_samples=args.test_samples)
    
    # Lưu metadata
    save_tokenizer_info(
        output_dir=output_dir,
        vocab_size=args.vocab_size,
        model_type=args.model_type,
        character_coverage=args.character_coverage,
        total_texts=len(texts),
        model_path=model_path
    )
    
    print(f"\n✅ Hoàn tất! Tokenizer đã sẵn sàng tại: {output_dir}")
    print(f"\n💡 Để sử dụng tokenizer trong code:")
    print(f"   import sentencepiece as spm")
    print(f"   sp = spm.SentencePieceProcessor()")
    print(f"   sp.load('{model_path}')")
    print(f"   tokens = sp.encode('Văn bản tiếng Việt')")
    
    return 0


if __name__ == "__main__":
    exit(main())


