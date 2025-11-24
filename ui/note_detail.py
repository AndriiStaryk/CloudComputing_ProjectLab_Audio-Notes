"""
Note detail view with audio player and collapsible transcription
"""
import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QTextEdit, QSlider, QGroupBox, QScrollArea, QFrame, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont
from services.audio_player import AudioPlayer


class CollapsibleSection(QWidget):
    """A collapsible section widget"""
    
    def __init__(self, title="", parent=None):
        super().__init__(parent)
        self.is_collapsed = True
        self.animation = None
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Toggle button
        self.toggle_btn = QPushButton(f"▼ {title}")
        self.toggle_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.2);
                color: white;
                border: none;
                border-radius: 10px;
                padding: 12px;
                font-size: 15px;
                font-weight: bold;
                text-align: left;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.3);
            }
        """)
        self.toggle_btn.clicked.connect(self.toggle)
        layout.addWidget(self.toggle_btn)
        
        # Content area
        self.content_area = QFrame()
        self.content_area.setMaximumHeight(0)
        self.content_area.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.1);
                border: none;
                border-radius: 10px;
                margin-top: 5px;
            }
        """)
        
        self.content_layout = QVBoxLayout(self.content_area)
        layout.addWidget(self.content_area)
        
    def set_content(self, widget):
        """Set the content widget"""
        self.content_layout.addWidget(widget)
        
    def toggle(self):
        """Toggle collapse/expand"""
        if self.animation:
            self.animation.stop()
            
        self.is_collapsed = not self.is_collapsed
        
        if self.is_collapsed:
            self.toggle_btn.setText(self.toggle_btn.text().replace("▲", "▼"))
            target_height = 0
        else:
            self.toggle_btn.setText(self.toggle_btn.text().replace("▼", "▲"))
            # Calculate content height
            target_height = self.content_layout.sizeHint().height() + 20
        
        self.animation = QPropertyAnimation(self.content_area, b"maximumHeight")
        self.animation.setDuration(300)
        self.animation.setStartValue(self.content_area.maximumHeight())
        self.animation.setEndValue(target_height)
        self.animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.animation.start()


