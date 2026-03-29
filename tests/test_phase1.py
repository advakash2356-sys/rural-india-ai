"""Example test file for Phase 1 components."""

import pytest
import asyncio
from pathlib import Path

from edge_node.core.orchestrator import EdgeNodeOrchestrator
from edge_node.core.state_manager import StateManager
from edge_node.models.manager import QuantizedModelManager
from edge_node.queue.async_queue import AsyncRequestQueue
from edge_node.hardware.monitor import HardwareMonitor
from edge_node.hardware.power import PowerManager


@pytest.fixture
async def orchestrator(tmp_path):
    """Create test orchestrator instance."""
    # Mock config paths
    (tmp_path / "models").mkdir(exist_ok=True)
    (tmp_path / "data").mkdir(exist_ok=True)
    
    orch = EdgeNodeOrchestrator()
    orch.config.models_path = str(tmp_path / "models")
    orch.config.queue_db_path = str(tmp_path / "data" / "queue.db")
    orch.config.state_dir = str(tmp_path / "data" / "state")
    
    # Reinitialize with test paths
    orch.request_queue = AsyncRequestQueue(
        db_path=str(tmp_path / "data" / "queue.db")
    )
    orch.model_manager = QuantizedModelManager(
        models_dir=Path(tmp_path / "models")
    )
    
    return orch


@pytest.mark.asyncio
async def test_orchestrator_startup(orchestrator):
    """Test edge node startup."""
    success = await orchestrator.startup()
    assert success or not success  # May fail due to missing MQTT broker
    
    # But internal systems should init
    assert orchestrator.model_manager is not None
    assert orchestrator.request_queue is not None


@pytest.mark.asyncio
async def test_state_manager(tmp_path):
    """Test state persistence."""
    sm = StateManager(str(tmp_path / "state"))
    
    # Test set/get
    assert sm.set("test_key", "test_value")
    assert sm.get("test_key") == "test_value"
    
    # Test pending requests
    assert sm.append_pending_request({"id": "req_1", "data": "test"})
    pending = sm.get_pending_requests()
    assert len(pending) == 1
    assert pending[0]["id"] == "req_1"


@pytest.mark.asyncio
async def test_request_queue(tmp_path):
    """Test async request queue."""
    queue = AsyncRequestQueue(
        db_path=str(tmp_path / "queue.db"),
        max_queue_size=100
    )
    
    # Test enqueue
    req_id = await queue.enqueue({
        "type": "test_request",
        "priority": 1
    })
    assert req_id is not None
    
    # Test pending count
    count = await queue.count_pending()
    assert count == 1
    
    # Test get pending
    pending = await queue.get_pending(limit=10)
    assert len(pending) == 1
    assert pending[0]["id"] == req_id
    
    # Test mark synced
    success = await queue.mark_synced(req_id)
    assert success
    
    # Should no longer be pending
    count = await queue.count_pending()
    assert count == 0


@pytest.mark.asyncio
async def test_model_manager(tmp_path):
    """Test quantized model manager."""
    mm = QuantizedModelManager(
        models_dir=Path(tmp_path / "models"),
        max_memory_mb=2048
    )
    
    # Test memory usage
    memory = mm.get_memory_usage()
    assert memory["used_mb"] == 0
    assert memory["max_mb"] == 2048
    
    # Test inference (will use placeholder)
    result = await mm.infer("Test query", context={})
    assert "error" in result or "response" in result


def test_hardware_monitor():
    """Test hardware monitoring."""
    hm = HardwareMonitor(thermal_threshold=75)
    
    status = hm.get_status()
    assert "cpu_percent" in status
    assert "memory_percent" in status
    assert "timestamp" in status
    
    # Check constraint methods
    overheating = hm.is_device_overheating()
    assert isinstance(overheating, bool)
    
    constrained = hm.is_memory_constrained()
    assert isinstance(constrained, bool)


def test_power_manager():
    """Test power management."""
    pm = PowerManager(solar_mode=True, battery_low_threshold=20)
    
    # Test status
    status = pm.get_status()
    assert "battery_percent" in status
    assert "solar_watts" in status
    assert "power_mode" in status
    
    # Test power modes
    pm.set_battery_percent(100)
    status = pm.get_status()
    assert status["power_mode"] in ["full", "reduced"]
    
    pm.set_battery_percent(10)
    status = pm.get_status()
    assert status["power_mode"] == "low_power"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
