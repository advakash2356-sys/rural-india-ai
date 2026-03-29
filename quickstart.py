#!/usr/bin/env python3
"""
Quick Start Guide - Rural India AI Edge Node (Phase 1)

This script demonstrates basic usage of the edge node framework.
Run with: python3 quickstart.py
"""

import asyncio
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """Demo of key Phase 1 features."""
    
    print("\n" + "="*70)
    print("Rural India AI - Phase 1 Edge Node Quickstart")
    print("="*70 + "\n")
    
    # Demo 1: Configuration
    print("📋 DEMO 1: Edge Node Configuration")
    print("-" * 70)
    
    from edge_node.config.settings import EdgeConfig
    
    config = EdgeConfig()
    config.node_id = "demo_village_001"
    config.language = "hi"
    print(f"{config}\n")
    
    # Demo 2: Hardware Monitoring
    print("\n📊 DEMO 2: Hardware Monitoring")
    print("-" * 70)
    
    from edge_node.hardware.monitor import HardwareMonitor
    
    hw_monitor = HardwareMonitor(thermal_threshold=75)
    hw_status = hw_monitor.get_status()
    print(f"CPU Usage: {hw_status['cpu_percent']:.1f}%")
    print(f"Memory Usage: {hw_status['memory_percent']:.1f}%")
    print(f"Temperature: {hw_status.get('temperature_celsius', 'N/A')}°C")
    print(f"Alerts: {hw_status.get('alerts', [])}\n")
    
    # Demo 3: Power Management
    print("\n⚡ DEMO 3: Power Management (Solar/Battery)")
    print("-" * 70)
    
    from edge_node.hardware.power import PowerManager
    
    power_mgr = PowerManager(solar_mode=True, battery_low_threshold=20)
    
    # Test different battery states
    for battery_level in [100, 50, 20]:
        power_mgr.set_battery_percent(battery_level)
        power_mgr.set_solar_input(250.0 if battery_level > 50 else 50.0)
        status = power_mgr.get_status()
        print(f"Battery {battery_level}%: Mode={status['power_mode']}, "
              f"Solar={status['solar_watts']:.0f}W")
    print()
    
    # Demo 4: Quantized Models
    print("\n🤖 DEMO 4: Quantized Model Management")
    print("-" * 70)
    
    from edge_node.models.loader import ModelLoader
    
    available_models = [
        {"name": "sarvam-2b-indic-quantized-gguf", "desc": "2B params, Indic, 4-bit"},
        {"name": "llama-3-8b-indic-quantized-q4", "desc": "8B params, Requires 8GB Pi"},
        {"name": "mobilebert-indic-lightweight", "desc": "110M params, Fast classifier"}
    ]
    
    print("Available Quantized Models:")
    for model in available_models:
        est_mem = ModelLoader.get_model_memory_estimate(
            model_size_mb=1000,
            quantization="q4_0"
        )
        print(f"  • {model['name']}: {model['desc']}")
        print(f"    → Est. Runtime Memory: {est_mem:.0f}MB")
    print()
    
    # Demo 5: Async Request Queue
    print("\n📬 DEMO 5: Async Request Queue (Store-and-Forward)")
    print("-" * 70)
    
    from edge_node.queue.async_queue import AsyncRequestQueue
    
    queue = AsyncRequestQueue(db_path=":memory:")  # In-memory for demo
    
    # Queue some requests
    requests = [
        {"type": "PM_KISAN_CHECK", "priority": 2},
        {"type": "NREGA_STATUS", "priority": 1},
        {"type": "HEALTH_TRIAGE", "priority": 1}
    ]
    
    for req in requests:
        req_id = await queue.enqueue(req)
        logger.info(f"Queued: {req['type']} → ID: {req_id}")
    
    # Check queue status
    status = await queue.get_status()
    print(f"\nQueue Status:")
    print(f"  Pending: {status['pending']}")
    print(f"  Total: {status['total']}\n")
    
    # Demo 6: Local Inference (Placeholder)
    print("\n🧠 DEMO 6: Local Inference (Quantized Model)")
    print("-" * 70)
    
    from edge_node.models.manager import QuantizedModelManager
    
    model_mgr = QuantizedModelManager(models_dir=Path("./models"), max_memory_mb=1800)
    
    # Demonstrate inference API (actual inference requires GGUF models)
    test_query = "मेरी गेहूं की फसल में कीटों का संक्रमण है। क्या करूं?"
    print(f"Query: {test_query}")
    
    result = await model_mgr.infer(test_query, context={"crop": "wheat"})
    print(f"Response: {result.get('response', 'Model not loaded (expected for demo)')}")
    print(f"Model: {result.get('model_id', 'N/A')}\n")
    
    # Demo 7: MQTT Connectivity
    print("\n🌐 DEMO 7: MQTT Opportunistic Networking")
    print("-" * 70)
    
    from edge_node.networking.mqtt_client import MQTTClient
    
    mqtt_client = MQTTClient(
        broker_address="mqtt.example.com",
        port=1883,
        client_id="demo_village_001"
    )
    
    status = await mqtt_client.get_status()
    print(f"MQTT Status:")
    print(f"  Broker: {status['broker']}")
    print(f"  Connected: {status['connected']}")
    print(f"  Buffered Messages: {status['buffered_messages']}\n")
    
    # Demo 8: Complete Orchestration
    print("\n🎭 DEMO 8: Complete EdgeNodeOrchestrator")
    print("-" * 70)
    
    from edge_node.core.orchestrator import EdgeNodeOrchestrator
    
    print("Initializing edge node orchestrator...")
    orch = EdgeNodeOrchestrator()
    
    print("✅ Phase 1 Components Ready:")
    print("  ✓ Device health monitoring")
    print("  ✓ Power management")
    print("  ✓ Quantized model loading")
    print("  ✓ Async request queuing")
    print("  ✓ Opportunistic networking")
    print("  ✓ Configuration management")
    print("\n")
    
    # Summary
    print("\n" + "="*70)
    print("QUICKSTART SUMMARY")
    print("="*70)
    
    print("""
Phase 1: Edge-Native Infrastructure ✅

Key Capabilities Demonstrated:
1. Edge Configuration Management
2. Hardware Monitoring (CPU/Memory/Temperature)
3. Power Management (Solar/Battery modes)
4. Quantized Model Framework (GGUF)
5. Async Request Queue (SQLite + MQTT)
6. Opportunistic Networking
7. Orchestrated Edge Node Control

Next Steps:
├─ Deploy to Raspberry Pi: bash deployment/install_alpine.sh
├─ Configure for your village: edit deployment/example_village_config.json
├─ Start service: rc-service rural-ai-edge start
├─ Monitor health: curl http://localhost:8000/health
└─ Test inference: curl -X POST http://localhost:8000/infer

Phase 2-6 Roadmap:
→ Phase 2: Voice-First Interface (WhatsApp, IVR, Indic ASR/TTS)
→ Phase 3: Local Data Ingestion (Vector DB, RAG, India Stack)
→ Phase 4: Domain Agents (Krishi, Asha, Yojana, Sahukar)
→ Phase 5: Trust & Guardrails (Consent, Misinformation filters)
→ Phase 6: Deployment & Scaling (OTA updates, dashboards)

For more info, see:
  - README.md: Project overview
  - docs/PHASE1_ARCHITECTURE.md: Technical design
  - docs/DEPLOYMENT_GUIDE.md: Production deployment
  - CONTRIBUTING.md: How to extend

Happy building! 🚀
""")
    print("="*70 + "\n")


if __name__ == "__main__":
    print("Starting quickstart demo...\n")
    asyncio.run(main())
    print("✅ Quickstart complete!")
