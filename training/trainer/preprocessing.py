"""
Preprocessing Script - Bước 1: Tiền xử lý dữ liệu truyện tiếng Việt

Mục đích:
    - Đọc dữ liệu raw từ training/dataset/raw/truyenmoiii_output/
    - Làm sạch và chuẩn hóa text theo chiến lược (SAFE/BALANCED/AGGRESSIVE)
    - Filter các chapter quá ngắn hoặc không hợp lệ
    - Chia thành paragraphs hợp lệ (50-2000 ký tự)
    - Lưu vào training/dataset/preprocessed/ (format: txt hoặc JSONL)

Chiến lược làm sạch:
    - SAFE: Chỉ loại bỏ control chars, chuẩn hóa whitespace/line breaks
    - BALANCED: SAFE + loại bỏ HTML tags, một số ký tự đặc biệt (giữ emoji, ký tự trong tên)
    - AGGRESSIVE: BALANCED + loại bỏ emoji, ký tự đặc biệt

Tác giả: AI Agent
Ngày: 2024
"""

import os
import re
import json
import unicodedata
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Literal
from tqdm import tqdm

# Import from local modules
from .utils import setup_encoding
from .config import Paths, PreprocessingConfig, CleaningLevel

# Setup encoding for Windows
setup_encoding()


# ============================================================================
# ENUM VÀ CONSTANTS
# ============================================================================

# Pattern để match số chapter từ tên file
# Ví dụ: "chapter_123.txt" → 123
CHAPTER_NUMBER_PATTERN = re.compile(r'chapter_(\d+)', re.IGNORECASE)

# Pattern để xóa HTML comments (trước khi xử lý tags)
# Ví dụ: "<!-- comment -->" → ""
HTML_COMMENT_PATTERN = re.compile(r'<!--.*?-->', re.DOTALL)

# Pattern để chuyển <br> và <br/> thành newline (trước khi xóa tags)
# Giữ lại cấu trúc paragraph từ HTML
BR_TAG_PATTERN = re.compile(r'<br\s*/?>', re.IGNORECASE)

# Pattern để xóa HTML tags (sau khi đã chuyển <br>)
# Ví dụ: "<strong>text</strong>" → "text"
HTML_TAG_PATTERN = re.compile(r'<[^>]+>')

# Pattern để xóa control characters (giữ lại \n, \t, space)
# \x00-\x08: NULL, SOH, STX, ..., BS
# \x0b-\x0c: VT (vertical tab), FF (form feed)
# \x0e-\x1f: SO, SI, DLE, ..., US
# \x7f-\x9f: DEL, padding, ...
CONTROL_CHARS_PATTERN = re.compile(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x9f]')

# Pattern để normalize whitespace (nhiều spaces/tabs → 1 space)
# LƯU Ý: Chỉ normalize trong dòng, không normalize line breaks
WHITESPACE_PATTERN = re.compile(r'[ \t]+')

# Pattern để normalize line breaks (nhiều newlines → tối đa 2)
# Giữ paragraph structure
MULTIPLE_NEWLINES_PATTERN = re.compile(r'\n{3,}')

# Pattern để chia paragraph (2 newlines liên tiếp)
PARAGRAPH_BREAK_PATTERN = re.compile(r'\n\s*\n')

# Pattern để tách câu (dấu chấm, chấm hỏi, chấm than)
# Dùng để chia paragraph dài
SENTENCE_END_PATTERN = re.compile(r'([.!?]+[\s\n]*)')

# Constants (có thể override bằng config)
# Giới hạn độ dài paragraph
MIN_PARAGRAPH_LENGTH = 50      # Đoạn quá ngắn (< 50 ký tự) → bỏ qua (TRỪ hội thoại)
RELAXED_PARAGRAPH_MIN_LENGTH = 30  # Cho phép giữ đoạn ngắn 30-49 ký tự nếu có câu hoàn chỉnh
MAX_PARAGRAPH_LENGTH = 2000     # Đoạn quá dài (> 2000 ký tự) → chia nhỏ

# Giới hạn độ dài chapter (bytes)
MIN_CHAPTER_LENGTH_BYTES = 500  # Chapter < 500 bytes → filter (TRỪ nếu có > 1 paragraph hợp lệ)
MIN_CHAPTER_RATIO = 0.1         # Chapter < 10% trung bình → filter (TRỪ nếu có > 1 paragraph hợp lệ)

# Độ dài tối thiểu của dòng để xóa (TRỪ hội thoại ngắn)
# Hội thoại ngắn thường có dấu câu: . ! ? ... hoặc dấu ngoặc kép
MIN_LINE_LENGTH = 10
DIALOGUE_PATTERN = re.compile(
    r'^(["\'「『].*[.!?…。！？]|[^.!?]*[.!?…。！？])$'
)


# ============================================================================
# CLASS PREPROCESSOR - XỬ LÝ PREPROCESSING
# ============================================================================

