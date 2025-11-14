"""
Utility functions for Manus Streamlit applications
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json

def format_timestamp(timestamp: int) -> str:
    """Format Unix timestamp to readable string"""
    return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

def calculate_time_ago(timestamp: int) -> str:
    """Calculate human-readable time ago from timestamp"""
    now = datetime.now()
    then = datetime.fromtimestamp(timestamp)
    diff = now - then
    
    if diff.days > 365:
        return f"{diff.days // 365}y ago"
    elif diff.days > 30:
        return f"{diff.days // 30}mo ago"
    elif diff.days > 0:
        return f"{diff.days}d ago"
    elif diff.seconds > 3600:
        return f"{diff.seconds // 3600}h ago"
    elif diff.seconds > 60:
        return f"{diff.seconds // 60}m ago"
    else:
        return "just now"

def format_file_size(bytes: int) -> str:
    """Format bytes to human-readable file size"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes < 1024.0:
            return f"{bytes:.2f} {unit}"
        bytes /= 1024.0
    return f"{bytes:.2f} PB"

def truncate_string(text: str, max_length: int = 50) -> str:
    """Truncate string to max length with ellipsis"""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."

def extract_file_extension(filename: str) -> str:
    """Extract file extension from filename"""
    if '.' not in filename:
        return ''
    return filename.split('.')[-1].lower()

def is_image_file(filename: str) -> bool:
    """Check if file is an image based on extension"""
    image_extensions = ['png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp', 'svg']
    return extract_file_extension(filename) in image_extensions

def is_document_file(filename: str) -> bool:
    """Check if file is a document based on extension"""
    document_extensions = ['pdf', 'docx', 'doc', 'txt', 'md', 'rtf']
    return extract_file_extension(filename) in document_extensions

def is_code_file(filename: str) -> bool:
    """Check if file is code based on extension"""
    code_extensions = ['py', 'js', 'jsx', 'ts', 'tsx', 'html', 'css', 'json', 'xml', 'yaml', 'yml']
    return extract_file_extension(filename) in code_extensions

def parse_task_metadata(metadata: Dict) -> Dict[str, Any]:
    """Parse and extract useful information from task metadata"""
    return {
        'task_url': metadata.get('task_url', ''),
        'credit_usage': metadata.get('credit_usage', 0),
        'model': metadata.get('model', 'unknown'),
        'profile': metadata.get('profile', 'unknown')
    }

def calculate_expiry_time(created_at: int, hours: int = 48) -> Dict:
    """Calculate expiry time and remaining time"""
    created = datetime.fromtimestamp(created_at)
    expires = created + timedelta(hours=hours)
    now = datetime.now()
    time_left = expires - now
    
    return {
        'expires_at': expires,
        'is_expired': time_left.total_seconds() <= 0,
        'hours_left': max(0, int(time_left.total_seconds() / 3600)),
        'minutes_left': max(0, int((time_left.total_seconds() % 3600) / 60))
    }

def sanitize_filename(filename: str) -> str:
    """Sanitize filename by removing invalid characters"""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename

def create_download_filename(base_name: str, extension: str) -> str:
    """Create a timestamped download filename"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f"{base_name}_{timestamp}.{extension}"

def estimate_reading_time(text: str, words_per_minute: int = 200) -> int:
    """Estimate reading time in minutes for given text"""
    word_count = len(text.split())
    return max(1, word_count // words_per_minute)

def validate_api_key(api_key: str) -> bool:
    """Basic validation for API key format"""
    if not api_key:
        return False
    if len(api_key) < 10:
        return False
    return True

def merge_conversation_messages(messages: List[Dict]) -> str:
    """Merge all conversation messages into a single text"""
    merged = []
    for msg in messages:
        role = msg.get('role', 'unknown').upper()
        content = msg.get('content', '')
        merged.append(f"{role}: {content}")
    return "\n\n".join(merged)

def calculate_statistics(values: List[float]) -> Dict:
    """Calculate basic statistics for a list of values"""
    if not values:
        return {'count': 0, 'sum': 0, 'avg': 0, 'min': 0, 'max': 0}
    
    return {
        'count': len(values),
        'sum': sum(values),
        'avg': sum(values) / len(values),
        'min': min(values),
        'max': max(values)
    }

def group_by_date(items: List[Dict], timestamp_key: str = 'created_at') -> Dict:
    """Group items by date"""
    grouped = {}
    for item in items:
        if timestamp_key in item:
            date = datetime.fromtimestamp(int(item[timestamp_key])).date()
            if date not in grouped:
                grouped[date] = []
            grouped[date].append(item)
    return grouped

def export_to_json(data: Any, pretty: bool = True) -> str:
    """Export data to JSON string"""
    if pretty:
        return json.dumps(data, indent=2, default=str)
    return json.dumps(data, default=str)

def parse_search_query(query: str) -> List[str]:
    """Parse search query into individual terms"""
    # Split by spaces and remove empty strings
    terms = [term.strip().lower() for term in query.split() if term.strip()]
    return terms

def match_search_query(text: str, query_terms: List[str]) -> bool:
    """Check if text matches all search query terms"""
    text_lower = text.lower()
    return all(term in text_lower for term in query_terms)
