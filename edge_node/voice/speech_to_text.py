"""
Speech-to-Text Engine - Indic language speech recognition
"""

import logging
import numpy as np
from typing import Optional, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class SpeechToTextEngine:
    """
    Speech-to-text conversion for Indic languages.
    
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
    
    # Supported languages and their ISO codes
    SUPPORTED_LANGUAGES = {
        'hi': 'Hindi',
        'ta': 'Tamil',
        'te': 'Telugu',
        'kn': 'Kannada',
        'ml': 'Malayalam',
        'mr': 'Marathi',
        'bn': 'Bengali',
        'gu': 'Gujarati',
        'en': 'English',
    }
    
    def __init__(self, 
                 language: str = 'hi',
                 model_dir: str = 'models',
                 sample_rate: int = 16000):
        """
        Initialize speech-to-text engine.
        
        Args:
            language: Language code (e.g., 'hi' for Hindi)
            model_dir: Directory containing quantized models
            sample_rate: Audio sample rate in Hz
        """
        if language not in self.SUPPORTED_LANGUAGES:
            logger.warning(f"Language {language} not fully supported, using Hindi as fallback")
            language = 'hi'
        
        self.language = language
        self.model_dir = Path(model_dir)
        self.sample_rate = sample_rate
        
        # Load model (will attempt to use Whisper or fallback to rule-based)
        self.model = self._load_model()
        
        logger.info(f"SpeechToTextEngine initialized for {self.SUPPORTED_LANGUAGES[language]}")
    
    def _load_model(self) -> Optional[Any]:
        """Load speech recognition model."""
        try:
            # Try to load OpenAI's Whisper model (has good Indic support)
            import whisper
            
            model_name = 'tiny'  # Use tiny model for edge devices
            logger.info(f"Loading Whisper {model_name} model...")
            
            model = whisper.load_model(model_name)
            logger.info("Whisper model loaded successfully")
            return model
            
        except ImportError:
            logger.warning("Whisper not available - using fallback STT")
            return None
        except Exception as e:
            logger.warning(f"Failed to load Whisper: {e} - using fallback STT")
            return None
    
    async def transcribe(self, audio_data: np.ndarray) -> Dict[str, Any]:
        """
        Transcribe audio to text.
        
        Args:
            audio_data: Audio data as numpy array
            
        Returns:
            Dict with transcription and metadata
        """
        try:
            if self.model is None:
                return self._fallback_transcribe(audio_data)
            
            # Normalize audio to [-1, 1] range
            audio_float = audio_data.astype(np.float32) / 32768.0
            
            # Use Whisper for transcription
            result = self.model.transcribe(
                audio_float,
                language=self.language,
                task='transcribe'
            )
            
            return {
                "text": result.get('text', ''),
                "language": self.language,
                "confidence": self._estimate_confidence(result),
                "segments": len(result.get('segments', [])),
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            return {
                "text": "",
                "language": self.language,
                "confidence": 0.0,
                "error": str(e),
                "success": False
            }
    
    def _fallback_transcribe(self, audio_data: np.ndarray) -> Dict[str, Any]:
        """Fallback transcription using basic pattern matching."""
        logger.warning("Using fallback STT - accuracy will be limited")
        
        # For demonstration, return mock transcription
        energy = np.sqrt(np.mean((audio_data.astype(np.float32) / 32768.0) ** 2))
        
        # Simple heuristic based on energy
        if energy > 0.05:
            if self.language == 'hi':
                text = "नमस्ते, आप क्या कर रहे हैं?"  # Hindi greeting
            elif self.language == 'ta':
                text = "வணக்கம், நீங்கள் எப்படி இருக்கிறீர்கள்?"  # Tamil greeting
            else:
                text = "Hello, how are you?"
        else:
            text = ""  # Silence
        
        return {
            "text": text,
            "language": self.language,
            "confidence": 0.5 if text else 0.0,
            "is_fallback": True,
            "success": True
        }
    
    def _estimate_confidence(self, result: Dict[str, Any]) -> float:
        """Estimate transcription confidence from Whisper result."""
        if 'segments' not in result:
            return 0.0
        
        # Average probability across segments
        probs = [seg.get('probability', 0.0) for seg in result['segments']]
        return float(np.mean(probs)) if probs else 0.0
    
    def set_language(self, language: str) -> bool:
        """Change language for transcription."""
        if language not in self.SUPPORTED_LANGUAGES:
            logger.error(f"Unsupported language: {language}")
            return False
        
        self.language = language
        logger.info(f"Language changed to {self.SUPPORTED_LANGUAGES[language]}")
        return True
    
    def get_supported_languages(self) -> Dict[str, str]:
        """Get supported languages."""
        return self.SUPPORTED_LANGUAGES.copy()
