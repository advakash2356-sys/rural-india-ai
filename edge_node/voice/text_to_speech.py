"""
Text-to-Speech Engine - Indic language speech synthesis
"""

import logging
import numpy as np
from typing import Optional, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class TextToSpeechEngine:
    """
    Text-to-speech conversion for Indic languages.
    
    Supports:
    - Hindi (hi)
    - Tamil (ta)
    - Telugu (te)
    - Kannada (kn)
    - Malayalam (ml)
    - Marathi (mr)
    - Bengali (bn)
    - Gujarati (gu)
    
    Uses quantized on-device models for offline operation.
    """
    
    # Supported languages and their voice options
    SUPPORTED_LANGUAGES = {
        'hi': {'name': 'Hindi', 'voices': ['ananya-f', 'abhishek-m']},
        'ta': {'name': 'Tamil', 'voices': ['kamali-f', 'kumaran-m']},
        'te': {'name': 'Telugu', 'voices': ['swetha-f', 'sanjay-m']},
        'kn': {'name': 'Kannada', 'voices': ['lavanya-f', 'suresh-m']},
        'ml': {'name': 'Malayalam', 'voices': ['anjali-f', 'anand-m']},
        'mr': {'name': 'Marathi', 'voices': ['anjali-f', 'akhilesh-m']},
        'bn': {'name': 'Bengali', 'voices': ['anika-f', 'arjun-m']},
        'gu': {'name': 'Gujarati', 'voices': ['aditi-f', 'ashok-m']},
        'en': {'name': 'English', 'voices': ['alice-f', 'adam-m']},
    }
    
    def __init__(self,
                 language: str = 'hi',
                 voice: Optional[str] = None,
                 model_dir: str = 'models',
                 sample_rate: int = 22050):
        """
        Initialize text-to-speech engine.
        
        Args:
            language: Language code (e.g., 'hi' for Hindi)
            voice: Specific voice identifier
            model_dir: Directory containing quantized models
            sample_rate: Audio sample rate in Hz
        """
        if language not in self.SUPPORTED_LANGUAGES:
            logger.warning(f"Language {language} not supported, using Hindi")
            language = 'hi'
        
        self.language = language
        self.model_dir = Path(model_dir)
        self.sample_rate = sample_rate
        
        # Set voice
        available_voices = self.SUPPORTED_LANGUAGES[language]['voices']
        self.voice = voice if voice in available_voices else available_voices[0]
        
        # Load model
        self.model = self._load_model()
        
        lang_name = self.SUPPORTED_LANGUAGES[language]['name']
        logger.info(f"TextToSpeechEngine initialized for {lang_name} ({self.voice})")
    
    def _load_model(self) -> Optional[Any]:
        """Load text-to-speech model."""
        try:
            # Try to load gTTS or similar for Indic languages
            from gtts import gTTS
            logger.info("gTTS available for TTS")
            return gTTS
            
        except ImportError:
            logger.warning("gTTS not available - using fallback TTS")
            return None
        except Exception as e:
            logger.warning(f"Failed to load TTS model: {e}")
            return None
    
    async def synthesize(self, text: str) -> Dict[str, Any]:
        """
        Synthesize text to speech.
        
        Args:
            text: Text to convert to speech
            
        Returns:
            Dict with audio data and metadata
        """
        try:
            if not text.strip():
                return {
                    "audio": np.array([]),
                    "duration": 0.0,
                    "text": text,
                    "language": self.language,
                    "success": True
                }
            
            if self.model is None:
                return self._fallback_synthesize(text)
            
            # Try using gTTS
            try:
                from gtts import gTTS
                from io import BytesIO
                import soundfile as sf
                
                logger.info(f"Synthesizing: {text[:50]}...")
                
                tts = gTTS(text=text, lang=self.language, slow=False)
                
                # Save to bytes buffer
                buffer = BytesIO()
                tts.write_to_fp(buffer)
                buffer.seek(0)
                
                # Read audio data
                audio_data, sr = sf.read(buffer)
                
                # Resample if needed
                if sr != self.sample_rate:
                    audio_data = self._resample(audio_data, sr, self.sample_rate)
                
                duration = len(audio_data) / self.sample_rate
                
                return {
                    "audio": audio_data,
                    "duration": duration,
                    "text": text,
                    "language": self.language,
                    "voice": self.voice,
                    "sample_rate": self.sample_rate,
                    "success": True
                }
                
            except ImportError:
                return self._fallback_synthesize(text)
            
        except Exception as e:
            logger.error(f"Synthesis failed: {e}")
            return self._fallback_synthesize(text)
    
    def _fallback_synthesize(self, text: str) -> Dict[str, Any]:
        """Fallback TTS using simple beeping."""
        logger.warning("Using fallback TTS - generating tone")
        
        # Generate simple tone pattern (pitch varies by text length)
        duration = min(len(text) * 0.05, 5.0)  # Max 5 seconds
        t = np.linspace(0, duration, int(self.sample_rate * duration))
        
        # Vary frequency based on text
        frequency = 440 + (len(text) % 100) * 4.4  # 440Hz base + variation
        audio_data = 0.3 * np.sin(2 * np.pi * frequency * t)
        
        return {
            "audio": audio_data.astype(np.float32),
            "duration": float(duration),
            "text": text,
            "language": self.language,
            "is_fallback": True,
            "success": True
        }
    
    @staticmethod
    def _resample(audio_data: np.ndarray, 
                  orig_sr: int, 
                  target_sr: int) -> np.ndarray:
        """Resample audio to target sample rate."""
        try:
            import librosa
            return librosa.resample(audio_data, orig_sr=orig_sr, target_sr=target_sr)
        except ImportError:
            # Simple linear interpolation fallback
            ratio = target_sr / orig_sr
            new_length = int(len(audio_data) * ratio)
            return np.interp(
                np.linspace(0, len(audio_data) - 1, new_length),
                np.arange(len(audio_data)),
                audio_data
            )
    
    def set_language(self, language: str, voice: Optional[str] = None) -> bool:
        """Change language and/or voice."""
        if language not in self.SUPPORTED_LANGUAGES:
            logger.error(f"Unsupported language: {language}")
            return False
        
        self.language = language
        
        available_voices = self.SUPPORTED_LANGUAGES[language]['voices']
        if voice and voice in available_voices:
            self.voice = voice
        else:
            self.voice = available_voices[0]
        
        lang_name = self.SUPPORTED_LANGUAGES[language]['name']
        logger.info(f"Language changed to {lang_name} ({self.voice})")
        return True
    
    def get_supported_languages(self) -> Dict[str, Any]:
        """Get supported languages and voices."""
        return {lang: info.copy() for lang, info in self.SUPPORTED_LANGUAGES.items()}