class NoteDetailView(QWidget):
    """View for displaying note details with audio player"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.note = None
        self.audio_player = AudioPlayer()
        self.parent_window = parent
        self.setup_ui()
        
        # Timer for updating playback position
        self.playback_timer = QTimer()
        self.playback_timer.timeout.connect(self.update_playback)
        self.playback_timer.setInterval(100)  # Update every 100ms
        self.playback_start_time = 0
        self.playback_position = 0
    
    def setup_ui(self):
        """Setup the user interface"""
        # Gradient background
        self.setStyleSheet("""
            QWidget {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #667eea,
                    stop:1 #764ba2
                );
            }
        """)
        
        # Scroll area for content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                background: rgba(255, 255, 255, 0.1);
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background: rgba(255, 255, 255, 0.3);
                border-radius: 6px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(255, 255, 255, 0.5);
            }
        """)
        
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Header with back and delete buttons
        header_layout = QHBoxLayout()
        
        # Back button
        back_btn = QPushButton("← Back to Notes")
        back_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.2);
                color: white;
                border: none;
                border-radius: 10px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.3);
            }
        """)
        header_layout.addWidget(back_btn)
        
        header_layout.addStretch()
        
        # Delete button
        self.delete_btn = QPushButton("🗑️ Delete Note")
        self.delete_btn.clicked.connect(self.delete_note)
        self.delete_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #ff6b6b,
                    stop:1 #ee5a6f
                );
                color: white;
                border: none;
                border-radius: 10px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #ee5a6f,
                    stop:1 #ff6b6b
                );
            }
        """)
        header_layout.addWidget(self.delete_btn)
        
        layout.addLayout(header_layout)
        
        # Title
        self.title_label = QLabel()
        self.title_label.setStyleSheet("""
            font-size: 28px;
            font-weight: bold;
            color: white;
            background: transparent;
            margin: 10px 0;
        """)
        self.title_label.setWordWrap(True)
        layout.addWidget(self.title_label)
        
        # Date
        self.date_label = QLabel()
        self.date_label.setStyleSheet("""
            color: rgba(255, 255, 255, 0.8);
            font-size: 14px;
            background: transparent;
            margin-bottom: 10px;
        """)
        layout.addWidget(self.date_label)
        
        # Audio player with modern styling
        player_frame = QFrame()
        player_frame.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.15);
                border: none;
                border-radius: 16px;
                padding: 20px;
            }
        """)
        player_layout = QVBoxLayout(player_frame)
        
        player_title = QLabel("🎵 Audio Player")
        player_title.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: white;
            background: transparent;
        """)
        player_layout.addWidget(player_title)
        
        # Playback controls
        controls_layout = QHBoxLayout()
        
        self.play_btn = QPushButton("▶ Play")
        self.play_btn.clicked.connect(self.toggle_playback)
        self.play_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #f093fb,
                    stop:1 #f5576c
                );
                color: white;
                border: none;
                border-radius: 10px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #f5576c,
                    stop:1 #f093fb
                );
            }
        """)
        controls_layout.addWidget(self.play_btn)
        
        self.stop_btn = QPushButton("⏹ Stop")
        self.stop_btn.clicked.connect(self.stop_playback)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.2);
                color: white;
                border: none;
                border-radius: 10px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.3);
            }
        """)
        controls_layout.addWidget(self.stop_btn)
        
        controls_layout.addStretch()
        
        self.duration_label = QLabel("00:00 / 00:00")
        self.duration_label.setStyleSheet("""
            color: white;
            font-size: 14px;
            background: transparent;
        """)
        controls_layout.addWidget(self.duration_label)
        
        player_layout.addLayout(controls_layout)
        
        # Progress slider
        self.progress_slider = QSlider(Qt.Orientation.Horizontal)
        self.progress_slider.setEnabled(False)
        self.progress_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                background: rgba(255, 255, 255, 0.2);
                height: 8px;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: white;
                width: 18px;
                height: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }
            QSlider::sub-page:horizontal {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4facfe,
                    stop:1 #00f2fe
                );
                border-radius: 4px;
            }
        """)
        player_layout.addWidget(self.progress_slider)
        
        layout.addWidget(player_frame)
        
        # Summary section
        summary_frame = QFrame()
        summary_frame.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.15);
                border: none;
                border-radius: 16px;
                padding: 20px;
            }
        """)
        summary_layout = QVBoxLayout(summary_frame)
        
        summary_title = QLabel("📝 Summary")
        summary_title.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: white;
            background: transparent;
        """)
        summary_layout.addWidget(summary_title)
        
        self.summary_text = QTextEdit()
        self.summary_text.setReadOnly(True)
        self.summary_text.setMinimumHeight(150)
        self.summary_text.setStyleSheet("""
            QTextEdit {
                background: rgba(255, 255, 255, 0.9);
                border: none;
                border-radius: 10px;
                padding: 12px;
                font-size: 14px;
                color: #333;
            }
        """)
        summary_layout.addWidget(self.summary_text)
        
        layout.addWidget(summary_frame)
        
        # Collapsible transcription section
        self.transcription_section = CollapsibleSection("📄 Full Transcription")
        
        self.transcription_text = QTextEdit()
        self.transcription_text.setReadOnly(True)
        self.transcription_text.setMinimumHeight(200)
        self.transcription_text.setStyleSheet("""
            QTextEdit {
                background: rgba(255, 255, 255, 0.9);
                border: none;
                border-radius: 10px;
                padding: 12px;
                font-size: 14px;
                color: #333;
            }
        """)
        self.transcription_section.set_content(self.transcription_text)
        
        layout.addWidget(self.transcription_section)
        
        layout.addStretch()
        
        scroll.setWidget(content)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)
    
    def load_note(self, note):
        """Load a note into the view"""
        self.note = note
        
        # Update UI
        self.title_label.setText(note.title)
        self.date_label.setText(f"Created: {note.created_at}")
        self.summary_text.setPlainText(note.summary)
        self.transcription_text.setPlainText(note.transcription)
        
        # Load audio
        try:
            self.audio_player.load(note.audio_path)
            duration_mins = int(note.duration // 60)
            duration_secs = int(note.duration % 60)
            self.duration_label.setText(f"00:00 / {duration_mins:02d}:{duration_secs:02d}")
            self.progress_slider.setMaximum(int(note.duration * 10))  # 10 updates per second
            self.progress_slider.setValue(0)
        except Exception as e:
            self.duration_label.setText(f"Error loading audio: {str(e)}")
    
    def toggle_playback(self):
        """Toggle play/pause"""
        try:
            if self.audio_player.is_playing:
                self.audio_player.pause()
                self.play_btn.setText("▶ Play")
                self.playback_timer.stop()
            else:
                import time
                self.audio_player.play()
                self.play_btn.setText("⏸ Pause")
                self.playback_start_time = time.time() - self.playback_position
                self.playback_timer.start()
        except Exception as e:
            print(f"Playback error: {e}")
            self.play_btn.setText("▶ Play")
            self.playback_timer.stop()
            self.duration_label.setText(f"Playback error: {str(e)}")
    
    def stop_playback(self):
        """Stop playback"""
        self.audio_player.stop()
        self.play_btn.setText("▶ Play")
        self.playback_timer.stop()
        self.playback_position = 0
        self.progress_slider.setValue(0)
        if self.note:
            duration_mins = int(self.note.duration // 60)
            duration_secs = int(self.note.duration % 60)
            self.duration_label.setText(f"00:00 / {duration_mins:02d}:{duration_secs:02d}")
    
    def update_playback(self):
        """Update playback position"""
        if not self.audio_player.is_busy():
            # Playback finished
            self.stop_playback()
            return
        
        if not self.note:
            return
        
        # Calculate current position based on elapsed time
        import time
        self.playback_position = time.time() - self.playback_start_time
        
        # Clamp to duration
        if self.playback_position > self.note.duration:
            self.playback_position = self.note.duration
        
        # Update slider
        self.progress_slider.setValue(int(self.playback_position * 10))
        
        # Update time label
        current_mins = int(self.playback_position // 60)
        current_secs = int(self.playback_position % 60)
        duration_mins = int(self.note.duration // 60)
        duration_secs = int(self.note.duration % 60)
        self.duration_label.setText(f"{current_mins:02d}:{current_secs:02d} / {duration_mins:02d}:{duration_secs:02d}")
    
    def hideEvent(self, event):
        """Stop playback when view is hidden"""
        self.stop_playback()
        super().hideEvent(event)
    
    def delete_note(self):
        """Delete the current note with confirmation"""
        if not self.note:
            return
        
        # Show confirmation dialog
        reply = QMessageBox.question(
            self,
            'Delete Note',
            f'Are you sure you want to delete "{self.note.title}"?\n\nThis action cannot be undone.',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Stop playback
            self.stop_playback()
            
            # Delete audio file if it exists
            if os.path.exists(self.note.audio_path):
                try:
                    os.remove(self.note.audio_path)
                except Exception as e:
                    print(f"Warning: Could not delete audio file: {e}")
            
            # Delete note from storage
            if self.parent_window and hasattr(self.parent_window, 'storage'):
                self.parent_window.storage.delete_note(self.note.id)
                
                # Go back to main window
                self.hide()
                central_widget = QWidget()
                self.parent_window.setCentralWidget(central_widget)
                self.parent_window.setup_ui()
                self.parent_window.load_notes()
                
                QMessageBox.information(
                    self.parent_window,
                    'Note Deleted',
                    'The note has been successfully deleted.'
                )
