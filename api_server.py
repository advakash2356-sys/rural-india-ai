"""
REST API Server - Expose all Rural India AI functionality
"""

import asyncio
import logging
import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

# Load environment variables
load_dotenv()

from edge_node.core.orchestrator import EdgeNodeOrchestrator
from edge_node.voice.service import VoiceService
from edge_node.rag.vector_db import VectorDatabase, RAGEngine
from edge_node.agents.domain_agents import AgentOrchestrator
from edge_node.safety.guardrails import GuardrailsEngine, BiasDetector, TrustScore
from edge_node.observability.monitor import MetricsCollector, UsageAnalytics, HealthMonitor, Dashboard

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration from environment
PORT = int(os.getenv("PORT", 8000))
HOST = os.getenv("HOST", "0.0.0.0")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
BETA_MODE = os.getenv("BETA_MODE", "True").lower() == "true"
REQUIRE_CONSENT = os.getenv("REQUIRE_CONSENT", "True").lower() == "true"
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8000").split(",")

# Initialize FastAPI
app = FastAPI(
    title="Rural India AI",
    description="Edge-native AI platform for rural villages",
    version="1.0.0"
)

# Add CORS middleware for cloud deployment
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global components
orchestrator: Optional[EdgeNodeOrchestrator] = None
voice_service: Optional[VoiceService] = None
vector_db: Optional[VectorDatabase] = None
rag_engine: Optional[RAGEngine] = None
agent_orchestrator: Optional[AgentOrchestrator] = None
guardrails: Optional[GuardrailsEngine] = None
bias_detector: Optional[BiasDetector] = None
trust_scorer: Optional[TrustScore] = None
metrics: Optional[MetricsCollector] = None
analytics: Optional[UsageAnalytics] = None
health_monitor: Optional[HealthMonitor] = None
dashboard: Optional[Dashboard] = None


# Request/Response Models
class QueryRequest(BaseModel):
    query: str
    language: Optional[str] = "hi"
    use_rag: bool = True
    use_agents: bool = True


class VoiceQueryRequest(BaseModel):
    duration: float = 5.0
    language: Optional[str] = "hi"


class DocumentRequest(BaseModel):
    text: str
    doc_id: Optional[str] = None
    metadata: Optional[Dict] = None


class LanguageSwitchRequest(BaseModel):
    language: str


# Startup/Shutdown
@app.on_event("startup")
async def startup_event():
    """Initialize all components"""
    global orchestrator, voice_service, vector_db, rag_engine
    global agent_orchestrator, guardrails, bias_detector, trust_scorer
    global metrics, analytics, health_monitor, dashboard
    
    logger.info("Starting Rural India AI Server...")
    
    orchestrator = EdgeNodeOrchestrator()
    startup_ok = await orchestrator.startup()
    
    if not startup_ok:
        logger.error("Failed to start edge node")
        return
    
    voice_service = VoiceService(orchestrator, language='hi')
    vector_db = VectorDatabase()
    rag_engine = RAGEngine(vector_db, orchestrator)
    agent_orchestrator = AgentOrchestrator()
    guardrails = GuardrailsEngine()
    bias_detector = BiasDetector()
    trust_scorer = TrustScore()
    metrics = MetricsCollector()
    analytics = UsageAnalytics()
    health_monitor = HealthMonitor()
    dashboard = Dashboard(metrics, analytics, health_monitor)
    
    logger.info("✓ All components initialized")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down server...")
    if orchestrator:
        await orchestrator.shutdown()
    if voice_service:
        voice_service.cleanup()
    if metrics:
        metrics.export_metrics()
    logger.info("Server shutdown complete")


# ================= PHASE 1: Edge Node APIs =================

@app.get("/api/v1/health")
async def health_check():
    """Get system health status"""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    return await orchestrator.get_health_status()


