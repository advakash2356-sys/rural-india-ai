"""
Edge Node Orchestrator - Central controller for villages edge computing node.
Coordinates model loading, async queuing, hardware monitoring, and connectivity.
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path

from edge_node.hardware.monitor import HardwareMonitor
from edge_node.hardware.power import PowerManager
from edge_node.models.manager import QuantizedModelManager
from edge_node.queue.async_queue import AsyncRequestQueue
from edge_node.networking.mqtt_client import MQTTClient
from edge_node.config.settings import EdgeConfig

logger = logging.getLogger(__name__)


class EdgeNodeOrchestrator:
    """
    Main orchestrator for edge node operations.
    
    Responsibilities:
    - Initialize all subsystems (hardware, models, queue, network)
    - Monitor edge node health and resource constraints
    - Manage asynchronous request queuing and forwarding
    - Handle graceful degradation during connectivity loss
    - Execute local inference on quantized models
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the edge node orchestrator.
        
        Args:
            config_path: Path to edge node configuration file
        """
        self.config = EdgeConfig.load(config_path)
        self.node_id = self.config.node_id
        self.is_running = False
        self.startup_time = None
        
        # Initialize subsystems
        self.hardware_monitor = HardwareMonitor(
            thermal_threshold_celsius=self.config.thermal_threshold,
            memory_threshold_percent=self.config.memory_threshold
        )
        self.power_manager = PowerManager(
            solar_mode=self.config.has_solar,
            battery_low_threshold=self.config.battery_low_threshold
        )
        self.model_manager = QuantizedModelManager(
            models_dir=Path(self.config.models_path),
            max_memory_mb=self.config.max_model_memory_mb
        )
        self.request_queue = AsyncRequestQueue(
            db_path=self.config.queue_db_path,
            max_queue_size=self.config.max_queue_size
        )
        self.mqtt_client = MQTTClient(
            broker_address=self.config.mqtt_broker,
            port=self.config.mqtt_port,
            client_id=self.node_id,
            topics=self.config.mqtt_topics
        )
        
        logger.info(f"EdgeNodeOrchestrator initialized for node: {self.node_id}")
    
    async def startup(self) -> bool:
        """
        Perform startup sequence for the edge node.
        
        Returns:
            True if startup successful, False otherwise
        """
        try:
            logger.info(f"Starting edge node {self.node_id}...")
            self.startup_time = datetime.utcnow()
            
            # Initialize MQTT connection
            await self.mqtt_client.connect()
            logger.info("MQTT connection established")
            
            # Load quantized models
            loaded_models = await self.model_manager.load_default_models()
            logger.info(f"Loaded {len(loaded_models)} quantized models: {loaded_models}")
            
            # Check hardware status
            hw_status = self.hardware_monitor.get_status()
            temp_str = f"{hw_status['temperature_celsius']:.1f}°C" if hw_status['temperature_celsius'] is not None else "N/A"
            logger.info(f"Hardware status - CPU: {hw_status['cpu_percent']}%, "
                       f"Memory: {hw_status['memory_percent']}%, "
                       f"Temp: {temp_str}")
            
            # Check power status
            power_status = self.power_manager.get_status()
            logger.info(f"Power status - Battery: {power_status['battery_percent']}%, "
                       f"Solar: {power_status['solar_watts']:.1f}W, "
                       f"Mode: {power_status['power_mode']}")
            
            # Restore and sync any pending requests from queue
            pending_count = await self.request_queue.count_pending()
            logger.info(f"Found {pending_count} pending requests in queue")
            
            self.is_running = True
            logger.info(f"Edge node {self.node_id} startup complete")
            return True
            
        except Exception as e:
            logger.error(f"Startup failed: {e}")
            return False
    
    async def shutdown(self) -> None:
        """Perform graceful shutdown of the edge node."""
        try:
            logger.info(f"Shutting down edge node {self.node_id}...")
            self.is_running = False
            
            # Persist any in-flight requests to queue
            await self.request_queue.flush()
            logger.info("Request queue flushed")
            
            # Disconnect MQTT
            await self.mqtt_client.disconnect()
            logger.info("MQTT disconnected")
            
            logger.info(f"Edge node {self.node_id} shutdown complete")
        except Exception as e:
            logger.error(f"Shutdown error: {e}")
    
    async def process_local_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process a query using local quantized models (no cloud dependency).
        
        Args:
            query: Input query text
            context: Optional contextual data
            
        Returns:
            Response dictionary with answer and metadata
        """
        try:
            # Check hardware constraints before inference
            hw_status = self.hardware_monitor.get_status()
            if hw_status['cpu_percent'] > 85:
                logger.warning("CPU utilization high - deferring inference")
                return {
                    "error": "Device busy, please try again",
                    "status": "deferred",
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            # Execute inference on quantized model
            result = await self.model_manager.infer(
                query=query,
                context=context or {}
            )
            
            logger.info(f"Local inference complete: {result.get('model_id')} tokens: {result.get('tokens_used')}")
            return result
            
        except Exception as e:
            logger.error(f"Inference error: {e}")
            return {"error": str(e), "status": "failed"}
    
    async def queue_cloud_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Queue a request for cloud synchronization when connectivity available.
        Implements Store-and-Forward protocol.
        
        Args:
            request_data: Request to queue
            
        Returns:
            Queue response with request_id
        """
        try:
            request_id = await self.request_queue.enqueue(request_data)
            logger.info(f"Request queued: {request_id}")
            
            # Attempt immediate send if connection available
            if await self.mqtt_client.is_connected_async():
                await self._sync_pending_requests()
            
            return {
                "status": "queued",
                "request_id": request_id,
                "will_sync": await self.mqtt_client.is_connected_async()
            }
            
        except Exception as e:
            logger.error(f"Queue error: {e}")
            return {"status": "error", "error": str(e)}
    
    async def _sync_pending_requests(self) -> None:
        """
        Sync all pending requests to cloud when connectivity available.
        Implements opportunistic networking.
        """
        try:
            pending = await self.request_queue.get_pending(limit=10)
            
            for req in pending:
                success = await self.mqtt_client.publish(
                    topic=self.config.mqtt_topics['requests'],
                    payload=req
                )
                
                if success:
                    await self.request_queue.mark_synced(req['id'])
                    logger.info(f"Synced request: {req['id']}")
                else:
                    logger.warning(f"Failed to sync request: {req['id']}")
                    break
                    
        except Exception as e:
            logger.error(f"Sync error: {e}")
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status of the edge node."""
        hw_status = self.hardware_monitor.get_status()
        power_status = self.power_manager.get_status()
        queue_status = await self.request_queue.get_status()
        mqtt_status = await self.mqtt_client.get_status()
        
        return {
            "node_id": self.node_id,
            "is_running": self.is_running,
            "uptime_seconds": (datetime.utcnow() - self.startup_time).total_seconds() if self.startup_time else 0,
            "hardware": hw_status,
            "power": power_status,
            "queue": queue_status,
            "connectivity": mqtt_status,
            "timestamp": datetime.utcnow().isoformat()
        }
