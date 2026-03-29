"""
Main entry point for Rural India AI Edge Node
Phase 1: Edge-Native Infrastructure
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from edge_node.core.orchestrator import EdgeNodeOrchestrator
from edge_node.config.settings import EdgeConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def main():
    """Main application entry point."""
    try:
        logger.info("=" * 60)
        logger.info("Rural India AI - Edge Node (Phase 1)")
        logger.info("=" * 60)
        
        # Initialize configuration
        config_file = Path("config/edge_config.json")
        config = EdgeConfig.load(str(config_file) if config_file.exists() else None)
        logger.info(f"\n{config}\n")
        
        # Initialize orchestrator
        orchestrator = EdgeNodeOrchestrator(str(config_file) if config_file.exists() else None)
        
        # Startup
        startup_success = await orchestrator.startup()
        if not startup_success:
            logger.error("Edge node startup failed")
            return 1
        
        # Get health status
        health = await orchestrator.get_health_status()
        logger.info(f"Health Status:\n{health}\n")
        
        # Process sample local query
        logger.info("Testing local inference...")
        result = await orchestrator.process_local_query(
            "मेरी फसल में कीटों का संक्रमण है। क्या करूं?",  # Hindi: crop pest infection
            context={"crop": "wheat", "location": "village_001"}
        )
        logger.info(f"Inference result: {result}\n")
        
        # Test async queuing
        logger.info("Testing request queuing...")
        queue_result = await orchestrator.queue_cloud_request({
            "type": "PM_KISAN_CHECK",
            "user_id": "user_123",
            "priority": 1
        })
        logger.info(f"Queue result: {queue_result}\n")
        
        # Graceful shutdown
        await orchestrator.shutdown()
        
        logger.info("Edge node execution complete")
        return 0
        
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
