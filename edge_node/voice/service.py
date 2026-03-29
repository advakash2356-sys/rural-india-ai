"""
Voice Service - Integrates voice interface with edge orchestrator
Phase 2 Feature
"""

import asyncio
import logging
from typing import Optional, Dict, Any
from pathlib import Path

from edge_node.voice import AudioPipeline

logger = logging.getLogger(__name__)


class VoiceService:
    """
    Voice service for the edge node.
    
    Integrates with the EdgeNodeOrchestrator to:
    - Accept voice queries in Indic languages
    - Process through local AI models
    - Return voice responses
    
    Designed for low-resource devices with intermittent connectivity.
    """
    
    def __init__(self,
                 orchestrator,
                 language: str = 'hi',
                 auto_playback: bool = True,
                 save_interactions: bool = False):
        """
        Initialize voice service.
        
        Args:
            orchestrator: EdgeNodeOrchestrator instance
            language: Default language code
            auto_playback: Automatically play responses
            save_interactions: Save audio interactions
        """
        self.orchestrator = orchestrator
        self.language = language
        self.auto_playback = auto_playback
        self.save_interactions = save_interactions
        
        # Create interaction directory
        self.interaction_dir = Path('data/interactions')
        if save_interactions:
            self.interaction_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize audio pipeline
        self.pipeline = AudioPipeline(
            language=language,
            sample_rate=16000,
            auto_playback=auto_playback,
            inference_callback=self._process_query
        )
        
        logger.info(f"VoiceService initialized for {language}")
    
    async def _process_query(self, text: str) -> Dict[str, str]:
        """
        Process transcribed text through inference.
        
        Args:
            text: Transcribed query text
            
        Returns:
            Response with generated text
        """
        try:
            logger.info(f"Processing query: {text[:50]}...")
            
            # Use orchestrator's local inference
            result = await self.orchestrator.process_local_query(text)
            
            if result.get("error"):
                response = f"क्षमा करें, मुझे समझ नहीं आया। कृपया दोबारा कहें।"  # Hindi fallback
                if self.language == 'ta':
                    response = "மன்னிக்கவும், நான் புரிந்துகொள்ளவில்லை. தயவுசெய்து மீண்டும் சொல்லுங்கள்."
                elif self.language == 'en':
                    response = "Sorry, I didn't understand. Please try again."
            else:
                response = result.get("response", "Query processed")
            
            return {
                "response": response,
                "successful": True
            }
            
        except Exception as e:
            logger.error(f"Query processing failed: {e}")
            return {
                "response": "गलती हुई, कृपया दोबारा कोशिश करें।",  # Hindi fallback
                "successful": False,
                "error": str(e)
            }
    
    async def handle_voice_interaction(self, 
                                      duration: float = 5.0) -> Dict[str, Any]:
        """
        Handle complete voice interaction.
        
        Args:
            duration: Recording duration in seconds
            
        Returns:
            Complete interaction result
        """
        logger.info("Starting voice interaction...")
        
        try:
            # Process through pipeline
            result = await self.pipeline.process_voice_query(
                duration=duration,
                save_audio=self.save_interactions
            )
            
            # Save interaction if enabled
            if self.save_interactions and result.get("success"):
                await self._save_interaction(result)
            
            return result
            
        except Exception as e:
            logger.error(f"Voice interaction failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _save_interaction(self, result: Dict[str, Any]) -> None:
        """Save interaction details."""
        try:
            import json
            
            filename = self.interaction_dir / f"interaction_{self.pipeline.interaction_count}.json"
            
            with open(filename, 'w') as f:
                json.dump(result, f, indent=2)
            
            logger.info(f"Interaction saved: {filename}")
            
        except Exception as e:
            logger.warning(f"Failed to save interaction: {e}")
    
    def set_language(self, language: str) -> bool:
        """Change language for voice service."""
        if self.pipeline.set_language(language):
            self.language = language
            logger.info(f"Voice service language changed to {language}")
            return True
        return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get voice service status."""
        pipeline_status = self.pipeline.get_status()
        
        return {
            "service": "voice",
            "enabled": True,
            "language": self.language,
            **pipeline_status
        }
    
    async def test_audio_setup(self) -> Dict[str, Any]:
        """Test audio setup (record and playback)."""
        logger.info("Testing audio setup...")
        
        try:
            # Record brief audio
            logger.info("Recording test audio...")
            audio_data = self.pipeline.voice_processor.record_audio(2.0)
            
            if audio_data is None:
                return {
                    "success": False,
                    "error": "Failed to record audio"
                }
            
            # Check voice activity
            has_voice, energy = self.pipeline.voice_processor.detect_voice_activity(audio_data)
            
            # Playback test
            logger.info("Playing back test audio...")
            playback_ok = self.pipeline.voice_processor.playback_audio(audio_data)
            
            return {
                "success": playback_ok,
                "recorded_samples": len(audio_data),
                "voice_detected": has_voice,
                "energy": float(energy),
                "playback": "success" if playback_ok else "failed"
            }
            
        except Exception as e:
            logger.error(f"Audio test failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def cleanup(self) -> None:
        """Clean up voice service resources."""
        self.pipeline.cleanup()
        logger.info("VoiceService cleanup complete")
