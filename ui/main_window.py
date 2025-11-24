"""
Main application window
"""
import os
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QListWidget, QListWidgetItem, QLabel,
    QMessageBox, QProgressDialog, QComboBox, QFrame
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont
from datetime import datetime
from models.note import Note
from storage.note_storage import NoteStorage
from services.speech_to_text import SpeechToTextService
from services.summarizer import SummarizerService
from services.audio_player import AudioPlayer
from ui.audio_recorder import AudioRecorderDialog
from ui.note_detail import NoteDetailView
import uuid


class ProcessAudioThread(QThread):
    """Thread for processing audio (transcription and summarization)"""
    finished = pyqtSignal(str, str, str, float)  # transcription, summary, title, duration
    error = pyqtSignal(str)
    
    def __init__(self, audio_path, stt_service, summarizer_service, audio_player, custom_name=""):
        super().__init__()
        self.audio_path = audio_path
        self.stt_service = stt_service
        self.summarizer_service = summarizer_service
        self.audio_player = audio_player
        self.custom_name = custom_name
    
    def run(self):
        """Process the audio file"""
        try:
            # Get duration
            duration = self.audio_player.get_duration(self.audio_path)
            
            # Transcribe
            transcription = self.stt_service.transcribe_audio(self.audio_path)
            
            # Summarize
            summary = self.summarizer_service.summarize(transcription)
            
            # Generate title (use custom name if provided)
            if self.custom_name:
                title = self.custom_name
            else:
                title = self.summarizer_service.generate_title(transcription)
            
            self.finished.emit(transcription, summary, title, duration)
        except Exception as e:
            self.error.emit(str(e))


