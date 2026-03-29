# Rural India AI Edge Node - Phase 1
# Edge-Native Infrastructure Deployment

## Quick Start

```bash
# Install dependencies
pip install -e .

# Run edge node
python main.py

# Start FastAPI service
uvicorn api:app --host 0.0.0.0 --port 8000
```

## Project Structure

```
rural-india-ai/
├── edge-node/
│   ├── core/               # Orchestration & state management
│   ├── models/             # Quantized LLM management
│   ├── queue/              # Async request queuing (SQLite)
│   ├── hardware/           # Power & thermal monitoring
│   ├── networking/         # MQTT client for opportunistic networking
│   └── config/             # Configuration management
├── deployment/             # Deployment scripts and configs
├── docs/                   # Architecture & implementation docs
├── main.py                 # CLI entry point
├── api.py                  # FastAPI HTTP service
├── setup.py                # Package configuration
└── requirements.txt        # Dependencies
```

## Phase 1: Edge-Native Infrastructure

### 1. **EdgeNodeOrchestrator** (`core/orchestrator.py`)
- Central controller for village edge nodes
- Coordinates: hardware monitoring, model loading, async queuing, connectivity
- Manages graceful degradation during connectivity loss
- Implements local inference on quantized models

### 2. **QuantizedModelManager** (`models/manager.py`)
- Loads GGUF-format quantized Indic SLMs (Sarvam 2B, Llama-3 8B)
- Manages memory constraints (max 2GB on Raspberry Pi)
- Handles model versioning and hot-swapping
- Tracks inference statistics per model

### 3. **AsyncRequestQueue** (`queue/async_queue.py`)
- SQLite-backed persistent queue for store-and-forward
- Implements MQTT QoS 2 (exactly-once) semantics
- Priority-based request ordering
- Automatic retry logic with exponential backoff

### 4. **HardwareMonitor** (`hardware/monitor.py`)
- Tracks CPU, memory, temperature, disk usage
- Thermal throttling detection (75°C threshold)
- Power-aware performance recommendations
- Designed for 45°C+ ambient temps

### 5. **PowerManager** (`hardware/power.py`)
- Solar panel & battery level tracking
- Three power modes: full, reduced, low-power
- Charging schedule optimization
- Energy budget requests for tasks

### 6. **MQTTClient** (`networking/mqtt_client.py`)
- Opportunistic MQTT connectivity (QoS 2)
- Store-and-forward message buffering
- Bandwidth-aware compression
- Graceful degradation during 2G/3G dropouts

### 7. **EdgeConfig** (`config/settings.py`)
- Centralized configuration management
- Hardware profiles (Raspi 5, Mini PC server, etc.)
- Location-aware settings (village, state, language)
- Deployment-time customization

## Configuration Example

```json
{
  "node_id": "edge_village_001",
  "hardware_profile": "raspi5-4gb",
  "location": {
    "state": "Uttar Pradesh",
    "gram_panchayat": "Example Village",
    "lat": 25.5,
    "lon": 82.0
  },
  "language": "hi",
  "mqtt_broker": "cloud.example.com",
  "has_solar": true,
  "battery_low_threshold": 20.0
}
```

## API Endpoints

### Health & Status
- `GET /health` - Edge node health status
- `GET /config` - Current configuration
- `GET /models` - Loaded models & memory usage
- `GET /queue/status` - Async queue statistics

### Inference
- `POST /infer` - Run local inference (no cloud)
  ```json
  {
    "query": "मेरी फसल में कीटों का संक्रमण है?",
    "context": {"crop": "wheat"}
  }
  ```

### Cloud Sync
- `POST /queue` - Queue request for cloud sync
  ```json
  {
    "request_type": "PM_KISAN_CHECK",
    "data": {"user_id": "xyz"},
    "priority": 1
  }
  ```

## Key Features

✅ **Edge-Native Inference** - No cloud dependency for local queries
✅ **Intermittent Connectivity** - Store-and-forward with MQTT QoS 2
✅ **Power-Aware** - Solar/battery management & thermal throttling
✅ **Quantized Models** - GGUF format, 4-bit precision for 2GB limit
✅ **Async Everywhere** - SQLite queue, MQTT, async Python/FastAPI
✅ **Graceful Degradation** - Works offline, syncs opportunistically

## Monitoring Telemetry

Distributed telemetry protocol sends daily batches:
- CPU/Memory/Thermal metrics
- Battery & solar input
- Queue statistics
- Inference latency
- Network connectivity events

## Planned for Phase 2-6

- Voice-first WhatsApp/IVR interface
- Indic ASR & TTS (Bhashini integration)
- Vector DB (ChromaDB) for local RAG
- Domain-specific agents (Krishi, Asha, Yojana, Sahukar)
- Misinformation detection & consent engineering
- OTA model updates & self-healing

## Architecture Diagram

```
┌─────────────────────────────────────┐
│  Voice User (WhatsApp/Feature Phone)│
└─────────────┬───────────────────────┘
              │
              ▼
    ┌─────────────────────┐
    │  Voice Interface    │
    │  (Phase 2)          │
    └──────────┬──────────┘
               │
    ┌──────────▼──────────────────────────┐
    │   EdgeNodeOrchestrator               │
    │  ┌──────────────────────────────┐   │
    │  │ Local Inference Engine       │   │
    │  │ (Quantized SLMs)             │   │
    │  └──────────────────────────────┘   │
    │  ┌──────────────────────────────┐   │
    │  │ AsyncRequestQueue            │   │
    │  │ (SQLite + MQTT QoS 2)        │   │
    │  └──────────────────────────────┘   │
    └──────────┬──────────────────────────┘
               │
    ┌──────────▼──────────────────────────┐
    │ Hardware Layer                       │
    │ ├─ HardwareMonitor (CPU/Temp/Mem)  │
    │ ├─ PowerManager (Solar/Battery)     │
    │ └─ MQTTClient (Opportunistic)       │
    └──────────┬──────────────────────────┘
               │
    ┌──────────▼──────────────────────────┐
    │ Cloud (When Connected)               │
    │ ├─ Cloud LLM APIs                   │
    │ ├─ Data Syncing                     │
    │ └─ Model Updates                    │
    └──────────────────────────────────────┘
```

## Development Notes

- **Testing**: Use async/await patterns. See `pytest-asyncio`
- **Logging**: All modules use Python `logging`. Set level via env vars
- **Performance**: Async I/O throughout. Non-blocking hardware polling
- **Resilience**: No cloud dependencies for basic operation

## Next Steps

1. Implement GGUF model loading (llama-cpp-python)
2. Deploy to Raspberry Pi 5 with Alpine Linux
3. Create Gram Panchayat configuration templates
4. Build Phase 2 (Voice interface) on top
