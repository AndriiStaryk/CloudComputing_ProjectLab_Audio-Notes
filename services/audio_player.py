"""
Audio playback service
"""
import os
import pygame
import subprocess
import json
from mutagen import File as MutagenFile


class AudioPlayer:
    """Service for playing audio files"""
    
    def __init__(self):
        pygame.mixer.init()
        self.current_file = None
        self.converted_file = None
        self.is_playing = False
        self.is_paused = False
    
    def _convert_for_playback(self, audio_path: str) -> str:
        """Convert audio file to MP3 for playback if needed"""
        file_ext = os.path.splitext(audio_path)[1].lower()
        
        # Pygame supports these formats directly
        supported_formats = ['.mp3', '.ogg', '.wav']
        
        if file_ext in supported_formats:
            return audio_path
        
        # Convert to MP3 for playback
        mp3_path = audio_path.rsplit('.', 1)[0] + '_playback.mp3'
        
        # Check if already converted
        if os.path.exists(mp3_path):
            print(f"Using existing converted file: {mp3_path}")
            return mp3_path
        
        print(f"Converting {file_ext} to MP3 for playback...")
        try:
            result = subprocess.run([
                'ffmpeg', '-i', audio_path,
                '-vn',  # No video
                '-ar', '44100',  # Sample rate
                '-ac', '2',  # Stereo
                '-b:a', '192k',  # Bitrate
                '-y',  # Overwrite
                mp3_path
            ], check=True, capture_output=True)
            print(f"Conversion successful: {mp3_path}")
            return mp3_path
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.decode() if e.stderr else str(e)
            print(f"Conversion failed: {error_msg}")
            raise Exception(f"Failed to convert audio for playback: {error_msg}")
    
    def load(self, audio_path: str):
        """Load an audio file"""
        try:
            print(f"Loading audio: {audio_path}")
            
            # Check if file exists
            if not os.path.exists(audio_path):
                raise Exception(f"Audio file not found: {audio_path}")
            
            # Clean up previous converted file
            if self.converted_file and self.converted_file != self.current_file:
                if os.path.exists(self.converted_file):
                    try:
                        os.remove(self.converted_file)
                    except:
                        pass
            
            # Convert if needed
            playback_path = self._convert_for_playback(audio_path)
            
            print(f"Loading into pygame: {playback_path}")
            
            self.current_file = audio_path
            self.converted_file = playback_path if playback_path != audio_path else None
            
            pygame.mixer.music.load(playback_path)
            self.is_playing = False
            self.is_paused = False
            
            print("Audio loaded successfully")
        except Exception as e:
            print(f"Error in load(): {e}")
            raise Exception(f"Error loading audio: {str(e)}")
    
    def play(self):
        """Play the loaded audio"""
        try:
            if not self.current_file:
                raise Exception("No audio file loaded")
            
            if self.is_paused:
                pygame.mixer.music.unpause()
                self.is_paused = False
                self.is_playing = True
            else:
                # Ensure the file is actually loaded
                pygame.mixer.music.play()
                self.is_playing = True
                
        except Exception as e:
            print(f"Error playing audio: {e}")
            self.is_playing = False
            raise
    
    def pause(self):
        """Pause the audio"""
        if self.is_playing:
            pygame.mixer.music.pause()
            self.is_paused = True
            self.is_playing = False
    
    def stop(self):
        """Stop the audio"""
        pygame.mixer.music.stop()
        self.is_playing = False
        self.is_paused = False
        
        # Clean up converted file when stopping
        if self.converted_file and os.path.exists(self.converted_file):
            try:
                # Don't delete immediately as pygame might still be using it
                pass
            except:
                pass
    
    def get_duration(self, audio_path: str) -> float:
        """Get duration of audio file in seconds"""
        try:
            # Try using mutagen first (more reliable)
            audio_file = MutagenFile(audio_path)
            if audio_file is not None and hasattr(audio_file.info, 'length'):
                return float(audio_file.info.length)
            
            # Fallback to ffprobe
            result = subprocess.run([
                'ffprobe', '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'json',
                audio_path
            ], capture_output=True, text=True, check=True)
            
            data = json.loads(result.stdout)
            return float(data['format']['duration'])
        except Exception as e:
            print(f"Error getting duration: {e}")
            return 0.0
    
    def set_volume(self, volume: float):
        """Set volume (0.0 to 1.0)"""
        pygame.mixer.music.set_volume(volume)
    
    def is_busy(self) -> bool:
        """Check if audio is currently playing"""
        return pygame.mixer.music.get_busy()