class MainWindow(QMainWindow):
    """Main application window with notes list"""
    
    def __init__(self, stt_service, summarizer_service):
        super().__init__()
        self.stt_service = stt_service
        self.summarizer_service = summarizer_service
        self.storage = NoteStorage()
        self.audio_player = AudioPlayer()
        
        self.setup_ui()
        self.load_notes()
    
    def setup_ui(self):
        """Setup the user interface"""
        self.setWindowTitle("Audio Notes")
        self.resize(900, 700)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Modern gradient background
        central_widget.setStyleSheet("""
            QWidget {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #667eea,
                    stop:1 #764ba2
                );
            }
        """)
        
        # Main layout
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel("🎵 Audio Notes")
        title.setStyleSheet("""
            font-size: 32px;
            font-weight: bold;
            color: white;
            background: transparent;
        """)
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Add note button
        add_btn = QPushButton("➕ Add Note")
        add_btn.clicked.connect(self.add_note)
        add_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #f093fb,
                    stop:1 #f5576c
                );
                color: white;
                border: none;
                border-radius: 12px;
                padding: 12px 24px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #f5576c,
                    stop:1 #f093fb
                );
            }
            QPushButton:pressed {
                padding: 13px 23px 11px 25px;
            }
        """)
        header_layout.addWidget(add_btn)
        
        layout.addLayout(header_layout)
        
        # Sort controls
        sort_layout = QHBoxLayout()
        sort_label = QLabel("Sort by:")
        sort_label.setStyleSheet("""
            color: white;
            font-size: 14px;
            background: transparent;
        """)
        sort_layout.addWidget(sort_label)
        
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["Newest First", "Oldest First", "Title A-Z", "Title Z-A"])
        self.sort_combo.currentIndexChanged.connect(self.load_notes)
        self.sort_combo.setStyleSheet("""
            QComboBox {
                background: rgba(255, 255, 255, 0.2);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 14px;
                min-width: 150px;
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid white;
                margin-right: 8px;
            }
            QComboBox QAbstractItemView {
                background: #5a67d8;
                color: white;
                border: none;
                selection-background-color: rgba(255, 255, 255, 0.2);
                outline: none;
            }
        """)
        sort_layout.addWidget(self.sort_combo)
        sort_layout.addStretch()
        
        layout.addLayout(sort_layout)
        
        # Notes list with modern styling
        self.notes_list = QListWidget()
        self.notes_list.itemClicked.connect(self.open_note)
        self.notes_list.setStyleSheet("""
            QListWidget {
                background: rgba(255, 255, 255, 0.15);
                border: none;
                border-radius: 16px;
                padding: 10px;
                color: white;
                font-size: 14px;
                outline: none;
            }
            QListWidget::item {
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 10px;
                padding: 15px;
                margin: 5px;
            }
            QListWidget::item:hover {
                background: rgba(255, 255, 255, 0.25);
            }
            QListWidget::item:selected {
                background: rgba(255, 255, 255, 0.3);
                border: 1px solid rgba(255, 255, 255, 0.5);
            }
        """)
        layout.addWidget(self.notes_list)
        
        # Empty state
        self.empty_label = QLabel("No notes yet. Click '➕ Add Note' to create one!")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setStyleSheet("""
            color: rgba(255, 255, 255, 0.7);
            font-size: 18px;
            margin: 50px;
            background: transparent;
        """)
        layout.addWidget(self.empty_label)
        
        central_widget.setLayout(layout)
        
        # Note detail view (hidden initially)
        self.detail_view = NoteDetailView(self)
        self.detail_view.hide()
    
    def load_notes(self):
        """Load all notes from storage with sorting"""
        self.notes_list.clear()
        notes = self.storage.get_all_notes()
        
        if not notes:
            self.notes_list.hide()
            self.empty_label.show()
        else:
            # Sort notes
            sort_option = self.sort_combo.currentIndex() if hasattr(self, 'sort_combo') else 0
            if sort_option == 0:  # Newest First
                notes.sort(key=lambda n: n.created_at, reverse=True)
            elif sort_option == 1:  # Oldest First
                notes.sort(key=lambda n: n.created_at)
            elif sort_option == 2:  # Title A-Z
                notes.sort(key=lambda n: n.title.lower())
            elif sort_option == 3:  # Title Z-A
                notes.sort(key=lambda n: n.title.lower(), reverse=True)
            
            self.notes_list.show()
            self.empty_label.hide()
            
            for note in notes:
                # Format date
                try:
                    from datetime import datetime
                    dt = datetime.strptime(note.created_at, "%Y-%m-%d %H:%M:%S")
                    date_str = dt.strftime("%b %d, %Y")
                except:
                    date_str = note.created_at
                
                item_text = f"🎵  {note.title}\n     📅 {date_str}"
                item = QListWidgetItem(item_text)
                item.setData(Qt.ItemDataRole.UserRole, note.id)
                font = QFont()
                font.setPointSize(13)
                item.setFont(font)
                self.notes_list.addItem(item)
    
    def add_note(self):
        """Open dialog to add a new note"""
        dialog = AudioRecorderDialog(self.storage.audio_dir, self)
        
        if dialog.exec():
            audio_path = dialog.get_audio_path()
            custom_name = dialog.get_note_name()
            if audio_path:
                self.process_audio(audio_path, custom_name)
    
    def process_audio(self, audio_path: str, custom_name: str = ""):
        """Process audio file (transcription and summarization)"""
        # Show progress dialog
        progress = QProgressDialog("Processing audio...", None, 0, 0, self)
        progress.setWindowTitle("Please Wait")
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.show()
        
        # Create and start processing thread
        self.process_thread = ProcessAudioThread(
            audio_path,
            self.stt_service,
            self.summarizer_service,
            self.audio_player,
            custom_name
        )
        self.process_thread.finished.connect(
            lambda t, s, title, d: self.on_processing_finished(audio_path, t, s, title, d, progress)
        )
        self.process_thread.error.connect(
            lambda e: self.on_processing_error(e, progress)
        )
        self.process_thread.start()
    
    def on_processing_finished(self, audio_path, transcription, summary, title, duration, progress):
        """Handle successful processing"""
        progress.close()
        
        # Create new note
        note = Note(
            id=str(uuid.uuid4()),
            title=title,
            audio_path=audio_path,
            transcription=transcription,
            summary=summary,
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            duration=duration
        )
        
        # Save note
        self.storage.save_note(note)
        
        # Reload notes list
        self.load_notes()
        
        QMessageBox.information(self, "Success", "Note created successfully!")
    
    def on_processing_error(self, error, progress):
        """Handle processing error"""
        progress.close()
        QMessageBox.critical(self, "Error", f"Failed to process audio: {error}")
    
    def open_note(self, item):
        """Open note detail view"""
        note_id = item.data(Qt.ItemDataRole.UserRole)
        note = self.storage.get_note_by_id(note_id)
        
        if note:
            # Hide main window content and show detail view
            self.centralWidget().hide()
            self.detail_view.load_note(note)
            self.detail_view.setParent(None)
            self.setCentralWidget(self.detail_view)
            self.detail_view.show()
            
            # Connect back button
            def go_back():
                self.detail_view.hide()
                central_widget = QWidget()
                self.setCentralWidget(central_widget)
                self.setup_ui()
                self.load_notes()
            
            # Disconnect any existing connections
            try:
                self.detail_view.findChild(QPushButton).clicked.disconnect()
            except:
                pass
            
            self.detail_view.findChild(QPushButton).clicked.connect(go_back)
