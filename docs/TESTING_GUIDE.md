# Testing Guide - Phase 1

## Unit Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=edge_node --cov-report=term-missing
```

## Integration Tests

### Test Local Inference

```bash
# Start edge node
python3 main.py

# In another terminal
curl -X POST http://localhost:8000/infer \
  -H "Content-Type: application/json" \
  -d '{
    "query": "फसल की देखभाल कैसे करें?",
    "context": {"language": "hi", "crop": "wheat"}
  }'
```

### Test Async Queuing

```bash
# Queue a request
curl -X POST http://localhost:8000/queue \
  -H "Content-Type: application/json" \
  -d '{
    "request_type": "GOV_SCHEME_CHECK",
    "data": {"scheme": "PM_KISAN"},
    "priority": 1
  }'

# Check queue status
curl http://localhost:8000/queue/status

# Verify in SQLite
sqlite3 data/queue.db \
  "SELECT id, status, created_at FROM requests LIMIT 5;"
```

### Test MQTT Connectivity

```bash
# With mosquitto-clients installed:
mosquitto_sub -h localhost -t "edge/+/requests" &
mosquitto_pub -h localhost -t "edge/test/responses" \
  -m '{"result": "test_message"}'

# Verify MQTT client status
curl http://localhost:8000/connectivity/mqtt
```

### Test Power Management

```bash
# Simulate battery levels
python3 << 'EOF'
import asyncio
from edge_node.hardware.power import PowerManager

async def test_power():
    pm = PowerManager()
    
    # Simulate different battery states
    for battery in [100, 50, 20, 5]:
        pm.set_battery_percent(battery)
        status = pm.get_status()
        print(f"Battery {battery}% → Mode: {status['power_mode']}")

asyncio.run(test_power())
EOF
```

### Test Hardware Monitoring

```bash
# Run hardware monitor
python3 << 'EOF'
import asyncio
from edge_node.hardware.monitor import HardwareMonitor

async def monitor():
    hm = HardwareMonitor(thermal_threshold=75)
    while True:
        status = hm.get_status()
        print(f"CPU: {status['cpu_percent']}% | "
              f"Mem: {status['memory_percent']}% | "
              f"Temp: {status.get('temperature_celsius', 'N/A')}°C")
        await asyncio.sleep(5)

asyncio.run(monitor())
EOF
```

## Stress Tests

### CPU Stress Test

```bash
# Run heavy inference load
python3 << 'EOF'
import asyncio
from edge_node.core.orchestrator import EdgeNodeOrchestrator

async def stress_test():
    orchestrator = EdgeNodeOrchestrator()
    await orchestrator.startup()
    
    # Queue 100 requests rapidly
    for i in range(100):
        result = await orchestrator.process_local_query(
            f"Query number {i}: गेहूं की फसल की देखभाल"
        )
        print(f"[{i}] Inference time: {result.get('inference_time_ms')}ms")
    
    await orchestrator.shutdown()

asyncio.run(stress_test())
EOF
```

### Memory Stress Test

```bash
# Monitor memory under load
python3 << 'EOF'
import psutil
import asyncio
from edge_node.models.manager import QuantizedModelManager

async def memory_test():
    mm = QuantizedModelManager(models_dir="./models", max_memory_mb=2048)
    
    # Try loading multiple models
    models = [
        "sarvam-2b-indic-quantized-gguf",
        "llama-3-8b-indic-quantized-q4",
        "mobilebert-indic-lightweight"
    ]
    
    for model in models:
        await mm.load_model(model)
        mem = mm.get_memory_usage()
        process = psutil.Process()
        print(f"Model: {model}")
        print(f"  Queue memory: {mem['used_mb']:.1f}MB")
        print(f"  Process RSS: {process.memory_info().rss / 1024 / 1024:.1f}MB")

asyncio.run(memory_test())
EOF
```

### Connectivity Test

```bash
# Simulate network loss
python3 << 'EOF'
import asyncio
from edge_node.networking.mqtt_client import MQTTClient