class Preprocessor:
    """
    Class xử lý preprocessing dữ liệu truyện tiếng Việt.
    
    Chức năng chính:
        1. Đọc dữ liệu raw từ thư mục input
        2. Làm sạch text theo chiến lược (SAFE/BALANCED/AGGRESSIVE)
        3. Chia thành paragraphs hợp lệ
        4. Filter chapters không hợp lệ (có exception cho chapter có nhiều paragraphs)
        5. Lưu kết quả vào thư mục output (txt hoặc JSONL)
    
    Attributes:
        raw_dir (Path): Thư mục chứa dữ liệu raw
        output_dir (Path): Thư mục output sau preprocessing
        cleaning_level (CleaningLevel): Mức độ làm sạch
        min_chapter_length (int): Độ dài tối thiểu của chapter (bytes)
        min_ratio (float): Tỷ lệ tối thiểu so với trung bình (0.1 = 10%)
        stats (Dict): Thống kê quá trình preprocessing
    """
    
    def __init__(
        self,
        raw_dir: Optional[Path] = None,
        output_dir: Optional[Path] = None,
        cleaning_level: CleaningLevel = CleaningLevel.BALANCED,
        min_chapter_length: int = MIN_CHAPTER_LENGTH_BYTES,
        min_ratio: float = MIN_CHAPTER_RATIO,
        export_global_jsonl: bool = False,
        config: Optional[PreprocessingConfig] = None
    ):
        """
        Khởi tạo Preprocessor.
        
        Args:
            raw_dir: Đường dẫn thư mục chứa dữ liệu raw (default: Paths.RAW_DIR)
            output_dir: Đường dẫn thư mục output sau preprocessing (default: Paths.PREPROCESSED_DIR)
            cleaning_level: Mức độ làm sạch (SAFE/BALANCED/AGGRESSIVE)
            min_chapter_length: Độ dài tối thiểu của chapter (bytes)
            min_ratio: Tỷ lệ tối thiểu so với trung bình (0.1 = 10%)
            export_global_jsonl: True nếu muốn gom tất cả paragraph vào 1 file JSONL
            config: PreprocessingConfig object (nếu có sẽ override các tham số khác)
        
        Ví dụ:
            >>> preprocessor = Preprocessor(
            ...     cleaning_level=CleaningLevel.BALANCED
            ... )
            >>> # Hoặc dùng config
            >>> config = PreprocessingConfig(cleaning_level=CleaningLevel.AGGRESSIVE)
            >>> preprocessor = Preprocessor(config=config)
        """
        # Sử dụng config nếu được cung cấp
        if config is not None:
            self.raw_dir = config.raw_dir
            self.output_dir = config.output_dir
            self.cleaning_level = config.cleaning_level
            self.min_chapter_length = config.min_chapter_length
            self.min_ratio = config.min_ratio
        else:
            # Sử dụng tham số hoặc defaults từ Paths
            self.raw_dir = Path(raw_dir) if raw_dir is not None else Paths.RAW_DIR
            self.output_dir = Path(output_dir) if output_dir is not None else Paths.PREPROCESSED_DIR
            self.cleaning_level = cleaning_level
            self.min_chapter_length = min_chapter_length
            self.min_ratio = min_ratio
        
        self.export_global_jsonl = export_global_jsonl
        self.global_jsonl_file = Paths.ALL_NOVELS_PREPROCESSED_JSONL if export_global_jsonl else None
        self.global_paragraph_counter = 0
        
        # Tạo thư mục output nếu chưa tồn tại
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Khởi tạo dictionary để lưu thống kê
        self.stats = {
            'total_chapters': 0,
            'processed_chapters': 0,
            'filtered_chapters': 0,
            'total_paragraphs': 0,
            'total_chars': 0,
            'total_bytes': 0,
            'novels': {},
            'filter_reasons': []
        }
    
    # ========================================================================
    # CÁC HÀM TIỆN ÍCH (UTILITY FUNCTIONS)
    # ========================================================================
    
    def extract_chapter_number(self, filename: str) -> int:
        """
        Trích xuất số thứ tự chapter từ tên file.
        
        Args:
            filename: Tên file (ví dụ: "chapter_123.txt")
        
        Returns:
            Số thứ tự chapter (ví dụ: 123), hoặc 0 nếu không tìm thấy
        """
        match = CHAPTER_NUMBER_PATTERN.search(filename)
        if match:
            return int(match.group(1))
        return 0
    
    def is_dialogue_line(self, line: str, allow_longer: bool = False) -> bool:
        """
        Kiểm tra xem dòng có phải là hội thoại ngắn không.
        
        Hội thoại ngắn thường có:
        - Dấu ngoặc kép ở đầu/cuối
        - Dấu câu ở cuối (. ! ? ...)
        - Độ dài ngắn nhưng hợp lệ
        
        Args:
            line: Dòng text cần kiểm tra
            allow_longer: True nếu muốn cho phép đoạn dài hơn (<= MIN_PARAGRAPH_LENGTH)
        
        Returns:
            True nếu là hội thoại ngắn hợp lệ
        """
        stripped = line.strip()
        if not stripped:
            return False
        
        if allow_longer and len(stripped) <= MIN_PARAGRAPH_LENGTH:
            return bool(DIALOGUE_PATTERN.match(stripped))
        
        if len(stripped) <= MIN_LINE_LENGTH:
            return bool(DIALOGUE_PATTERN.match(stripped))
        return False
    
    # ========================================================================
    # CÁC HÀM LÀM SẠCH TEXT (TEXT CLEANING FUNCTIONS)
    # ========================================================================
    
    def remove_html_tags(self, text: str) -> str:
        """
        Loại bỏ HTML/XML tags và comments, nhưng giữ lại cấu trúc paragraph.
        
        QUAN TRỌNG:
            - Chuyển <br> và <br/> thành \n TRƯỚC khi xóa tags
            - Điều này giữ lại cấu trúc paragraph từ HTML
        
        Mức độ: AGGRESSIVE (nhưng giữ cấu trúc)
        
        Args:
            text: Text có thể chứa HTML tags
        
        Returns:
            Text đã loại bỏ HTML tags nhưng giữ cấu trúc paragraph
        """
        # Bước 1: Xóa HTML comments trước
        text = HTML_COMMENT_PATTERN.sub('', text)
        
        # Bước 2: Chuyển <br> và <br/> thành newline (GIỮ CẤU TRÚC)
        # Điều này quan trọng vì nhiều site dùng <br> để xuống dòng
        text = BR_TAG_PATTERN.sub('\n', text)
        
        # Bước 3: Xóa tất cả HTML tags còn lại
        text = HTML_TAG_PATTERN.sub('', text)
        
        return text
    
    def remove_control_characters(self, text: str) -> str:
        """
        Loại bỏ control characters (ký tự điều khiển không in được).
        
        Mức độ: SAFE
        - Giữ lại: \n (newline), \t (tab), space
        - Xóa: Tất cả control characters khác
        
        Args:
            text: Text có thể chứa control characters
        
        Returns:
            Text đã loại bỏ control characters
        """
        return CONTROL_CHARS_PATTERN.sub('', text)
    
    def normalize_whitespace(self, text: str) -> str:
        """
        Chuẩn hóa whitespace (nhiều spaces/tabs → 1 space).
        
        Mức độ: SAFE
        - Nhiều spaces liên tiếp → 1 space
        - Nhiều tabs liên tiếp → 1 space
        - Space + tab → 1 space
        - LƯU Ý: Chỉ normalize trong dòng, không normalize line breaks
        
        Args:
            text: Text có thể chứa nhiều whitespace
        
        Returns:
            Text đã chuẩn hóa whitespace
        """
        # Chỉ normalize spaces/tabs trong dòng, không normalize line breaks
        lines = text.split('\n')
        normalized_lines = [WHITESPACE_PATTERN.sub(' ', line) for line in lines]
        return '\n'.join(normalized_lines)
    
    def normalize_line_breaks(self, text: str) -> str:
        """
        Chuẩn hóa line breaks (xuống dòng).
        
        Mức độ: SAFE
        - \r\n (Windows) → \n
        - \r (Mac old) → \n
        - Nhiều \n liên tiếp (3+) → 2 \n (giữ paragraph break)
        
        Args:
            text: Text có thể chứa nhiều loại line breaks
        
        Returns:
            Text đã chuẩn hóa line breaks
        """
        # Normalize Windows line breaks (\r\n → \n)
        text = text.replace('\r\n', '\n')
        
        # Normalize Mac old line breaks (\r → \n)
        text = text.replace('\r', '\n')
        
        # Nhiều newlines liên tiếp (3+) → tối đa 2 (giữ paragraph break)
        text = MULTIPLE_NEWLINES_PATTERN.sub('\n\n', text)
        
        return text
    
    def remove_special_characters(self, text: str) -> str:
        """
        Loại bỏ ký tự đặc biệt không cần thiết DỰA TRÊN UNICODE CATEGORIES.
        
        CẢI THIỆN: Dùng Unicode general categories thay vì regex thủ công.
        - Giữ lại: Letters (L), Numbers (N), Punctuation (P), Symbols (S) hợp lệ
        - Xóa: Control (C), Format (Cf), Private Use (Co), Surrogate (Cs)
        
        Mức độ: MODERATE (BALANCED) hoặc AGGRESSIVE (tùy cleaning_level)
        
        Args:
            text: Text cần làm sạch
        
        Returns:
            Text đã loại bỏ ký tự đặc biệt (tùy cleaning_level)
        """
        if self.cleaning_level == CleaningLevel.SAFE:
            # SAFE: Không xóa gì cả, chỉ giữ lại
            return text
        
        result = []
        for char in text:
            # Lấy Unicode category
            category = unicodedata.category(char)
            char_code = ord(char)
            
            # Giữ lại:
            # - Letters (L): Tất cả chữ cái (bao gồm tiếng Việt)
            # - Numbers (N): Tất cả số
            # - Punctuation (P): Dấu câu
            # - Symbols (S): Một số symbols hợp lệ
            # - Whitespace: Space, \n, \t
            if category.startswith('L'):  # Letters
                result.append(char)
            elif category.startswith('N'):  # Numbers
                result.append(char)
            elif category.startswith('P'):  # Punctuation
                result.append(char)
            elif category.startswith('S'):  # Symbols
                # Chỉ giữ lại một số symbols hợp lệ (không phải emoji)
                # Emoji thường là So (Symbol, other) với code point > 0x1F000
                if self.cleaning_level == CleaningLevel.BALANCED:
                    # BALANCED: Giữ emoji và symbols (code point < 0x1F000 là symbols thông thường)
                    if char_code < 0x1F000:
                        result.append(char)
                    else:
                        # Emoji (code point >= 0x1F000) - giữ lại trong BALANCED
                        result.append(char)
                else:
                    # AGGRESSIVE: Chỉ giữ symbols thông thường, xóa emoji
                    if char_code < 0x1F000:
                        result.append(char)
                    # else: xóa emoji
            elif char in [' ', '\n', '\t']:  # Whitespace
                result.append(char)
            # else: Xóa (Control, Format, Private Use, Surrogate, etc.)
        
        return ''.join(result)
    
    def trim_whitespace(self, text: str) -> str:
        """
        Xóa whitespace ở đầu/cuối mỗi dòng và toàn bộ text.
        
        Mức độ: SAFE
        - Xóa space ở đầu/cuối mỗi dòng
        - Xóa space ở đầu/cuối toàn bộ text
        - Giữ lại line breaks (\n)
        
        Args:
            text: Text có thể có whitespace thừa
        
        Returns:
            Text đã trim whitespace
        """
        # Trim từng dòng
        lines = [line.strip() for line in text.split('\n')]
        text = '\n'.join(lines)
        
        # Trim toàn bộ text
        text = text.strip()
        
        return text
    
    def remove_short_lines(self, text: str, min_length: int = MIN_LINE_LENGTH) -> str:
        """
        Xóa các dòng quá ngắn, NHƯNG GIỮ LẠI HỘI THOẠI NGẮN.
        
        CẢI THIỆN: Không xóa hội thoại ngắn hợp lệ như "Được.", "Không.", "A!"
        
        Mức độ: MODERATE
        - Dòng có < min_length ký tự → Xóa (TRỪ hội thoại)
        - TRỪ: Dòng chỉ có số (có thể là số chương) → Giữ lại
        - TRỪ: Dòng là hội thoại ngắn → Giữ lại
        
        Args:
            text: Text có thể chứa dòng ngắn
            min_length: Độ dài tối thiểu của dòng (mặc định: 10)
        
        Returns:
            Text đã loại bỏ dòng ngắn (nhưng giữ hội thoại)
        """
        lines = text.split('\n')
        filtered_lines = []
        
        for line in lines:
            stripped = line.strip()
            
            # Giữ lại nếu đủ dài
            if len(stripped) >= min_length:
                filtered_lines.append(line)
            # Giữ lại nếu là số (có thể là số chương)
            elif stripped.isdigit():
                filtered_lines.append(line)
            # Giữ lại nếu là hội thoại ngắn (CẢI THIỆN)
            elif self.is_dialogue_line(stripped):
                filtered_lines.append(line)
            # else: bỏ qua dòng ngắn
        
        return '\n'.join(filtered_lines)
    
    def clean_text(self, text: str) -> str:
        """
        Hàm tổng hợp: Làm sạch text theo chiến lược (SAFE/BALANCED/AGGRESSIVE).
        
        QUAN TRỌNG: Thứ tự xử lý được sắp xếp lại để tránh conflict:
            1. Loại bỏ HTML tags (chuyển <br> thành \n trước)
            2. Loại bỏ control characters
            3. Chuẩn hóa line breaks (TRƯỚC normalize whitespace)
            4. Chuẩn hóa whitespace (SAU normalize line breaks)
            5. Loại bỏ ký tự đặc biệt (tùy cleaning_level)
            6. Trim whitespace
            7. Xóa dòng quá ngắn (nhưng giữ hội thoại)
        
        Args:
            text: Text raw cần làm sạch
        
        Returns:
            Text đã được làm sạch
        """
        # Bước 1: Loại bỏ HTML tags (chuyển <br> thành \n trước) - AGGRESSIVE
        if self.cleaning_level != CleaningLevel.SAFE:
            text = self.remove_html_tags(text)
        
        # Bước 2: Loại bỏ control characters - SAFE
        text = self.remove_control_characters(text)
        
        # Bước 3: Chuẩn hóa line breaks TRƯỚC normalize whitespace - SAFE
        # Quan trọng: Phải normalize line breaks trước để giữ cấu trúc paragraph
        text = self.normalize_line_breaks(text)
        
        # Bước 4: Chuẩn hóa whitespace SAU normalize line breaks - SAFE
        text = self.normalize_whitespace(text)
        
        # Bước 5: Loại bỏ ký tự đặc biệt (tùy cleaning_level) - MODERATE/AGGRESSIVE
        if self.cleaning_level != CleaningLevel.SAFE:
            text = self.remove_special_characters(text)
        
        # Bước 6: Trim whitespace - SAFE
        text = self.trim_whitespace(text)
        
        # Bước 7: Xóa dòng quá ngắn (nhưng giữ hội thoại) - MODERATE
        if self.cleaning_level != CleaningLevel.SAFE:
            text = self.remove_short_lines(text, min_length=MIN_LINE_LENGTH)
        
        return text
    
    # ========================================================================
    # CÁC HÀM CHIA ĐOẠN VĂN (PARAGRAPH SEGMENTATION)
    # ========================================================================
    
    def split_into_paragraphs(self, text: str) -> List[str]:
        """
        Chia text thành các paragraphs (đoạn văn).
        
        Quy tắc:
            - Tách theo pattern: \n\s*\n (2 newlines liên tiếp)
            - Mỗi paragraph là một đoạn văn độc lập
        
        Args:
            text: Text cần chia thành paragraphs
        
        Returns:
            List các paragraphs (đã strip)
        """
        # Chia theo paragraph break (2 newlines liên tiếp)
        paragraphs = PARAGRAPH_BREAK_PATTERN.split(text)
        
        # Strip và loại bỏ paragraph rỗng
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        
        return paragraphs
    
    def split_long_paragraph(self, paragraph: str, max_length: int = MAX_PARAGRAPH_LENGTH) -> List[str]:
        """
        Chia paragraph dài thành nhiều chunks nhỏ hơn.
        
        CẢI THIỆN: Có fallback theo độ dài nếu không tìm thấy dấu câu.
        
        Quy tắc:
            - Nếu paragraph <= max_length → giữ nguyên
            - Nếu paragraph > max_length → chia thành chunks
            - Ưu tiên: Chia theo câu (dấu chấm, chấm hỏi, chấm than)
            - Fallback: Chia theo độ dài cố định nếu không có dấu câu
        
        Args:
            paragraph: Paragraph cần chia (nếu quá dài)
            max_length: Độ dài tối đa của mỗi chunk (mặc định: 2000)
        
        Returns:
            List các chunks (có thể chỉ có 1 phần tử nếu không cần chia)
        """
        # Nếu không quá dài thì giữ nguyên
        if len(paragraph) <= max_length:
            return [paragraph]
        
        chunks = []
        current_chunk = ""
        
        # Thử chia theo câu (dấu chấm, chấm hỏi, chấm than)
        sentences = SENTENCE_END_PATTERN.split(paragraph)
        
        # Nếu không tìm thấy dấu câu (chỉ có 1 phần tử), dùng fallback
        if len(sentences) <= 1:
            # Fallback: Chia theo độ dài cố định
            for i in range(0, len(paragraph), max_length):
                chunk = paragraph[i:i + max_length]
                # Tìm vị trí space gần nhất để không cắt giữa từ
                if i + max_length < len(paragraph):
                    last_space = chunk.rfind(' ')
                    if last_space > max_length * 0.8:  # Nếu space không quá xa
                        chunk = chunk[:last_space]
                chunks.append(chunk.strip())
            return [c for c in chunks if c]  # Loại bỏ chunk rỗng
        
        # Ghép lại sentences thành chunks
        for i in range(0, len(sentences), 2):
            # Lấy sentence và dấu câu đi kèm
            sentence = sentences[i] + (sentences[i+1] if i+1 < len(sentences) else '')
            
            # Nếu thêm sentence này vẫn <= max_length thì thêm vào chunk hiện tại
            if len(current_chunk) + len(sentence) <= max_length:
                current_chunk += sentence
            else:
                # Nếu chunk hiện tại đã có nội dung thì lưu lại
                if current_chunk:
                    chunks.append(current_chunk.strip())
                # Bắt đầu chunk mới
                current_chunk = sentence
        
        # Lưu chunk cuối cùng
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def filter_valid_paragraphs(self, paragraphs: List[str]) -> List[str]:
        """
        Lọc các paragraphs hợp lệ (độ dài 50-2000 ký tự).
        
        Quy tắc:
            - Quá ngắn (< 50 ký tự): Bỏ qua (TRỪ hội thoại ngắn)
            - Hợp lệ (50-2000 ký tự): Giữ lại
            - Quá dài (> 2000 ký tự): Chia nhỏ
        
        Args:
            paragraphs: List các paragraphs cần filter
        
        Returns:
            List các paragraphs hợp lệ (đã chia nhỏ nếu cần)
        """
        valid_paragraphs = []
        
        for para in paragraphs:
            length = len(para)
            
            # Quá ngắn → bỏ qua (TRỪ hội thoại ngắn)
            if length < MIN_PARAGRAPH_LENGTH:
                # Giữ hội thoại (cho phép dài tới MIN_PARAGRAPH_LENGTH)
                if self.is_dialogue_line(para, allow_longer=True):
                    valid_paragraphs.append(para)
                    continue
                
                # Cho phép giữ đoạn 30-49 ký tự nếu có dấu câu kết thúc
                if length >= RELAXED_PARAGRAPH_MIN_LENGTH:
                    if any(punct in para for punct in '.!?…。！？'):
                        valid_paragraphs.append(para)
                        continue
                # else: bỏ qua đoạn quá ngắn
                continue
            
            # Hợp lệ → giữ lại
            elif length <= MAX_PARAGRAPH_LENGTH:
                valid_paragraphs.append(para)
            
            # Quá dài → chia nhỏ
            else:
                chunks = self.split_long_paragraph(para, max_length=MAX_PARAGRAPH_LENGTH)
                valid_paragraphs.extend(chunks)
        
        return valid_paragraphs
    
    # ========================================================================
    # CÁC HÀM FILTER CHAPTER
    # ========================================================================
    
    def should_filter_chapter(
        self,
        content: str,
        paragraphs: List[str],
        novel_avg_size: Optional[float] = None
    ) -> Tuple[bool, str]:
        """
        Quyết định có nên filter chapter này không.
        
        CẢI THIỆN: Nếu chapter có > 1 paragraph hợp lệ → KHÔNG FILTER
        (Tránh filter oan chapter ngắn nhưng có nhiều paragraphs hợp lệ)
        
        Quy tắc:
            1. Nếu có > 1 paragraph hợp lệ → KHÔNG FILTER
            2. Độ dài < min_chapter_length (bytes) → Filter
            3. Độ dài < min_ratio * trung bình → Filter
        
        Args:
            content: Nội dung chapter (đã làm sạch)
            paragraphs: List các paragraphs hợp lệ
            novel_avg_size: Độ dài trung bình của truyện (bytes), None nếu chưa tính
        
        Returns:
            Tuple (should_filter, reason):
                - should_filter: True nếu nên filter, False nếu giữ lại
                - reason: Lý do filter (nếu có)
        """
        # CẢI THIỆN: Nếu có > 1 paragraph hợp lệ → KHÔNG FILTER
        if len(paragraphs) > 1:
            return False, ""
        
        content_bytes = len(content.encode('utf-8'))
        
        # Check 1: Độ dài tối thiểu tuyệt đối
        if content_bytes < self.min_chapter_length:
            return True, f"Độ dài < {self.min_chapter_length} bytes và chỉ có {len(paragraphs)} paragraph"
        
        # Check 2: Độ dài so với trung bình (nếu có)
        if novel_avg_size and novel_avg_size > 0:
            min_size = novel_avg_size * self.min_ratio
            if content_bytes < min_size:
                return True, f"Độ dài < {self.min_ratio*100}% trung bình ({min_size:.0f} bytes) và chỉ có {len(paragraphs)} paragraph"
        
        return False, ""
    
    # ========================================================================
    # CÁC HÀM XỬ LÝ NOVEL
    # ========================================================================
    
    def process_novel(self, novel_dir: Path) -> Optional[Dict]:
        """
        Xử lý một truyện: đọc, làm sạch, filter, chia paragraphs.
        
        Quy trình:
            1. Tìm tất cả file chapter
            2. Tính độ dài trung bình (để filter)
            3. Xử lý từng chapter:
                - Đọc file
                - Làm sạch text
                - Chia thành paragraphs
                - Filter paragraphs hợp lệ
                - Check filter chapter (có exception cho nhiều paragraphs)
            4. Thu thập thống kê
        
        Args:
            novel_dir: Đường dẫn thư mục chứa chapters của truyện
        
        Returns:
            Dict chứa stats và paragraphs, hoặc None nếu lỗi
        """
        novel_name = novel_dir.name
        print(f"\n📖 Xử lý: {novel_name}")
        
        # Tìm tất cả file chapter (pattern: chapter_*.txt)
        chapter_files = list(novel_dir.glob("chapter_*.txt"))
        
        # Sắp xếp theo số thứ tự chapter
        chapter_files.sort(key=lambda x: self.extract_chapter_number(x.name))
        
        if not chapter_files:
            print(f"  ⚠️  Không tìm thấy file chapter nào")
            return None
        
        print(f"  📄 Tìm thấy {len(chapter_files)} chapters")
        
        # Tính độ dài trung bình của chapters (để filter)
        chapter_sizes = []
        for chapter_file in chapter_files:
            try:
                size = chapter_file.stat().st_size
                chapter_sizes.append(size)
            except Exception as e:
                print(f"  ⚠️  Không đọc được size của {chapter_file.name}: {e}")
        
        avg_size = sum(chapter_sizes) / len(chapter_sizes) if chapter_sizes else 0
        print(f"  📊 Độ dài trung bình: {avg_size / 1024:.2f} KB")
        
        # Xử lý từng chapter
        processed_paragraphs = []
        processed_chapters = 0
        filtered_chapters = 0
        
        for chapter_file in tqdm(chapter_files, desc=f"  Đang xử lý", leave=False):
            try:
                chapter_index = self.extract_chapter_number(chapter_file.name)
                
                # Đọc file với encoding UTF-8
                with open(chapter_file, 'r', encoding='utf-8') as f:
                    raw_content = f.read()
                
                # Làm sạch text
                cleaned_content = self.clean_text(raw_content)
                
                # Chia thành paragraphs
                paragraphs = self.split_into_paragraphs(cleaned_content)
                
                # Filter paragraphs hợp lệ
                valid_paragraphs = self.filter_valid_paragraphs(paragraphs)
                
                # Check filter chapter (CẢI THIỆN: có exception cho nhiều paragraphs)
                should_filter, reason = self.should_filter_chapter(cleaned_content, valid_paragraphs, avg_size)
                if should_filter:
                    filtered_chapters += 1
                    reason_text = reason or "Không rõ lý do"
                    print(f"  🗑️  Bỏ {chapter_file.name}: {reason_text}")
                    self.stats['filter_reasons'].append({
                        'novel_name': novel_name,
                        'chapter_file': chapter_file.name,
                        'chapter_index': chapter_index,
                        'reason': reason_text
                    })
                    continue
                
                # Thêm vào list
                processed_paragraphs.extend(valid_paragraphs)
                processed_chapters += 1
                
            except Exception as e:
                print(f"  ❌ Lỗi khi xử lý {chapter_file.name}: {e}")
                continue
        
        # Thống kê
        total_chars = sum(len(p) for p in processed_paragraphs)
        total_bytes = sum(len(p.encode('utf-8')) for p in processed_paragraphs)
        
        novel_stats = {
            'novel_name': novel_name,
            'total_chapters': len(chapter_files),
            'processed_chapters': processed_chapters,
            'filtered_chapters': filtered_chapters,
            'total_paragraphs': len(processed_paragraphs),
            'total_chars': total_chars,
            'total_bytes': total_bytes,
            'avg_chars_per_chapter': total_chars / processed_chapters if processed_chapters > 0 else 0,
            'avg_chars_per_paragraph': total_chars / len(processed_paragraphs) if processed_paragraphs else 0
        }
        
        print(f"  ✅ Đã xử lý: {processed_chapters}/{len(chapter_files)} chapters")
        print(f"  🗑️  Đã filter: {filtered_chapters} chapters")
        print(f"  📝 Tổng paragraphs: {len(processed_paragraphs):,}")
        print(f"  📊 Tổng ký tự: {total_chars:,}")
        
        return {
            'stats': novel_stats,
            'paragraphs': processed_paragraphs
        }
    
    # ========================================================================
    # CÁC HÀM LƯU KẾT QUẢ
    # ========================================================================
    
    def save_preprocessed(
        self,
        novel_data: Dict,
        format: Literal['combined', 'jsonl'] = 'combined'
    ) -> None:
        """
        Lưu dữ liệu đã xử lý vào file.
        
        Format:
            - 'combined': 1 file .txt lớn cho mỗi truyện (khuyến nghị)
            - 'jsonl': JSONL format chuẩn LLM (mỗi dòng là 1 JSON object)
        
        Args:
            novel_data: Dict chứa stats và paragraphs
            format: Format output ('combined' hoặc 'jsonl')
        """
        if not novel_data:
            return
        
        novel_name = novel_data['stats']['novel_name']
        paragraphs = novel_data['paragraphs']
        
        if format == 'combined':
            # Lưu thành 1 file .txt lớn
            output_file = self.output_dir / f"{novel_name}_preprocessed.txt"
            
            with open(output_file, 'w', encoding='utf-8') as f:
                # Ghi từng paragraph, cách nhau bởi 2 newlines
                for para in paragraphs:
                    f.write(para)
                    f.write('\n\n')  # Separator giữa các paragraph
            
            print(f"  💾 Đã lưu: {output_file}")
        
        elif format == 'jsonl':
            # Lưu thành JSONL format (chuẩn LLM)
            output_file = self.output_dir / f"{novel_name}_preprocessed.jsonl"
            
            with open(output_file, 'w', encoding='utf-8') as f:
                for i, para in enumerate(paragraphs):
                    # Mỗi dòng là 1 JSON object
                    json_obj = {
                        "text": para,
                        "novel_name": novel_name,
                        "paragraph_index": i
                    }
                    f.write(json.dumps(json_obj, ensure_ascii=False) + '\n')
            
            print(f"  💾 Đã lưu: {output_file} (JSONL format)")
        
        # Lưu metadata
        metadata_file = self.output_dir / f"{novel_name}_metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(novel_data['stats'], f, ensure_ascii=False, indent=2)

    def append_to_global_jsonl(self, novel_data: Dict) -> None:
        """
        Bổ sung paragraphs của một truyện vào file JSONL tổng (nếu bật).
        
        Args:
            novel_data: Dict chứa thông tin truyện sau preprocessing
        """
        if not (self.export_global_jsonl and novel_data):
            return
        
        paragraphs = novel_data['paragraphs']
        novel_name = novel_data['stats']['novel_name']
        
        with open(self.global_jsonl_file, 'a', encoding='utf-8') as f:
            for idx, para in enumerate(paragraphs):
                json_obj = {
                    "text": para,
                    "novel_name": novel_name,
                    "paragraph_index": idx,
                    "global_paragraph_index": self.global_paragraph_counter
                }
                f.write(json.dumps(json_obj, ensure_ascii=False) + '\n')
                self.global_paragraph_counter += 1
    
    def save_summary(self) -> None:
        """Lưu file thống kê tổng của toàn bộ quá trình preprocessing."""
        summary_file = Paths.PREPROCESSING_SUMMARY_JSON
        
        summary = {
            'preprocessing_config': {
                'cleaning_level': self.cleaning_level.value,
                'min_chapter_length': self.min_chapter_length,
                'min_ratio': self.min_ratio,
                'min_paragraph_length': MIN_PARAGRAPH_LENGTH,
                'relaxed_paragraph_length': RELAXED_PARAGRAPH_MIN_LENGTH,
                'max_paragraph_length': MAX_PARAGRAPH_LENGTH,
                'export_global_jsonl': self.export_global_jsonl,
                'global_jsonl_file': str(self.global_jsonl_file) if self.export_global_jsonl else None
            },
            'statistics': {
                'total_novels': len(self.stats['novels']),
                'total_chapters': self.stats['total_chapters'],
                'processed_chapters': self.stats['processed_chapters'],
                'filtered_chapters': self.stats['filtered_chapters'],
                'total_paragraphs': self.stats['total_paragraphs'],
                'total_chars': self.stats['total_chars'],
                'total_bytes': self.stats['total_bytes'],
                'global_paragraphs': self.global_paragraph_counter if self.export_global_jsonl else 0
            },
            'novels': self.stats['novels'],
            'filter_reasons': self.stats['filter_reasons']
        }
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 Đã lưu thống kê: {summary_file}")
    
    def print_summary(self) -> None:
        """In thống kê tổng ra console."""
        print("\n" + "=" * 80)
        print("📊 THỐNG KÊ TỔNG")
        print("=" * 80)
        print(f"📚 Tổng số truyện: {len(self.stats['novels'])}")
        print(f"📄 Tổng số chapters: {self.stats['total_chapters']:,}")
        print(f"✅ Đã xử lý: {self.stats['processed_chapters']:,}")
        print(f"🗑️  Đã filter: {self.stats['filtered_chapters']:,}")
        print(f"📝 Tổng paragraphs: {self.stats['total_paragraphs']:,}")
        print(f"📊 Tổng ký tự: {self.stats['total_chars']:,}")
        print(f"💾 Tổng dung lượng: {self.stats['total_bytes'] / (1024*1024):.2f} MB")
        if self.stats['total_paragraphs'] > 0:
            print(f"📈 Trung bình: {self.stats['total_chars'] / self.stats['total_paragraphs']:.0f} ký tự/paragraph")
        if self.export_global_jsonl:
            print(f"🧾 Global JSONL: {self.global_paragraph_counter:,} paragraphs → {self.global_jsonl_file}")
        print("=" * 80)
    
    # ========================================================================
    # HÀM CHÍNH - CHẠY PREPROCESSING
    # ========================================================================
    
    def run(self, format: Literal['combined', 'jsonl'] = 'combined') -> None:
        """
        Hàm chính: Chạy preprocessing cho tất cả truyện.
        
        Args:
            format: Format output ('combined' hoặc 'jsonl')
        """
        print("=" * 80)
        print("🚀 BẮT ĐẦU PREPROCESSING")
        print("=" * 80)
        print(f"📁 Input: {self.raw_dir}")
        print(f"📁 Output: {self.output_dir}")
        print(f"⚙️  Cleaning Level: {self.cleaning_level.value.upper()}")
        print(f"⚙️  Format: {format}")
        print(f"🔧 Min chapter length: {self.min_chapter_length} bytes")
        print(f"🔧 Min ratio: {self.min_ratio * 100}% trung bình")
        if self.export_global_jsonl:
            print(f"🧾 Global JSONL: {self.global_jsonl_file}")
        print("=" * 80)
        
        # Chuẩn bị file global JSONL (nếu bật)
        if self.export_global_jsonl:
            try:
                if self.global_jsonl_file.exists():
                    self.global_jsonl_file.unlink()
            except Exception as exc:
                print(f"⚠️  Không xóa được file cũ {self.global_jsonl_file}: {exc}")
            self.global_paragraph_counter = 0
        
        # Tìm tất cả folder truyện
        novel_dirs = [d for d in self.raw_dir.iterdir() if d.is_dir()]
        
        if not novel_dirs:
            print(f"❌ Không tìm thấy folder truyện nào trong {self.raw_dir}")
            return
        
        print(f"\n📚 Tìm thấy {len(novel_dirs)} truyện\n")
        
        # Xử lý từng truyện
        for novel_dir in novel_dirs:
            novel_data = self.process_novel(novel_dir)
            
            if novel_data:
                # Lưu dữ liệu
                self.save_preprocessed(novel_data, format=format)
                # Ghi thêm vào file JSONL tổng nếu cần
                self.append_to_global_jsonl(novel_data)
                
                # Cập nhật thống kê
                stats = novel_data['stats']
                self.stats['total_chapters'] += stats['total_chapters']
                self.stats['processed_chapters'] += stats['processed_chapters']
                self.stats['filtered_chapters'] += stats['filtered_chapters']
                self.stats['total_paragraphs'] += stats['total_paragraphs']
                self.stats['total_chars'] += stats['total_chars']
                self.stats['total_bytes'] += stats['total_bytes']
                self.stats['novels'][stats['novel_name']] = stats
        
        # Lưu thống kê tổng
        self.save_summary()
        
        # In kết quả
        self.print_summary()


