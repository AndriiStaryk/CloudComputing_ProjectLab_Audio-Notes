"""
Data storage and persistence for notes
"""
import json
import os
from typing import List, Optional
from models.note import Note


class NoteStorage:
    """Handles saving and loading notes"""
    
    def __init__(self, storage_dir: str = "notes_data"):
        self.storage_dir = storage_dir
        self.notes_file = os.path.join(storage_dir, "notes.json")
        self.audio_dir = os.path.join(storage_dir, "audio")
        
        # Create directories if they don't exist
        os.makedirs(self.storage_dir, exist_ok=True)
        os.makedirs(self.audio_dir, exist_ok=True)
        
        # Initialize notes file if it doesn't exist
        if not os.path.exists(self.notes_file):
            self._save_notes([])
    
    def _save_notes(self, notes: List[Note]) -> None:
        """Save notes to JSON file"""
        with open(self.notes_file, 'w') as f:
            json.dump([note.to_dict() for note in notes], f, indent=2)
    
    def _load_notes(self) -> List[Note]:
        """Load notes from JSON file"""
        try:
            with open(self.notes_file, 'r') as f:
                data = json.load(f)
                return [Note.from_dict(note_dict) for note_dict in data]
        except (json.JSONDecodeError, FileNotFoundError):
            return []
    
    def get_all_notes(self) -> List[Note]:
        """Get all notes"""
        return self._load_notes()
    
    def get_note_by_id(self, note_id: str) -> Optional[Note]:
        """Get a specific note by ID"""
        notes = self._load_notes()
        for note in notes:
            if note.id == note_id:
                return note
        return None
    
    def save_note(self, note: Note) -> None:
        """Save or update a note"""
        notes = self._load_notes()
        
        # Update existing note or add new one
        found = False
        for i, existing_note in enumerate(notes):
            if existing_note.id == note.id:
                notes[i] = note
                found = True
                break
        
        if not found:
            notes.append(note)
        
        self._save_notes(notes)
    
    def delete_note(self, note_id: str) -> bool:
        """Delete a note by ID"""
        notes = self._load_notes()
        initial_length = len(notes)
        notes = [note for note in notes if note.id != note_id]
        
        if len(notes) < initial_length:
            self._save_notes(notes)
            return True
        return False
    
    def get_audio_path(self, filename: str) -> str:
        """Get full path for an audio file"""
        return os.path.join(self.audio_dir, filename)