@app.get("/api/v1/status")
async def system_status():
    """Get detailed system status"""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    try:
        status = {
            "node_id": orchestrator.node_id,
            "is_running": orchestrator.is_running,
            "hardware": orchestrator.hardware_monitor.get_status(),
            "power": orchestrator.power_manager.get_status(),
            "queue": {
                "pending": 0,
                "retrying": 0,
                "synced": 0
            }
        }
        
        # Try to get queue stats if available
        if orchestrator.request_queue:
            try:
                status["queue"]["pending"] = await orchestrator.request_queue.count_pending()
                status["queue"]["retrying"] = await orchestrator.request_queue.count_retrying()
                status["queue"]["synced"] = await orchestrator.request_queue.count_synced()
            except Exception as queue_error:
                logger.warning(f"Could not fetch queue stats: {queue_error}")
        
        return status
    except Exception as e:
        logger.error(f"Status endpoint error: {e}")
        raise HTTPException(status_code=500, detail=f"Status retrieval failed: {str(e)}")


@app.get("/api/v1/hardware")
async def hardware_status():
    """Get hardware metrics"""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    return orchestrator.hardware_monitor.get_status()


@app.get("/api/v1/power")
async def power_status():
    """Get power management status"""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    return orchestrator.power_manager.get_status()


@app.post("/api/v1/sync")
async def trigger_sync():
    """Trigger immediate request queue sync"""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    await orchestrator._sync_pending_requests()
    return {"status": "synced"}


# ================= PHASE 2: Voice APIs =================

