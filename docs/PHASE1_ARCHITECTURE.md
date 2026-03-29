# Rural India AI - Phase 1 Architecture Documentation

## Executive Summary

Phase 1 implements **Edge-Native Infrastructure** for deploying AI systems in resource-constrained rural Indian villages with intermittent connectivity, extreme temperatures, and constrained power supplies.

Traditional cloud-first architectures fail in this environment. This phase creates a **decentralized, resilient foundation** where:
- Compute happens locally on edge devices
- Connectivity is opportunistic (MQTT store-and-forward)
- Power is solar/battery aware
- Hardware gracefully degrades under thermal stress

## System Architecture

### 1. Core Components

```
┌─────────────────────────────────────────────────────────────────┐
│                    EdgeNodeOrchestrator                         │
│                    (Central Controller)                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────┐  ┌──────────────────┐                    │
│  │ Model Manager    │  │ Request Queue    │                    │
│  │ (Quantized LLMs) │  │ (Store-Forward)  │                    │
│  └──────────────────┘  └──────────────────┘                    │
│                                                                 │
│  ┌──────────────────┐  ┌──────────────────┐                    │
│  │ Hardware Monitor │  │ Power Manager    │                    │
│  │ (CPU/Temp/Mem)  │  │ (Solar/Battery)  │                    │
│  └──────────────────┘  └──────────────────┘                    │
│                                                                 │
│  ┌────────────────────────────────────────┐                    │
│  │ MQTT Client (Opportunistic Networking) │                    │
│  └────────────────────────────────────────┘                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2. Data Flow

#### Local Inference (No Cloud Needed)
```
User Input (Hindi/Dialect)
       │
       ▼
Local Quantized Model (2B-8B params)
       │
       ▼
Local Vector DB (Hyper-local context)
       │
       ▼
Response (Voice/Text)
```

#### Cloud Sync (When Online)
```
Local Queue (SQLite)
       │
       ▼
MQTT Publish (QoS 2 - Exactly Once)
       │
       ▼
Cloud Backend
       │
       ▼
Response → Local Queue → Consumer
```

## Technical Specifications

### Hardware Profile: Raspberry Pi 5 (4GB)

| Component | Specification |
|-----------|---------------|
| CPU | ARMv8 4-core @ 2.4 GHz |
| RAM | 4 GB (1.8 GB for models) |
| Storage | 64-128 GB microSD |
| Power | 5V, 5A (25W typical) |
| OS | Alpine Linux (minimal) |
| Thermal Design | Fanless, passive heatsink |

**Operating Conditions:**
- Ambient: 5°C to 48°C (winter to summer in UP)
- Humidity: 30-85% RH
- Altitude: 0-2000m
- Dust: High (requires sealed enclosure)

### Model Specifications

**Primary Model: Sarvam 2B Indic Quantized (4-bit)**
```
Parameters: 2.0 Billion
Training Data: 50+ Indian languages
Quantization: 4-bit (GGUF format)
Disk Size: ~1.2 GB
Memory at Runtime: ~1.8 GB (with context padding)
Inference Speed: ~2-3 tokens/second on Pi 5
Latency: 500-1500ms for typical 20-token response
```

**Fallback Model: MobileBERT Indic (Lightweight)**
```
Parameters: 110 Million
Focus: Classification/Intent extraction
Quantization: 8-bit
Disk Size: 200 MB
Memory: 350 MB
Latency: 50-150ms
```

### Queue Architecture

**SQLite-backed async queue:**
```sql
CREATE TABLE requests (
    id TEXT PRIMARY KEY,
    request_type TEXT,
    payload JSONB,
    status TEXT (pending|syncing|synced|failed),
    priority INTEGER,
    created_at ISO8601,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 5
)
```

**Synchronization Strategy:**
1. User creates request → Immediately queued locally
2. If online (MQTT connected): Publish with QoS 2 (exactly-once)
3. If offline: Batch store locally, retry on connection recovery
4. Exponential backoff: 5s → 10s → 30s → 60s → max 5 attempts
5. "Data Mule" fallback: Official with smartphone syncs batch quarterly

### Power Management

**Three Operational Modes:**

| Mode | CPU Freq | Inference | Sync | Use Case |
|------|----------|-----------|------|----------|
| **Full** | 2.4 GHz | Enabled | Every 5min | Day (solar available) |
| **Reduced** | 1.8 GHz | Enabled | Every 15min | Evening (battery low) |
| **Low Power** | 1.2 GHz | Disabled | Every 60min | Night (battery <20%) |

**Power Budget Calculation:**
```
Solar Array: 400W peak
Battery: 100Ah @ 9.6V = 960 Wh
Daily Draw: 
  - Night (10h): 15W × 10h = 150 Wh
  - Day (14h): 25W × 14h = 350 Wh
  - Total: ~500 Wh/day (sustainable with 400W solar)
