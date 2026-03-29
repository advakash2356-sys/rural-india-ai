"""
Audio Pipeline - Orchestrates voice I/O and processing
"""

import asyncio
import logging
import numpy as np
from typing import Optional, Dict, Any, Callable
from datetime import datetime

from .processor import VoiceProcessor
from .speech_to_text import SpeechToTextEngine
from .text_to_speech import TextToSpeechEngine

logger = logging.getLogger(__name__)


class AudioPipeline:
    """
    Complete audio pipeline for voice interaction.
    
    Flow:
    1. Capture audio from microphone
    2. Apply voice activity detection
    3. Convert speech to text (STT)
    4. Process text (send to AI/inference)
    5. Convert response to speech (TTS)
    6. Play audio output
    
    All operations optimized for edge devices with Indic language support.
    """
    
    def __init__(self,
                 language: str = 'hi',
                 sample_rate: int = 16000,
                 auto_playback: bool = True,
                 inference_callback: Optional[Callable] = None):
        """
        Initialize audio pipeline.
        
        Args:
            language: Indic language code (e.g., 'hi')
            sample_rate: Audio sample rate in Hz
            auto_playback: Automatically play responses
            inference_callback: Function to call with transcribed text
        """
        self.language = language
        self.sample_rate = sample_rate
        self.auto_playback = auto_playback
        self.inference_callback = inference_callback
        
        # Initialize subsystems
        self.voice_processor = VoiceProcessor(
            sample_rate=sample_rate,
            chunk_size=1024
        )
        
        self.stt_engine = SpeechToTextEngine(
            language=language,
            sample_rate=sample_rate
        )
        
        self.tts_engine = TextToSpeechEngine(
            language=language,
            sample_rate=22050  # TTS typically uses different sample rate
        )
        
        # Pipeline state
        self.is_active = False
        self.last_interaction = None
        self.interaction_count = 0
        
        logger.info(f"AudioPipeline initialized for {language}")
    
    async def process_voice_query(self, 
                                 duration: float = 5.0,
                                 save_audio: bool = False) -> Dict[str, Any]:
        """
        Complete voice query processing pipeline.
        
        Args:
            duration: Recording duration in seconds
            save_audio: Save raw audio files
            
        Returns:
            Pipeline result with transcription and response
        """
        result = {
            "success": False,
            "steps": [],
            "error": None,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        try:
            # Step 1: Capture audio
            logger.info(f"Step 1: Capturing audio ({duration}s)...")
            audio_filename = None
            if save_audio:
                audio_filename = f"query_{self.interaction_count}.wav"
            
            audio_data = self.voice_processor.record_audio(duration, audio_filename)
            
            if audio_data is None or len(audio_data) == 0:
                result["error"] = "Failed to capture audio"
                return result
            
            result["steps"].append({
                "name": "audio_capture",
                "samples": len(audio_data),
                "duration": duration
            })
            
            # Step 2: Voice activity detection
            logger.info("Step 2: Detecting voice activity...")
            has_voice, energy = self.voice_processor.detect_voice_activity(audio_data)
            
            result["steps"].append({
                "name": "vad",
                "has_voice": has_voice,
                "energy": float(energy)
            })
            
            if not has_voice:
                logger.warning("No voice activity detected")
                result["error"] = "No voice detected in audio"
                return result
            
            # Step 3: Speech-to-text
            logger.info("Step 3: Converting speech to text...")
            transcription = await self.stt_engine.transcribe(audio_data)
            
            result["steps"].append({
                "name": "stt",
                "text": transcription.get("text", ""),
                "confidence": transcription.get("confidence", 0.0),
                "language": transcription.get("language")
            })
            
            if not transcription.get("success"):
                result["error"] = "Speech-to-text failed"
                return result
            
            text = transcription.get("text", "").strip()
            if not text:
                result["error"] = "No text transcribed from audio"
                return result
            
            # Step 4: Process with callback (e.g., inference/AI)
            response_text = text  # Default: echo
            
            if self.inference_callback:
                logger.info("Step 4: Processing with inference...")
                try:
                    inference_result = await self.inference_callback(text)
                    response_text = inference_result.get("response", text)
                    
                    result["steps"].append({
                        "name": "inference",
                        "input": text,
                        "output": response_text
                    })
                except Exception as e:
                    logger.warning(f"Inference failed: {e}, echoing input")
            
            # Step 5: Text-to-speech
            logger.info("Step 5: Converting response to speech...")
            synthesis = await self.tts_engine.synthesize(response_text)
            
            result["steps"].append({
                "name": "tts",
                "text": response_text,
                "duration": synthesis.get("duration", 0.0)
            })
            
            if not synthesis.get("success"):
                result["error"] = "Text-to-speech failed"
                return result
            
            # Step 6: Playback
            if self.auto_playback:
                logger.info("Step 6: Playing response...")
                audio = synthesis.get("audio")
                
                if audio is not None and len(audio) > 0:
                    self.voice_processor.playback_audio(audio)
                    result["steps"].append({
                        "name": "playback",
                        "status": "played"
                    })
            
            result["success"] = True
            result["transcription"] = text
            result["response"] = response_text
            
            # Update state
            self.interaction_count += 1
            self.last_interaction = datetime.utcnow().isoformat()
            
            return result
            
        except Exception as e:
            logger.error(f"Pipeline error: {e}")
            result["error"] = str(e)
            return result
    
    async def continuous_listening(self,
                                   check_interval: float = 0.5) -> None:
        """
        Run continuous voice listening loop.
        
        Args:
            check_interval: Check interval in seconds
        """
        self.is_active = True
        logger.info("Starting continuous voice listening...")
        
        try:
            while self.is_active:
                await asyncio.sleep(check_interval)
                
                # Check for voice activity in background
                # (would need streaming STT in production)
                
        except KeyboardInterrupt:
            logger.info("Continuous listening interrupted")
        finally:
            self.is_active = False
    
    def set_language(self, language: str) -> bool:
        """Change language for both STT and TTS."""
        success = True
        success = self.stt_engine.set_language(language) and success
        success = self.tts_engine.set_language(language) and success
        
        if success:
            self.language = language
            logger.info(f"Pipeline language changed to {language}")
        
        return success
    
    def get_status(self) -> Dict[str, Any]:
        """Get pipeline status."""
        return {
            "language": self.language,
            "sample_rate": self.sample_rate,
            "is_active": self.is_active,
            "interaction_count": self.interaction_count,
            "last_interaction": self.last_interaction,
            "supported_languages": self.stt_engine.get_supported_languages()
        }
    
    def cleanup(self) -> None:
        """Clean up resources."""
        self.is_active = False
        self.voice_processor.cleanup()
        logger.info("AudioPipeline cleanup complete")