@app.post("/api/v2/query")
async def text_query(request: QueryRequest, background_tasks: BackgroundTasks):
    """Process text query (voice will transcribe to this)"""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    try:
        start_time = __import__('time').time()
        query = request.query.strip()
        
        if not query:
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        # Safety check
        try:
            safety_level, issues = guardrails.check_input(query)
            if safety_level.value == "blocked":
                return JSONResponse(
                    status_code=403,
                    content={"error": "Query blocked by safety filters", "issues": issues}
                )
        except Exception as safety_error:
            logger.warning(f"Safety check error: {safety_error}")
            # Continue if safety check fails
        
        # Process query
        try:
            result = await orchestrator.process_local_query(query)
        except Exception as query_error:
            logger.error(f"Query processing error: {query_error}")
            result = {"success": False, "error": str(query_error), "response": "Error processing query"}
        
        # Record analytics
        latency_ms = (__import__('time').time() - start_time) * 1000
        try:
            background_tasks.add_task(
                analytics.record_interaction,
                query, request.language, "general", result.get("success", False), latency_ms
            )
        except Exception as analytics_error:
            logger.warning(f"Analytics error: {analytics_error}")
        
        # Bias check
        try:
            bias = bias_detector.analyze_balance(str(result))
            trust = trust_scorer.compute_score(str(result), has_evidence=True)
        except Exception as scoring_error:
            logger.warning(f"Bias/trust scoring error: {scoring_error}")
            bias = {"likely_bias": False}
            trust = 0.5
        
        return {
            "response": result,
            "safety": safety_level.value if 'safety_level' in locals() else "unchecked",
            "bias_detected": bias.get("likely_bias", False),
            "trust_score": trust,
            "latency_ms": latency_ms
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Query endpoint error: {e}")
        raise HTTPException(status_code=500, detail=f"Query processing failed: {str(e)}")
        
        return {
            "response": result,
            "safety": safety_level.value,
            "bias_detected": bias.get("likely_bias", False),
            "trust_score": trust,
            "latency_ms": latency_ms
        }
        
    except Exception as e:
        logger.error(f"Query processing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v2/voice")
async def voice_interaction(request: VoiceQueryRequest):
    """Process voice query (simulated - real implementation uses audio hardware)"""
    if not voice_service:
        raise HTTPException(status_code=503, detail="Voice service not initialized")
    
    try:
        # Set language
        voice_service.set_language(request.language)
        
        # In production: record actual audio and process
        # For now: return ready status
        return {
            "status": "ready",
            "language": request.language,
            "message": "Voice query Ready (connect microphone for audio input)"
        }
        
    except Exception as e:
        logger.error(f"Voice interaction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v2/languages")
async def supported_languages():
    """Get supported languages"""
    if not voice_service:
        raise HTTPException(status_code=503, detail="Voice service not initialized")
    
    return {
        "languages": voice_service.pipeline.stt_engine.get_supported_languages(),
        "current": voice_service.language
    }


@app.post("/api/v2/language")
async def switch_language(request: LanguageSwitchRequest):
    """Switch voice language"""
    if not voice_service:
        raise HTTPException(status_code=503, detail="Voice service not initialized")
    
    if voice_service.set_language(request.language):
        return {"status": "switched", "language": request.language}
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported language: {request.language}")


# ================= PHASE 3: Vector Database APIs =================

@app.post("/api/v3/documents")
async def add_document(request: DocumentRequest):
    """Add document to vector database"""
    if not vector_db:
        raise HTTPException(status_code=503, detail="Vector DB not initialized")
    
    doc_id = vector_db.add_document(
        text=request.text,
        doc_id=request.doc_id,
        metadata=request.metadata
    )
    
    return {"doc_id": doc_id, "status": "added"}


@app.post("/api/v3/search")
async def search_documents(request: QueryRequest):
    """Search vector database"""
    if not vector_db:
        raise HTTPException(status_code=503, detail="Vector DB not initialized")
    
    results = vector_db.search(request.query, top_k=5)
    
    return {
        "query": request.query,
        "results": [
            {"doc_id": r[0], "similarity": float(r[1]), "text": r[2][:200]}
            for r in results
        ]
    }


@app.get("/api/v3/stats")
async def vector_db_stats():
    """Get vector database statistics"""
    if not vector_db:
        raise HTTPException(status_code=503, detail="Vector DB not initialized")
    
    return vector_db.get_stats()


# ================= PHASE 4: Domain Agents APIs =================

@app.post("/api/v4/agents/query")
async def agent_query(request: QueryRequest):
    """Route query to appropriate domain agent"""
    if not agent_orchestrator:
        raise HTTPException(status_code=503, detail="Agent system not initialized")
    
    result = await agent_orchestrator.route_query(request.query, {})
    
    # Add mandatory disclaimers based on domain (PHASE 3: HARDENED LEGAL UI)
    domain = result.get("domain", "").lower()
    response_text = result.get("response", "")
    
    if domain == "healthcare":
        response_text += "\n\n🛑 DISCLAIMER: I am an AI, not a doctor. Please consult a local medical professional before making health decisions."
    elif domain == "agriculture":
        response_text += "\n\n🛑 DISCLAIMER: This is automated guidance. Verify with a local agricultural expert or KVK (Krishi Vigyan Kendra)."
    
    result["response"] = response_text
    
    # Log interaction for compliance monitoring
    logger.info(f"[BETA] Agent query - Domain: {domain}, ConsentRequired: {REQUIRE_CONSENT}")
    
    return result


@app.get("/api/v4/agents")
async def list_agents():
    """List available domain agents"""
    if not agent_orchestrator:
        raise HTTPException(status_code=503, detail="Agent system not initialized")
    
    return {
        "agents": agent_orchestrator.get_agents_info(),
        "count": len(agent_orchestrator.agents)
    }


# ================= PHASE 5: Safety APIs =================

@app.post("/api/v5/safety/check")
async def safety_check(request: QueryRequest):
    """Check text for safety issues"""
    if not guardrails:
        raise HTTPException(status_code=503, detail="Safety system not initialized")
    
    safety_level, issues = guardrails.check_input(request.query)
    bias = bias_detector.analyze_balance(request.query)
    
    return {
        "safety_level": safety_level.value,
        "issues": issues,
        "bias_analysis": bias,
        "stats": guardrails.get_stats()
    }


@app.post("/api/v5/trust/score")
async def trust_score(request: QueryRequest):
    """Calculate trust score for a response"""
    if not trust_scorer:
        raise HTTPException(status_code=503, detail="Trust system not initialized")
    
    score = trust_scorer.compute_score(request.query)
    
    return {
        "text": request.query[:100],
        "trust_score": score,
        "confidence": "high" if score > 0.7 else "medium" if score > 0.4 else "low"
    }


# ================= PHASE 6: Observability APIs =================

@app.get("/api/v6/dashboard")
async def get_dashboard():
    """Get complete dashboard data"""
    if not dashboard:
        raise HTTPException(status_code=503, detail="Dashboard not initialized")
    
    return dashboard.get_dashboard_data()


@app.get("/api/v6/metrics")
async def get_metrics():
    """Get metrics summary"""
    if not metrics:
        raise HTTPException(status_code=503, detail="Metrics not initialized")
    
    return {
        "inference": metrics.get_summary("inference_latency", minutes=60),
        "requests": metrics.get_summary("request_latency", minutes=60)
    }


@app.get("/api/v6/analytics")
async def get_analytics():
    """Get usage analytics"""
    if not analytics:
        raise HTTPException(status_code=503, detail="Analytics not initialized")
    
    return analytics.get_usage_summary()


@app.get("/api/v6/health")
async def detailed_health():
    """Get detailed health status"""
    if not health_monitor or not orchestrator:
        raise HTTPException(status_code=503, detail="Health monitor not initialized")
    
    return await health_monitor.check_health(orchestrator)


@app.get("/api/v6/export/metrics")
async def export_metrics():
    """Export metrics as JSON file"""
    if not metrics:
        raise HTTPException(status_code=503, detail="Metrics not initialized")
    
    try:
        from pathlib import Path
        metrics_file = Path("data/metrics/metrics.json")
        
        if metrics_file.exists():
            return FileResponse(
                path=metrics_file,
                media_type="application/json",
                filename="rural-india-ai-metrics.json"
            )
        else:
            raise HTTPException(status_code=404, detail="Metrics file not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ================= Root Endpoints =================

@app.get("/ui")
async def serve_ui():
    """Serve the beta UI with consent modal"""
    try:
        from pathlib import Path
        ui_file = Path(__file__).parent / "index.html"
        return FileResponse(ui_file, media_type="text/html")
    except Exception as e:
        logger.error(f"Failed to serve UI: {e}")
        raise HTTPException(status_code=500, detail="UI not available")


@app.get("/")
async def root(request=None):
    """Welcome endpoint - serves UI if accessed from browser, JSON if API"""
    # Check if request asks for HTML (from browser)
    try:
        from pathlib import Path
        ui_file = Path(__file__).parent / "index.html"
        if ui_file.exists():
            # Return HTML for browser access
            return FileResponse(ui_file, media_type="text/html")
    except:
        pass
    
    # Fall back to JSON API response
    return {
        "name": "Rural India AI",
        "version": "1.0.0",
        "status": "operational" if orchestrator and orchestrator.is_running else "initializing",
        "docs": "/docs",
        "ui": "/ui",
        "beta": True,
        "compliance": {
            "consent_required": REQUIRE_CONSENT,
            "disclosures": [
                "Experimental system (As-Is)",
                "Not professional advice",
                "Limitation of liability",
                "Data monitoring for safety",
                "Indian jurisdiction"
            ]
        },
        "api_endpoints": {
            "phase_1": "/api/v1/health, /api/v1/status, /api/v1/hardware, /api/v1/power",
            "phase_2": "/api/v2/query, /api/v2/voice, /api/v2/languages",
            "phase_3": "/api/v3/documents, /api/v3/search, /api/v3/stats",
            "phase_4": "/api/v4/agents/query, /api/v4/agents",
            "phase_5": "/api/v5/safety/check, /api/v5/trust/score",
            "phase_6": "/api/v6/dashboard, /api/v6/metrics, /api/v6/analytics, /api/v6/health"
        }
    }


@app.get("/docs")
async def api_docs():
    """API documentation"""
    return {
        "title": "Rural India AI API",
        "version": "1.0.0",
        "endpoints": {
            "health": {"path": "/api/v1/health", "method": "GET", "description": "System health check"},
            "query": {"path": "/api/v2/query", "method": "POST", "description": "Process text query"},
            "search": {"path": "/api/v3/search", "method": "POST", "description": "Search documents"},
            "agents": {"path": "/api/v4/agents/query", "method": "POST", "description": "Query domain agents"},
            "safety": {"path": "/api/v5/safety/check", "method": "POST", "description": "Check safety"},
            "dashboard": {"path": "/api/v6/dashboard", "method": "GET", "description": "Get dashboard"}
        },
        "full_docs": "/docs (OpenAPI)"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