```

### Thermal Management

**Heat Source Analysis:**
- CPU: 4-8W sustained during inference
- Storage: 1-2W
- Network (WiFi/Cellular): 2-3W
- Total: ~10W in reduced mode, 15-20W in full mode

**Cooling Strategy:**
- Passive heatsink + aluminum enclosure
- Thermal zone monitoring every 5 seconds
- Automatic inference deferral above 75°C
- Night mode execution for batch processing

## Communication Protocols

### MQTT (Primary)
```
Broker: cloud.example.com:1883
Client ID: edge_{node_id}
QoS: 2 (Exactly Once)

Topics:
- edge/{node_id}/requests → Outbound queries
- edge/{node_id}/responses → Inbound results
- edge/{node_id}/telemetry → Health metrics (daily batch)
- updates/{node_id} → Model/config updates
```

### Backup: SMS/USSD (Data Mule)
```
Format: JSON-encoded base64 in SMS
Maximum: 160 characters per message
Frequency: Quarterly or on-demand
Use: Sync when 2G-only available
```

## State Management

**Critical State Persistence:**
```
/data/state/
├── node_state.json       # Edge metadata, last sync time
├── model_manifest.json   # Loaded models, versions
└── queue.db              # SQLite request queue
```

**Failure Modes Handled:**
- Power loss → Resume from state after reboot
- Network partitioned → Local queue persists
- Thermal throttle → Graceful degradation
- Disk full → Rotate old queue entries

## Observability & Monitoring

**Lightweight Telemetry (kilobytes/day):**
```json
{
  "timestamp": "2024-03-28T14:30:00Z",
  "node_id": "edge_up_example_001",
  "cpu_percent": 35,
  "memory_percent": 72,
  "temperature_celsius": 42,
  "battery_percent": 65,
  "solar_watts": 250,
  "queue_pending": 3,
  "inference_count": 156,
  "sync_status": "ok"
}
```

**Sent Once Daily** (total ~2 KB/day = 60 KB/month)

## Security Considerations

**Current Phase 1 (Development):**
- MQTT over plain TCP (for minimal overhead)
- Local SQLite (no encryption, edge node is trusted)

**Future Phases:**
- MQTT over TLS with certificates
- Local SQLite encryption (sqlcipher)
- Voice biometric consent (Phase 5)
- Input validation & injection prevention

## Deployment Checklist

- [ ] Alpine Linux 3.18+ on Raspberry Pi 5
- [ ] Python 3.10+ with venv
- [ ] Solar+Battery system installed & monitored
- [ ] MQTT broker address configured
- [ ] Village configuration file deployed
- [ ] Quantized models pre-downloaded
- [ ] Systemd service enabled for auto-startup
- [ ] Health check dashboard accessible
- [ ] Gram Panchayat trained on reboot procedures

## Performance Targets

| Metric | Target | Current | Notes |
|--------|--------|---------|-------|
| Boot time | <3 min | 2-2.5 min | Alpine helps |
| Local inference latency | <2 sec | ~1.5 sec | Sarvam 2B |
| Queue throughput | >100 req/sec | Not yet measured | SQLite limit ~1K |
| Memory overhead | <500 MB | ~450 MB | OS + base services |
| Power draw (idle) | <5W | ~3W | Good headroom |
| MQTT msg round-trip | <5 sec | Depends on connectivity | QoS 2 overhead |

## Known Limitations & Trade-offs

### Limitations
1. **Model Size**: 2B parameters is max practical limit (1.8 GB load)
2. **Context Window**: 2048 tokens (vs 4096+ in cloud models)
3. **Inference Speed**: ~2 tokens/sec (vs 50+ tokens/sec on GPU)
4. **No Real-time Streaming**: Batch-based inference only

### Trade-offs Made
- Chose **4-bit quantization** (q4) over q2 for accuracy (uses more memory)
- Chose **MQTT QoS 2** over UDP (more overhead, 100% reliability)
- Chose **SQLite** over in-memory queue (slower but durable)
- Chose **off-peak OTA** (2 AM) over immediate updates (battery conscious)

## Future Improvements (Phase 2-6)

Phase 1 provides foundation for:
- **Phase 2**: Voice UI + Indic ASR/TTS
- **Phase 3**: Vector DB + hyper-local RAG
- **Phase 4**: Domain-specific agents
- **Phase 5**: Guardrails + consent engineering
- **Phase 6**: Dashboard + self-healing

Each builds on Phase 1's edge-native, async-first architecture.
