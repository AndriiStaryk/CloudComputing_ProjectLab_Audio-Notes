"""
Data model for audio notes
"""
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional
import json


@dataclass
class Note:
    """Represents an audio note with transcription and summary"""
    id: str
    title: str
    audio_path: str
    transcription: str
    summary: str
    created_at: str
    duration: float  # in seconds
    
    def to_dict(self) -> dict:
        """Convert note to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Note':
        """Create note from dictionary"""
        return cls(**data)
    
    def to_json(self) -> str:
        """Convert note to JSON string"""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Note':
        """Create note from JSON string"""
        return cls.from_dict(json.loads(json_str))
