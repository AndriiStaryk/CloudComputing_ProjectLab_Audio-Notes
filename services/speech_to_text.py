"""
Google Cloud Speech-to-Text integration
"""
import os
import subprocess
import time
from google.cloud import speech
from google.cloud import storage


class SpeechToTextService:
    """Service for transcribing audio using Google Cloud Speech-to-Text"""
    
    def __init__(self):
        self.client = speech.SpeechClient()
        self.storage_client = None
        self.bucket_name = None
        self.project_id = os.getenv('GOOGLE_CLOUD_PROJECT_ID')
    
    def _convert_to_wav(self, audio_path: str) -> str:
        """Convert audio file to WAV format for processing"""
        file_ext = os.path.splitext(audio_path)[1].lower()
        
        if file_ext == '.wav':
            return audio_path
        
        # Convert to WAV using ffmpeg
        wav_path = audio_path.rsplit('.', 1)[0] + '_converted.wav'
        try:
            subprocess.run([
                'ffmpeg', '-i', audio_path,
                '-ar', '16000',  # Sample rate
                '-ac', '1',       # Mono
                '-y',            # Overwrite
                wav_path
            ], check=True, capture_output=True)
            return wav_path
        except subprocess.CalledProcessError as e:
            raise Exception(f"Failed to convert audio: {e.stderr.decode()}")
    
    def _get_audio_duration(self, audio_path: str) -> float:
        """Get audio duration in seconds"""
        try:
            result = subprocess.run([
                'ffprobe', '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1',
                audio_path
            ], capture_output=True, text=True, check=True)
            return float(result.stdout.strip())
        except Exception:
            return 0.0
    
    def _setup_gcs_bucket(self):
        """Setup Google Cloud Storage bucket for long audio files"""
        if not self.storage_client:
            self.storage_client = storage.Client(project=self.project_id)
        
        # Use project-based bucket name
        if not self.bucket_name:
            self.bucket_name = f"{self.project_id}-audio-transcription"
        
        # Create bucket if it doesn't exist
        try:
            bucket = self.storage_client.get_bucket(self.bucket_name)
        except Exception:
            # Create bucket in us-central1 region
            bucket = self.storage_client.create_bucket(
                self.bucket_name,
                location='us-central1'
            )
        
        return bucket
    
    def _upload_to_gcs(self, audio_path: str) -> str:
        """Upload audio file to Google Cloud Storage and return GCS URI"""
        bucket = self._setup_gcs_bucket()
        
        # Generate blob name
        filename = os.path.basename(audio_path)
        blob_name = f"audio/{int(time.time())}_{filename}"
        
        # Upload file
        blob = bucket.blob(blob_name)
        blob.upload_from_filename(audio_path)
        
        # Return GCS URI
        gcs_uri = f"gs://{self.bucket_name}/{blob_name}"
        
        return gcs_uri, blob
    
    def _delete_from_gcs(self, blob):
        """Delete blob from Google Cloud Storage"""
        try:
            if blob:
                blob.delete()
        except Exception:
            pass
    
    def transcribe_audio(self, audio_path: str, language_code: str = "auto") -> str:
        """
        Transcribe audio file to text with automatic language detection
        Automatically uses long-running recognition for audio longer than 55 seconds
        
        Args:
            audio_path: Path to the audio file
            language_code: Language code (default: "auto" for automatic detection)
            
        Returns:
            Transcribed text
        """
        try:
            # Convert to WAV if needed
            wav_path = self._convert_to_wav(audio_path)
            
            # Check audio duration
            duration = self._get_audio_duration(wav_path)
            
            # Use long-running recognition for audio longer than 55 seconds
            if duration > 55:
                return self._transcribe_long_audio(wav_path, language_code)
            
            # Use synchronous recognition for short audio
            # Read audio file
            with open(wav_path, 'rb') as audio_file:
                content = audio_file.read()
            
            # Configure recognition with automatic language detection
            audio = speech.RecognitionAudio(content=content)
            
            if language_code == "auto":
                # Use automatic language detection with multiple language alternatives
                config = speech.RecognitionConfig(
                    encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                    # Specify multiple language alternatives for auto-detection
                    language_code="en-US",  # Primary language
                    alternative_language_codes=[
                        "uk-UA",  # Ukrainian
                        "ru-RU",  # Russian
                        "es-ES",  # Spanish
                        "fr-FR",  # French
                        "de-DE",  # German
                        "it-IT",  # Italian
                        "pt-PT",  # Portuguese
                        "pl-PL",  # Polish
                        "ja-JP",  # Japanese
                        "zh-CN",  # Chinese (Simplified)
                        "ko-KR",  # Korean
                        "ar-SA",  # Arabic
                        "hi-IN",  # Hindi
                        "tr-TR",  # Turkish
                    ],
                    enable_automatic_punctuation=True,
                    enable_word_time_offsets=False,
                )
            else:
                # Use specified language
                config = speech.RecognitionConfig(
                    encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                    language_code=language_code,
                    enable_automatic_punctuation=True,
                    enable_word_time_offsets=False,
                )
            
            # Perform transcription
            response = self.client.recognize(config=config, audio=audio)
            
            # Combine all transcripts
            transcription = " ".join(
                result.alternatives[0].transcript 
                for result in response.results
            )
            
            # Clean up converted file if it was created
            if wav_path != audio_path and os.path.exists(wav_path):
                os.remove(wav_path)
            
            return transcription if transcription else "No speech detected in audio."
            
        except Exception as e:
            # Clean up converted file if it was created
            if wav_path != audio_path and os.path.exists(wav_path):
                os.remove(wav_path)
            return f"Error during transcription: {str(e)}"
    
    def _transcribe_long_audio(self, audio_path: str, language_code: str = "auto") -> str:
        """
        Transcribe long audio files using async recognition with GCS
        
        Args:
            audio_path: Path to the audio file
            language_code: Language code (default: "auto" for automatic detection)
            
        Returns:
            Transcribed text
        """
        gcs_uri = None
        blob = None
        
        try:
            # Upload to GCS
            gcs_uri, blob = self._upload_to_gcs(audio_path)
            
            # Configure recognition
            audio = speech.RecognitionAudio(uri=gcs_uri)
            
            if language_code == "auto":
                config = speech.RecognitionConfig(
                    encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                    language_code="en-US",
                    alternative_language_codes=[
                        "uk-UA", "ru-RU", "es-ES", "fr-FR", "de-DE",
                        "it-IT", "pt-PT", "pl-PL", "ja-JP", "zh-CN",
                        "ko-KR", "ar-SA", "hi-IN", "tr-TR"
                    ],
                    enable_automatic_punctuation=True,
                )
            else:
                config = speech.RecognitionConfig(
                    encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                    language_code=language_code,
                    enable_automatic_punctuation=True,
                )
            
            # Start long-running recognition
            operation = self.client.long_running_recognize(config=config, audio=audio)
            
            # Wait for operation to complete
            print("Waiting for transcription to complete...")
            response = operation.result(timeout=300)  # 5 minute timeout
            
            # Combine all transcripts
            transcription = " ".join(
                result.alternatives[0].transcript 
                for result in response.results
            )
            
            # Clean up GCS file
            self._delete_from_gcs(blob)
            
            # Clean up converted file if it was created
            if audio_path.endswith('_converted.wav') and os.path.exists(audio_path):
                os.remove(audio_path)
            
            return transcription if transcription else "No speech detected in audio."
            
        except Exception as e:
            # Clean up GCS file
            self._delete_from_gcs(blob)
            
            # Clean up converted file if it was created
            if audio_path.endswith('_converted.wav') and os.path.exists(audio_path):
                os.remove(audio_path)
            
            return f"Error during transcription: {str(e)}"
    
    def transcribe_audio_long(self, audio_path: str, language_code: str = "en-US") -> str:
        """
        Transcribe long audio files using async recognition
        For files longer than 1 minute, use this method
        This method is now deprecated - use transcribe_audio() which automatically 
        handles both short and long audio files
        
        Args:
            audio_path: Path to the audio file
            language_code: Language code (default: en-US)
            
        Returns:
            Transcribed text
        """
        return self.transcribe_audio(audio_path, language_code)
