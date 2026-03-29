"""
Voice Processor - Handles audio capture, processing, and playback
"""

import logging
import numpy as np
from pathlib import Path
from typing import Optional, Tuple
from datetime import datetime

try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False

logger = logging.getLogger(__name__)


class VoiceProcessor:
    """
    Handles voice input/output on edge devices.
    
    Supports:
    - Microphone input with noise suppression
    - Speaker output with volume control
    - Audio format conversion
    - Voice activity detection
    """
    
    def __init__(self, 
                 sample_rate: int = 16000,
                 chunk_size: int = 1024,
                 channels: int = 1,
                 audio_dir: str = "data/audio"):
        """
        Initialize voice processor.
        
        Args:
            sample_rate: Audio sample rate in Hz (16000 for speech)
            chunk_size: Chunk size for streaming
            channels: Number of audio channels (1 for mono)
            audio_dir: Directory for audio files
        """
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.channels = channels
        self.audio_dir = Path(audio_dir)
        self.audio_dir.mkdir(parents=True, exist_ok=True)
        
        self.stream = None
        self.is_recording = False
        
        if PYAUDIO_AVAILABLE:
            self.p = pyaudio.PyAudio()
        else:
            self.p = None
            logger.warning("PyAudio not available - voice input disabled")
        
        logger.info(f"VoiceProcessor initialized - Sample rate: {sample_rate}Hz, "
                   f"Channels: {channels}, Chunk: {chunk_size}")
    
    def record_audio(self, duration: float, filename: Optional[str] = None) -> Optional[np.ndarray]:
        """
        Record audio from microphone.
        
        Args:
            duration: Recording duration in seconds
            filename: Optional file to save recording
            
        Returns:
            Audio data as numpy array or None if recording failed
        """
        if not PYAUDIO_AVAILABLE or self.p is None:
            logger.error("PyAudio not available for recording")
            return None
        
        try:
            logger.info(f"Starting audio recording ({duration}s)...")
            
            self.stream = self.p.open(
                format=8,  # pyaudio.paInt16
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size
            )
            
            frames = []
            for _ in range(int(self.sample_rate / self.chunk_size * duration)):
                data = self.stream.read(self.chunk_size)
                frames.append(np.frombuffer(data, dtype=np.int16))
            
            self.stream.stop_stream()
            self.stream.close()
            
            audio_data = np.concatenate(frames)
            
            if filename:
                self._save_audio(audio_data, filename)
            
            logger.info(f"Recording complete: {len(audio_data)} samples")
            return audio_data
            
        except Exception as e:
            logger.error(f"Recording failed: {e}")
            if self.stream:
                self.stream.stop_stream()
                self.stream.close()
            return None
    
    def playback_audio(self, audio_data: np.ndarray, wait: bool = True) -> bool:
        """
        Play audio through speaker.
        
        Args:
            audio_data: Audio data as numpy array
            wait: Wait for playback to complete
            
        Returns:
            True if successful
        """
        if not PYAUDIO_AVAILABLE or self.p is None:
            logger.warning("PyAudio not available for playback")
            return False
        
        try:
            logger.info(f"Starting audio playback ({len(audio_data)} samples)...")
            
            self.stream = self.p.open(
                format=8,  # pyaudio.paInt16
                channels=self.channels,
                rate=self.sample_rate,
                output=True,
                frames_per_buffer=self.chunk_size
            )
            
            # Convert to int16 if needed
            if audio_data.dtype != np.int16:
                audio_data = (audio_data * 32767).astype(np.int16)
            
            for i in range(0, len(audio_data), self.chunk_size):
                chunk = audio_data[i:i+self.chunk_size]
                self.stream.write(chunk.tobytes())
            
            if wait:
                self.stream.stop_stream()
                self.stream.close()
                logger.info("Playback complete")
            
            return True
            
        except Exception as e:
            logger.error(f"Playback failed: {e}")
            if self.stream:
                self.stream.stop_stream()
                self.stream.close()
            return False
    
    def detect_voice_activity(self, audio_data: np.ndarray, 
                            threshold: float = 0.02) -> Tuple[bool, float]:
        """
        Detect if audio contains voice (simple energy-based).
        
        Args:
            audio_data: Audio data as numpy array
            threshold: Energy threshold for voice detection
            
        Returns:
            (has_voice, energy_level)
        """
        # Normalize audio
        audio_norm = audio_data.astype(np.float32) / 32768.0
        
        # Calculate RMS energy
        energy = np.sqrt(np.mean(audio_norm ** 2))
        
        has_voice = energy > threshold
        
        return has_voice, float(energy)
    
    def _save_audio(self, audio_data: np.ndarray, filename: str) -> bool:
        """Save audio data to file."""
        try:
            import soundfile as sf
            filepath = self.audio_dir / filename
            sf.write(str(filepath), audio_data, self.sample_rate)
            logger.info(f"Audio saved: {filepath}")
            return True
        except ImportError:
            logger.warning("soundfile not available for saving audio")
            return False
        except Exception as e:
            logger.error(f"Failed to save audio: {e}")
            return False
    
    def cleanup(self) -> None:
        """Clean up resources."""
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        
        if self.p:
            self.p.terminate()
        
        logger.info("VoiceProcessor cleanup complete")