async def connectivity_test():
    mqtt = MQTTClient(broker_address="localhost")
    
    # Test online
    await mqtt.connect()
    for i in range(5):
        success = await mqtt.publish(
            "edge/test/requests",
            {"sequence": i}
        )
        print(f"Message {i}: {'Published' if success else 'Buffered'}")
        await asyncio.sleep(1)
    
    # Simulate disconnect
    await mqtt.disconnect()
    
    # Try publishing offline (should buffer)
    for i in range(5, 10):
        success = await mqtt.publish(
            "edge/test/requests",
            {"sequence": i}
        )
        print(f"Message {i} (offline): {'Published' if success else 'Buffered'}")
    
    # Reconnect and verify flush
    await mqtt.connect()
    flushed = await mqtt.flush_buffer()
    print(f"Flushed {flushed} buffered messages")

asyncio.run(connectivity_test())
EOF
```

## Performance Benchmarks

### Inference Latency

```bash
# Measure inference time
python3 << 'EOF'
import asyncio
import time
from edge_node.models.manager import QuantizedModelManager

async def benchmark():
    mm = QuantizedModelManager(models_dir="./models")
    await mm.load_model("sarvam-2b-indic-quantized-gguf")
    
    query = "मेरी फसल में कीटों का संक्रमण है। क्या करूं?"
    
    # Warmup
    await mm.infer(query)
    
    # Benchmark
    times = []
    for _ in range(10):
        start = time.perf_counter()
        result = await mm.infer(query)
        end = time.perf_counter()
        times.append((end - start) * 1000)
    
    print(f"Mean: {sum(times)/len(times):.1f}ms")
    print(f"Min: {min(times):.1f}ms")
    print(f"Max: {max(times):.1f}ms")
    print(f"P95: {sorted(times)[int(len(times)*0.95)]:.1f}ms")

asyncio.run(benchmark())
EOF
```

### Queue Throughput

```bash
# Measure queue insert/retrieve rate
python3 << 'EOF'
import asyncio
import time
from edge_node.queue.async_queue import AsyncRequestQueue

async def queue_benchmark():
    queue = AsyncRequestQueue(db_path="./test_queue.db")
    
    # Benchmark queue insertion
    start = time.perf_counter()
    for i in range(1000):
        await queue.enqueue({"type": "test", "id": i})
    insert_time = time.perf_counter() - start
    
    print(f"1000 inserts in {insert_time:.2f}s ({1000/insert_time:.0f} req/s)")
    
    # Benchmark retrieval
    start = time.perf_counter()
    retrieved = await queue.get_pending(limit=100)
    retrieve_time = time.perf_counter() - start
    
    print(f"Retrieved 100 in {retrieve_time*1000:.1f}ms")

asyncio.run(queue_benchmark())
EOF
```

## Thermal Testing

### Simulate High Temperature

```bash
# Monitor temperature during load
watch -n 1 'cat /sys/class/thermal/thermal_zone0/temp | awk "{print \$1/1000 \"°C\"}"'

# Stress test CPU
stress-ng --cpu 4 --timeout 300s &
python3 << 'EOF'
import asyncio
from edge_node.hardware.monitor import HardwareMonitor

async def thermal_test():
    hm = HardwareMonitor(thermal_threshold=60)
    for _ in range(60):
        status = hm.get_status()
        alerts = status.get('alerts', [])
        throttle = hm.get_throttle_recommendations()
        print(f"Temp: {status['temperature_celsius']:.1f}°C | "
              f"Throttle: {throttle['should_defer_inference']} | "
              f"Alerts: {alerts}")
        await asyncio.sleep(1)

asyncio.run(thermal_test())
EOF
```

## End-to-End Test Scenario

```bash
# Complete user journey test

# 1. Start edge node
python3 main.py &
sleep 2

# 2. User asks local question (offline)
curl -X POST http://localhost:8000/infer \
  -d '{"query": "गेहूं की फसल में रोग"}' \
  -H "Content-Type: application/json"

# 3. User requests government check (queued for cloud)
curl -X POST http://localhost:8000/queue \
  -d '{
    "request_type": "PM_KISAN_ELIGIBILITY",
    "data": {"aadhar": "XXXX****XXXX"},
    "priority": 2
  }' \
  -H "Content-Type: application/json"

# 4. Check queue status
curl http://localhost:8000/queue/status

# 5. Monitor health
curl http://localhost:8000/health | jq .

# 6. List models
curl http://localhost:8000/models | jq .
```

## Continuous Integration

Sample GitHub Actions workflow (`.github/workflows/test.yml`):

```yaml
name: Phase 1 Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.10', '3.11']
    
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-asyncio pytest-cov
    
    - name: Run tests
      run: pytest tests/ --cov=edge_node
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
```
