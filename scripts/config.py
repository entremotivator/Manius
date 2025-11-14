"""
Configuration management for Manus Streamlit applications
"""

import os
from typing import Optional
from dataclasses import dataclass

@dataclass
class ManusConfig:
    """Configuration class for Manus API settings"""
    
    # API settings
    base_url: str = "https://api.manus.im"
    api_key: Optional[str] = None
    
    # Agent settings
    default_agent_profile: str = "quality"
    default_timeout_seconds: int = 300
    
    # File settings
    max_file_size_mb: int = 100
    file_expiry_hours: int = 48
    supported_file_types: list = None
    
    # Task settings
    default_task_limit: int = 50
    max_task_limit: int = 100
    
    # UI settings
    page_title: str = "Manus AI Assistant"
    page_icon: str = "🤖"
    layout: str = "wide"
    
    def __post_init__(self):
        """Initialize default values after dataclass initialization"""
        if self.supported_file_types is None:
            self.supported_file_types = [
                'pdf', 'docx', 'doc', 'txt', 'md',
                'csv', 'xlsx', 'xls', 'json',
                'png', 'jpg', 'jpeg', 'gif', 'webp',
                'py', 'js', 'jsx', 'ts', 'tsx', 'html', 'css',
                'zip', 'tar', 'gz'
            ]
        
        # Load from environment variables if available
        if not self.api_key:
            self.api_key = os.getenv('MANUS_API_KEY')
    
    def validate(self) -> bool:
        """Validate configuration settings"""
        if not self.api_key:
            return False
        
        if self.default_timeout_seconds < 60 or self.default_timeout_seconds > 600:
            return False
        
        if self.default_task_limit < 1 or self.default_task_limit > self.max_task_limit:
            return False
        
        return True
    
    def to_dict(self) -> dict:
        """Convert config to dictionary"""
        return {
            'base_url': self.base_url,
            'api_key': '***' if self.api_key else None,
            'default_agent_profile': self.default_agent_profile,
            'default_timeout_seconds': self.default_timeout_seconds,
            'max_file_size_mb': self.max_file_size_mb,
            'file_expiry_hours': self.file_expiry_hours,
            'default_task_limit': self.default_task_limit,
        }

# Default configuration instance
default_config = ManusConfig()

# Agent profile descriptions
AGENT_PROFILES = {
    'quality': {
        'name': 'Quality',
        'description': 'More thorough reasoning and analysis. Best for complex tasks requiring deep thinking.',
        'icon': '🎯',
        'use_cases': [
            'Complex problem solving',
            'Detailed document analysis',
            'Code review and optimization',
            'Research and synthesis'
        ]
    },
    'speed': {
        'name': 'Speed',
        'description': 'Faster responses with efficient processing. Best for quick queries and simple tasks.',
        'icon': '⚡',
        'use_cases': [
            'Quick questions',
            'Simple file processing',
            'Rapid prototyping',
            'Fast iterations'
        ]
    }
}

# File type categories
FILE_TYPE_CATEGORIES = {
    'documents': ['pdf', 'docx', 'doc', 'txt', 'md', 'rtf'],
    'spreadsheets': ['csv', 'xlsx', 'xls'],
    'data': ['json', 'xml', 'yaml', 'yml'],
    'images': ['png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp', 'svg'],
    'code': ['py', 'js', 'jsx', 'ts', 'tsx', 'html', 'css', 'java', 'cpp', 'c', 'go', 'rs'],
    'archives': ['zip', 'tar', 'gz', 'rar', '7z']
}

# Status configurations
TASK_STATUS_CONFIG = {
    'completed': {'emoji': '✅', 'color': '#28a745', 'label': 'Completed'},
    'running': {'emoji': '⏳', 'color': '#ffc107', 'label': 'Running'},
    'pending': {'emoji': '⏸️', 'color': '#17a2b8', 'label': 'Pending'},
    'error': {'emoji': '❌', 'color': '#dc3545', 'label': 'Error'}
}

# Export formats
EXPORT_FORMATS = {
    'json': {'name': 'JSON', 'extension': 'json', 'mime': 'application/json'},
    'csv': {'name': 'CSV', 'extension': 'csv', 'mime': 'text/csv'},
    'markdown': {'name': 'Markdown', 'extension': 'md', 'mime': 'text/markdown'},
    'txt': {'name': 'Plain Text', 'extension': 'txt', 'mime': 'text/plain'}
}
