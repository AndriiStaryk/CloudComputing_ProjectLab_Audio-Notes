"""
Audio recording dialog
"""
import os
import wave
import pyaudio
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QFileDialog, QMessageBox, QLineEdit
)
from PyQt6.QtCore import QTimer, Qt
from datetime import datetime


class AudioRecorderDialog(QDialog):
    """Dialog for recording or uploading audio"""
    
    def __init__(self, storage_dir: str, parent=None):
        super().__init__(parent)
        self.storage_dir = storage_dir
        self.audio_path = None
        self.is_recording = False
        self.frames = []
        self.audio = None
        self.stream = None
        self.recording_time = 0
        
        self.setup_ui()
        self.setup_audio()
    
    def setup_ui(self):
        """Setup the user interface"""
        self.setWindowTitle("Add Audio Note")
        self.setModal(True)
        self.resize(500, 400)
        
        # Gradient background
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #667eea,
                    stop:1 #764ba2
                );
            }
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Title
        title = QLabel("Add Audio Note")
        title.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: white;
            background: transparent;
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Note name input
        name_label = QLabel("Note Name (optional):")
        name_label.setStyleSheet("""
            color: white;
            font-size: 14px;
            background: transparent;
        """)
        layout.addWidget(name_label)
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter a name for your note...")
        self.name_input.setStyleSheet("""
            QLineEdit {
                background: rgba(255, 255, 255, 0.9);
                border: none;
                border-radius: 10px;
                padding: 12px;
                font-size: 14px;
                color: #333;
            }
            QLineEdit:focus {
                background: white;
            }
        """)
        layout.addWidget(self.name_input)
        
        layout.addSpacing(10)
        
        # Record button
        self.record_btn = QPushButton("🎤 Start Recording")
        self.record_btn.clicked.connect(self.toggle_recording)
        self.record_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #f093fb,
                    stop:1 #f5576c
                );
                color: white;
                border: none;
                border-radius: 12px;
                padding: 15px;
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
        """)
        layout.addWidget(self.record_btn)
        
        # Or separator
        separator = QLabel("— OR —")
        separator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        separator.setStyleSheet("""
            color: rgba(255, 255, 255, 0.7);
            font-size: 14px;
            margin: 10px;
            background: transparent;
        """)
        layout.addWidget(separator)
        
        # Upload button
        upload_btn = QPushButton("📁 Upload Audio File")
        upload_btn.clicked.connect(self.upload_audio)
        upload_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.2);
                color: white;
                border: none;
                border-radius: 12px;
                padding: 15px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.3);
            }
        """)
        layout.addWidget(upload_btn)
        
        layout.addStretch()
        
        # Button layout
        button_layout = QHBoxLayout()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.15);
                color: white;
                border: none;
                border-radius: 10px;
                padding: 12px 24px;
                font-size: 14px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.25);
            }
        """)
        button_layout.addWidget(cancel_btn)
        
        self.ok_btn = QPushButton("Create Note")
        self.ok_btn.clicked.connect(self.accept)
        self.ok_btn.setEnabled(False)
        self.ok_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4facfe,
                    stop:1 #00f2fe
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
                    stop:0 #00f2fe,
                    stop:1 #4facfe
                );
            }
            QPushButton:disabled {
                background: rgba(255, 255, 255, 0.1);
                color: rgba(255, 255, 255, 0.4);
            }
        """)
        button_layout.addWidget(self.ok_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # Timer for recording duration
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_recording_time)
    
    def setup_audio(self):
        """Setup PyAudio for recording"""
        self.audio = pyaudio.PyAudio()
        self.chunk = 1024
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = 16000
    
    def toggle_recording(self):
        """Start or stop recording"""
        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_recording()
    
    def start_recording(self):
        """Start recording audio"""
        try:
            self.frames = []
            self.recording_time = 0
            
            self.stream = self.audio.open(
                format=self.format,
                channels=self.channels,
                rate=self.rate,
                input=True,
                frames_per_buffer=self.chunk,
                stream_callback=self.audio_callback
            )
            
            self.stream.start_stream()
            self.is_recording = True
            self.record_btn.setText("⏹ Stop Recording")
            self.record_btn.setStyleSheet("""
                QPushButton {
                    background: #ff4444;
                    color: white;
                    border: none;
                    border-radius: 12px;
                    padding: 15px;
                    font-size: 16px;
                    font-weight: bold;
                }
            """)
            self.timer.start(1000)  # Update every second
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to start recording: {str(e)}")
    
    def stop_recording(self):
        """Stop recording audio"""
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        
        self.is_recording = False
        self.timer.stop()
        self.record_btn.setText("✅ Recording Saved")
        self.record_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #11998e,
                    stop:1 #38ef7d
                );
                color: white;
                border: none;
                border-radius: 12px;
                padding: 15px;
                font-size: 16px;
                font-weight: bold;
            }
        """)
        self.record_btn.setEnabled(False)
        
        # Save recording
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"recording_{timestamp}.wav"
        self.audio_path = os.path.join(self.storage_dir, filename)
        
        # Write WAV file
        with wave.open(self.audio_path, 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(self.audio.get_sample_size(self.format))
            wf.setframerate(self.rate)
            wf.writeframes(b''.join(self.frames))
        
        self.ok_btn.setEnabled(True)
    
    def audio_callback(self, in_data, frame_count, time_info, status):
        """Callback for audio stream"""
        self.frames.append(in_data)
        return (in_data, pyaudio.paContinue)
    
    def update_recording_time(self):
        """Update recording time display"""
        self.recording_time += 1
        minutes = self.recording_time // 60
        seconds = self.recording_time % 60
        self.record_btn.setText(f"⏺ Recording... {minutes:02d}:{seconds:02d}")
    
    def upload_audio(self):
        """Upload an existing audio file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Audio File",
            "",
            "Audio Files (*.mp3 *.mp4 *.wav *.m4a);;All Files (*)"
        )
        
        if file_path:
            # Copy file to storage directory
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_ext = os.path.splitext(file_path)[1]
            filename = f"upload_{timestamp}{file_ext}"
            self.audio_path = os.path.join(self.storage_dir, filename)
            
            # Copy file
            import shutil
            shutil.copy2(file_path, self.audio_path)
            
            # Show success
            self.record_btn.setText(f"✅ File Uploaded")
            self.record_btn.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(
                        x1:0, y1:0, x2:1, y2:0,
                        stop:0 #11998e,
                        stop:1 #38ef7d
                    );
                    color: white;
                    border: none;
                    border-radius: 12px;
                    padding: 15px;
                    font-size: 16px;
                    font-weight: bold;
                }
            """)
            self.record_btn.setEnabled(False)
            self.ok_btn.setEnabled(True)
    
    def get_audio_path(self) -> str:
        """Get the path to the recorded/uploaded audio"""
        return self.audio_path
    
    def get_note_name(self) -> str:
        """Get the custom note name if provided"""
        return self.name_input.text().strip() if hasattr(self, 'name_input') else ""
    
    def closeEvent(self, event):
        """Clean up when dialog closes"""
        if self.is_recording:
            self.stop_recording()
        
        if self.audio:
            self.audio.terminate()
        
        super().closeEvent(event)
