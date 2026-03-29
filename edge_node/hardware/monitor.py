"""
Hardware Monitor - Tracks edge device health and constraints.
Essential for harsh-environment deployment in Indian villages with extreme temps.
"""

import psutil
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class HardwareMonitor:
    """
    Monitors hardware health and resource constraints on edge nodes.
    
    Tracks:
    - CPU utilization and temperature
    - Memory usage
    - Disk space
    - Thermal throttling indicators
    - Power state
    
    Designed for fanless, solid-state devices in 45°C+ environments.
    """
    
    def __init__(self, thermal_threshold_celsius: float = 75.0, 
                 memory_threshold_percent: float = 85.0):
        """
        Initialize hardware monitor.
        
        Args:
            thermal_threshold_celsius: CPU temp warning threshold
            memory_threshold_percent: Memory usage warning threshold
        """
        self.thermal_threshold = thermal_threshold_celsius
        self.memory_threshold = memory_threshold_percent
        self.alert_history = []
        
        logger.info(f"HardwareMonitor initialized - Thermal threshold: {thermal_threshold_celsius}°C, "
                   f"Memory threshold: {memory_threshold_percent}%")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get comprehensive hardware status.
        
        Returns:
            Dictionary with hardware metrics
        """
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            # Memory metrics
            memory = psutil.virtual_memory()
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            
            # Temperature (if available)
            temperature = self._get_temperature()
            
            # Check alert conditions
            alerts = []
            if temperature and temperature > self.thermal_threshold:
                alerts.append(f"HIGH_TEMP: {temperature:.1f}°C > {self.thermal_threshold}°C threshold")
            if memory.percent > self.memory_threshold:
                alerts.append(f"HIGH_MEMORY: {memory.percent:.1f}% > {self.memory_threshold}% threshold")
            
            if alerts:
                logger.warning(f"Hardware alerts: {', '.join(alerts)}")
            
            return {
                "cpu_percent": cpu_percent,
                "cpu_count": cpu_count,
                "memory_percent": memory.percent,
                "memory_available_mb": memory.available >> 20,  # Convert to MB
                "memory_total_mb": memory.total >> 20,
                "disk_percent": disk.percent,
                "disk_free_mb": disk.free >> 20,
                "temperature_celsius": temperature,
                "thermal_throttling": temperature > self.thermal_threshold if temperature else False,
                "load_average": psutil.getloadavg(),
                "alerts": alerts,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get hardware status: {e}")
            return {"error": str(e)}
    
    @staticmethod
    def _get_temperature() -> Optional[float]:
        """
        Get CPU temperature if available.
        
        Returns:
            Temperature in Celsius or None if unavailable
        """
        try:
            temps = psutil.sensors_temperatures()
            if 'coretemp' in temps:
                return temps['coretemp'][0].current
            elif 'acpitz' in temps:
                return temps['acpitz'][0].current
            elif temps:
                # Return first available temperature
                first_key = list(temps.keys())[0]
                return temps[first_key][0].current
            return None
        except Exception:
            return None
    
    def is_device_overheating(self) -> bool:
        """Check if device is in thermal stress."""
        status = self.get_status()
        temp = status.get('temperature_celsius')
        return temp and temp > self.thermal_threshold if temp else False
    
    def is_memory_constrained(self) -> bool:
        """Check if device is low on memory."""
        status = self.get_status()
        return status.get('memory_percent', 0) > self.memory_threshold
    
    def get_throttle_recommendations(self) -> Dict[str, Any]:
        """
        Get performance throttling recommendations based on hardware state.
        
        Returns:
            Recommendations for inference throttling
        """
        status = self.get_status()
        
        recommendations = {
            "should_defer_inference": False,
            "inference_batch_size": 1,
            "model_precision": "q4",  # 4-bit quantization
            "max_context_tokens": 2048,
            "reasons": []
        }
        
        # High temperature - defer non-essential work
        if status.get('thermal_throttling'):
            recommendations["should_defer_inference"] = True
            recommendations["reasons"].append("High temperature")
        
        # High CPU - reduce batch size
        if status.get('cpu_percent', 0) > 80:
            recommendations["inference_batch_size"] = 1
            recommendations["reasons"].append("High CPU utilization")
        
        # Low memory - use lower precision
        if status.get('memory_percent', 0) > 75:
            recommendations["model_precision"] = "q2"
            recommendations["reasons"].append("Low memory")
        
        return recommendations