# ============================================================================
# HÀM MAIN - ENTRY POINT
# ============================================================================

def main():
    """
    Hàm main: Parse arguments và chạy preprocessing.
    
    Arguments:
        --raw-dir: Thư mục chứa dữ liệu raw
        --output-dir: Thư mục output
        --cleaning-level: Mức độ làm sạch (safe/balanced/aggressive)
        --format: Format output (combined/jsonl)
        --min-length: Độ dài tối thiểu chapter (bytes)
        --min-ratio: Tỷ lệ tối thiểu so với trung bình
    """
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Preprocessing dữ liệu truyện tiếng Việt',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ví dụ:
  # Chạy với default settings (BALANCED)
  python preprocessing.py
  
  # Chọn cleaning level
  python preprocessing.py --cleaning-level safe
  python preprocessing.py --cleaning-level balanced
  python preprocessing.py --cleaning-level aggressive
  
  # Xuất JSONL format
  python preprocessing.py --format jsonl
  
  # Tùy chỉnh filter
  python preprocessing.py --min-length 500 --min-ratio 0.1
        """
    )
    
    parser.add_argument(
        '--raw-dir',
        type=str,
        default='training/dataset/raw/truyenmoiii_output',
        help='Thư mục chứa dữ liệu raw'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default='training/dataset/preprocessed',
        help='Thư mục output sau preprocessing'
    )
    
    parser.add_argument(
        '--cleaning-level',
        type=str,
        choices=['safe', 'balanced', 'aggressive'],
        default='balanced',
        help='Mức độ làm sạch: safe (chỉ normalize), balanced (giữ emoji), aggressive (xóa emoji)'
    )
    
    parser.add_argument(
        '--format',
        type=str,
        choices=['combined', 'jsonl'],
        default='combined',
        help='Format output: combined (.txt) hoặc jsonl (.jsonl)'
    )
    
    parser.add_argument(
        '--min-length',
        type=int,
        default=MIN_CHAPTER_LENGTH_BYTES,
        help=f'Độ dài tối thiểu của chapter (bytes) (mặc định: {MIN_CHAPTER_LENGTH_BYTES})'
    )
    
    parser.add_argument(
        '--min-ratio',
        type=float,
        default=MIN_CHAPTER_RATIO,
        help=f'Tỷ lệ tối thiểu so với trung bình (0.1 = 10%%) (mặc định: {MIN_CHAPTER_RATIO})'
    )
    
    parser.add_argument(
        '--global-jsonl',
        action='store_true',
        help='Xuất thêm file all_novels_preprocessed.jsonl (gom toàn bộ đoạn văn)'
    )
    
    args = parser.parse_args()
    
    # Chuyển đổi cleaning level string thành Enum
    cleaning_level_map = {
        'safe': CleaningLevel.SAFE,
        'balanced': CleaningLevel.BALANCED,
        'aggressive': CleaningLevel.AGGRESSIVE
    }
    cleaning_level = cleaning_level_map[args.cleaning_level]
    
    # Tạo preprocessor
    preprocessor = Preprocessor(
        raw_dir=args.raw_dir,
        output_dir=args.output_dir,
        cleaning_level=cleaning_level,
        min_chapter_length=args.min_length,
        min_ratio=args.min_ratio,
        export_global_jsonl=args.global_jsonl
    )
    
    # Chạy preprocessing
    preprocessor.run(format=args.format)


if __name__ == "__main__":
    main()
