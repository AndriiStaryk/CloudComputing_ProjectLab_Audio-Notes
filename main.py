"""
Audio Notes Application - Main Entry Point
"""
import sys
import os
from dotenv import load_dotenv
from PyQt6.QtWidgets import QApplication, QMessageBox
from ui.main_window import MainWindow
from services.speech_to_text import SpeechToTextService
from services.summarizer import SummarizerService


def check_environment():
    """Check if all required environment variables are set"""
    required_vars = [
        'GOOGLE_APPLICATION_CREDENTIALS',
        'GOOGLE_CLOUD_PROJECT_ID'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        return False, missing_vars
    
    # Check if credentials file exists
    creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    if creds_path and not os.path.exists(creds_path):
        return False, [f"Credentials file not found: {creds_path}"]
    
    return True, []


def main():
    """Main application entry point"""
    # Load environment variables
    load_dotenv()
    
    # Create Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("Audio Notes")
    
    # Check environment
    env_ok, missing = check_environment()
    if not env_ok:
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setWindowTitle("Configuration Error")
        msg.setText("Missing required configuration!")
        msg.setInformativeText(
            "Please set up your environment variables:\n\n" +
            "\n".join(f"- {var}" for var in missing) +
            "\n\nSee README.md for setup instructions."
        )
        msg.exec()
        sys.exit(1)
    
    try:
        # Initialize services
        stt_service = SpeechToTextService()
        summarizer_service = SummarizerService(
            project_id=os.getenv('GOOGLE_CLOUD_PROJECT_ID'),
            credentials_path=os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        )
        
        # Create and show main window
        window = MainWindow(stt_service, summarizer_service)
        window.show()
        
        # Run application
        sys.exit(app.exec())
        
    except Exception as e:
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setWindowTitle("Startup Error")
        msg.setText("Failed to start application!")
        msg.setInformativeText(str(e))
        msg.setDetailedText(
            "Make sure you have:\n"
            "1. Set up Google Cloud credentials correctly\n"
            "2. Enabled Speech-to-Text API\n"
            "3. Enabled Vertex AI API\n"
            "4. Set GOOGLE_CLOUD_PROJECT_ID\n\n"
            "See README.md for detailed setup instructions."
        )
        msg.exec()
        sys.exit(1)


if __name__ == '__main__':
    main()
