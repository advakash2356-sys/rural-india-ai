"""
Phase 2 Voice Demo - Test voice interface with edge node
"""

import asyncio
import logging
from pathlib import Path

from edge_node.core.orchestrator import EdgeNodeOrchestrator
from edge_node.voice.service import VoiceService

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def main():
    """Run voice interface demo."""
    
    logger.info("=" * 60)
    logger.info("Rural India AI - Phase 2 Voice Interface Demo")
    logger.info("=" * 60)
    
    # Initialize orchestrator (Phase 1)
    orchestrator = EdgeNodeOrchestrator()
    
    # Start edge node
    startup_ok = await orchestrator.startup()
    if not startup_ok:
        logger.error("Failed to start edge node")
        return
    
    try:
        # Initialize voice service (Phase 2)
        logger.info("\nInitializing voice service...")
        voice_service = VoiceService(
            orchestrator=orchestrator,
            language='hi',
            auto_playback=True,
            save_interactions=True
        )
        
        # Print status
        status = voice_service.get_status()
        logger.info(f"\nVoice Service Status:")
        for key, value in status.items():
            logger.info(f"  {key}: {value}")
        
        # Test audio setup
        logger.info("\n" + "=" * 60)
        logger.info("Testing audio setup...")
        logger.info("=" * 60)
        
        audio_test = await voice_service.test_audio_setup()
        logger.info(f"\nAudio Test Results:")
        for key, value in audio_test.items():
            logger.info(f"  {key}: {value}")
        
        if not audio_test.get("success"):
            logger.warning("Audio setup test failed - PyAudio may not be available")
            logger.info("(This is expected on systems without microphone/speaker)")
        
        # Simulate voice interaction (without actual audio)
        logger.info("\n" + "=" * 60)
        logger.info("Simulating voice interaction...")
        logger.info("=" * 60)
        
        # Since we can't actually record audio in all environments,
        # we'll demonstrate the text processing part
        logger.info("\nProcessing sample query through inference...")
        
        sample_query = "नमस्ते, आज का मौसम कैसा है?"  # "Hello, what is today's weather?"
        logger.info(f"Query: {sample_query}")
        
        inference_result = await orchestrator.process_local_query(sample_query)
        logger.info(f"Inference Result: {inference_result}")
        
        # Show language support
        logger.info("\n" + "=" * 60)
        logger.info("Supported Languages & Features")
        logger.info("=" * 60)
        
        supported = voice_service.pipeline.stt_engine.get_supported_languages()
        logger.info("\nSupported Languages:")
        for lang_code, lang_name in supported.items():
            logger.info(f"  {lang_code}: {lang_name}")
        
        # Demonstrate language switching
        logger.info("\nDemonstrating language switching...")
        
        for test_lang in ['hi', 'ta', 'en']:
            voice_service.set_language(test_lang)
            status = voice_service.get_status()
            logger.info(f"  Switched to: {status['language']}")
        
        # Reset to Hindi
        voice_service.set_language('hi')
        
        logger.info("\n" + "=" * 60)
        logger.info("Phase 2 Demo Complete")
        logger.info("=" * 60)
        logger.info("\nKey Features Implemented:")
        logger.info("  ✓ Speech-to-Text (Indic languages)")
        logger.info("  ✓ Text-to-Speech (Indic languages)")
        logger.info("  ✓ Audio Pipeline orchestration")
        logger.info("  ✓ Voice Activity Detection")
        logger.info("  ✓ Multi-language support")
        logger.info("  ✓ Edge device optimization")
        
        logger.info("\nNext Steps:")
        logger.info("  - Train on Indic language models")
        logger.info("  - Deploy on Raspberry Pi hardware")
        logger.info("  - Test with real audio input")
        logger.info("  - Phase 3: Vector databases & RAG")
        
    finally:
        # Cleanup
        logger.info("\nCleaning up...")
        await orchestrator.shutdown()
        logger.info("Demo complete")


if __name__ == "__main__":
    asyncio.run(main())
