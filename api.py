"""
FastAPI service wrapper for edge node orchestrator.
Provides HTTP API for testing and debugging (when connectivity available).
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import asyncio
import logging

from edge_node.core.orchestrator import EdgeNodeOrchestrator
from edge_node.config.settings import EdgeConfig

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Rural India AI - Edge Node API",
    description="Phase 1: Edge-Native Infrastructure",
    version="0.1.0"
)

# Global orchestrator instance
orchestrator: Optional[EdgeNodeOrchestrator] = None


class QueryRequest(BaseModel):
    """Request model for local inference."""
    query: str
    context: Optional[dict] = None


class AsyncRequestPayload(BaseModel):
    """Model for cloud-sync request."""
    request_type: str
    data: dict
    priority: int = 0


@app.on_event("startup")
async def startup_event():
    """Initialize edge node on app startup."""
    global orchestrator
    try:
        orchestrator = EdgeNodeOrchestrator()
        success = await orchestrator.startup()
        if not success:
            logger.error("Edge node startup failed")
    except Exception as e:
        logger.error(f"Startup error: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Graceful shutdown."""
    global orchestrator
    if orchestrator:
        await orchestrator.shutdown()


@app.get("/health")
async def health_check():
    """Get edge node health status."""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Edge node not initialized")
    
    health = await orchestrator.get_health_status()
    return JSONResponse(health)


@app.post("/infer")
async def local_inference(request: QueryRequest):
    """Run local inference on quantized model."""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Edge node not initialized")
    
    result = await orchestrator.process_local_query(request.query, request.context)
    return JSONResponse(result)


@app.post("/queue")
async def queue_request(request: AsyncRequestPayload):
    """Queue request for cloud synchronization."""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Edge node not initialized")
    
    result = await orchestrator.queue_cloud_request({
        "type": request.request_type,
        "data": request.data,
        "priority": request.priority
    })
    return JSONResponse(result)


@app.get("/queue/status")
async def queue_status():
    """Get async queue status."""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Edge node not initialized")
    
    status = await orchestrator.request_queue.get_status()
    return JSONResponse(status)


@app.get("/models")
async def list_models():
    """List loaded quantized models."""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Edge node not initialized")
    
    memory_usage = orchestrator.model_manager.get_memory_usage()
    return JSONResponse(memory_usage)


@app.get("/config")
async def get_config():
    """Get current edge node configuration."""
    config = EdgeConfig.load()
    return JSONResponse({
        "node_id": config.node_id,
        "hardware_profile": config.hardware_profile,
        "location": config.location,
        "connectivity": {
            "mqtt_broker": config.mqtt_broker,
            "mqtt_port": config.mqtt_port
        }
    })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
