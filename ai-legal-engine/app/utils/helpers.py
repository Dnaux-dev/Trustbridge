"""
Helper utilities for TrustBridge
"""
import re
import hashlib
from typing import List
from datetime import datetime


def clean_text(text: str) -> str:
    """Clean and normalize text"""
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove special characters but keep basic punctuation
    text = re.sub(r'[^\w\s.,;:!?()\-]', '', text)
    return text.strip()


def extract_emails(text: str) -> List[str]:
    """Extract email addresses from text"""
    pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    return list(set(re.findall(pattern, text)))


def extract_phone_numbers(text: str) -> List[str]:
    """Extract Nigerian phone numbers"""
    # Nigerian format: +234, 0, etc.
    patterns = [
        r'\+234\d{10}',  # +2348012345678
        r'0\d{10}',      # 08012345678
        r'\d{11}'        # 08012345678
    ]
    numbers = []
    for pattern in patterns:
        numbers.extend(re.findall(pattern, text))
    return list(set(numbers))


def generate_document_id(text: str) -> str:
    """Generate unique ID for document"""
    return hashlib.md5(text.encode()).hexdigest()[:12]


def calculate_readability_score(text: str) -> int:
    """
    Simple readability score (0-100)
    Higher = easier to read
    """
    words = text.split()
    sentences = text.split('.')
    
    if len(sentences) == 0:
        return 0
    
    avg_words_per_sentence = len(words) / max(len(sentences), 1)
    
    # Simple Flesch-like score
    if avg_words_per_sentence < 10:
        return 90  # Very easy
    elif avg_words_per_sentence < 15:
        return 70  # Easy
    elif avg_words_per_sentence < 20:
        return 50  # Medium
    else:
        return 30  # Difficult


def format_timestamp(dt: datetime = None) -> str:
    """Format datetime for responses"""
    if dt is None:
        dt = datetime.utcnow()
    return dt.strftime("%Y-%m-%d %H:%M:%S UTC")


def truncate_text(text: str, max_length: int = 200) -> str:
    """Truncate text with ellipsis"""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."


def extract_company_mentions(text: str) -> List[str]:
    """Extract potential company names (basic heuristic)"""
    # Look for capitalized words followed by Ltd, Inc, Nigeria, etc.
    pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Ltd|Inc|Limited|Nigeria|Plc)\b'
    return list(set(re.findall(pattern, text)))


def is_valid_ndpr_article(article: str) -> bool:
    """Check if article reference is valid NDPR format"""
    # NDPR format: 2.1, 3.4, etc.
    pattern = r'^\d+\.\d+$'
    return bool(re.match(pattern, article))


def parse_ndpr_articles(text: str) -> List[str]:
    """Extract NDPR article references from text"""
    pattern = r'Article\s+(\d+\.\d+)|(\d+\.\d+)'
    matches = re.findall(pattern, text)
    articles = [m[0] or m[1] for m in matches if m[0] or m[1]]
    return list(set(articles))


def pseudonymize_id(user_id: str) -> str:
    """Create pseudonymized user ID"""
    return hashlib.sha256(user_id.encode()).hexdigest()[:16]


def estimate_reading_time(text: str) -> str:
    """Estimate reading time for document"""
    words = len(text.split())
    minutes = max(1, words // 200)  # Average reading speed
    
    if minutes == 1:
        return "1 minute"
    elif minutes < 60:
        return f"{minutes} minutes"
    else:
        hours = minutes // 60
        mins = minutes % 60
        return f"{hours}h {mins}m"