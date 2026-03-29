"""
Power Manager - Manages solar-battery arrays and power states for fanless edge nodes.
Optimizes for off-grid, solar-powered infrastructure in rural India.
"""

import logging
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class PowerManager:
    """
    Manages power states for solar-backed, battery-equipped edge nodes.
    
    Features:
    - Battery state tracking
    - Solar input monitoring
    - Power mode management (full, reduced, low-power)
    - Charge scheduling optimization
    
    Designed for solar panels with intelligent charge controllers
    deployed in villages with 45°C+ ambient temperatures.
    """
    
    POWER_MODES = {
        "full": {"cpu_freq_mhz": 2400, "inference_enabled": True, "sync_interval_min": 5},
        "reduced": {"cpu_freq_mhz": 1800, "inference_enabled": True, "sync_interval_min": 15},
        "low_power": {"cpu_freq_mhz": 1200, "inference_enabled": False, "sync_interval_min": 60}
    }
    
    def __init__(self, solar_mode: bool = True, battery_low_threshold: float = 20.0):
        """
        Initialize power manager.
        
        Args:
            solar_mode: Whether solar input is available
            battery_low_threshold: Battery percentage to trigger low-power mode
        """
        self.solar_mode = solar_mode
        self.battery_low_threshold = battery_low_threshold
        self.power_mode = "full"
        self.solar_watts = 0.0
        self.battery_percent = 100.0
        
        logger.info(f"PowerManager initialized - Solar mode: {solar_mode}, "
                   f"Low battery threshold: {battery_low_threshold}%")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current power status.
        
        Returns:
            Power metrics and state
        """
        try:
            # Simulate solar and battery readings
            # In production: read from actual hardware interfaces
            
            self.power_mode = self._determine_power_mode()
            
            return {
                "solar_mode_enabled": self.solar_mode,
                "solar_watts": self.solar_watts,
                "battery_percent": self.battery_percent,
                "battery_low": self.battery_percent < self.battery_low_threshold,
                "power_mode": self.power_mode,
                "power_config": self.POWER_MODES[self.power_mode],
                "estimated_runtime_hours": self._estimate_runtime(),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get power status: {e}")
            return {"error": str(e)}
    
    def _determine_power_mode(self) -> str:
        """
        Determine optimal power mode based on battery and solar input.
        
        Returns:
            Power mode string: 'full', 'reduced', or 'low_power'
        """
        # If battery is very low, force low-power mode
        if self.battery_percent < self.battery_low_threshold:
            return "low_power"
        
        # If battery is good and solar is available, use full power
        if self.solar_mode and self.solar_watts > 50:
            return "full"
        
        # Default to reduced power
        return "reduced"
    
    def _estimate_runtime(self) -> float:
        """
        Estimate remaining runtime on battery.
        
        Returns:
            Estimated hours of operation
        """
        # Simplified calculation
        # In production: use actual power draw metrics
        if self.battery_percent < 5:
            return 0.5
        elif self.battery_percent < 20:
            return 2.0
        elif self.battery_percent < 50:
            return 6.0
        else:
            return 12.0 if self.solar_mode else 24.0
    
    def request_power_budget(self, task_name: str, estimated_watts: float, 
                            duration_seconds: float) -> bool:
        """
        Request power budget for a task.
        
        Args:
            task_name: Name of task
            estimated_watts: Estimated power draw
            duration_seconds: Task duration estimate
            
        Returns:
            True if power is available
        """
        energy_needed_wh = (estimated_watts * duration_seconds) / 3600
        battery_capacity_wh = 100 * self.battery_percent  # Assume 100Wh battery
        
        available = energy_needed_wh < battery_capacity_wh * 0.3  # Keep 30% margin
        
        if available:
            logger.info(f"Power budget approved for '{task_name}': {energy_needed_wh:.1f}Wh")
        else:
            logger.warning(f"Insufficient power budget for '{task_name}': need {energy_needed_wh:.1f}Wh")
        
        return available
    
    def set_solar_input(self, watts: float) -> None:
        """Update solar panel input measurement."""
        self.solar_watts = max(0, watts)
        logger.debug(f"Solar input updated: {self.solar_watts:.1f}W")
    
    def set_battery_percent(self, percent: float) -> None:
        """Update battery charge percentage."""
        self.battery_percent = max(0, min(100, percent))
        logger.debug(f"Battery updated: {self.battery_percent:.1f}%")
    
    def get_charging_schedule(self) -> Dict[str, Any]:
        """
        Get optimal charging schedule based on solar availability
        and time-of-day (minimize cloud cover impact).
        
        Returns:
            Charging schedule recommendations
        """
        return {
            "primary_charge_hours": "6:00-18:00",  # Typical Indian daylight
            "cloud_contingency": "Run inference in morning (clearer skies)",
            "thermal_management": "Avoid heavy compute 12:00-16:00 (peak heat)",
            "night_mode_start": "19:00",
            "night_mode_end": "05:00",
            "deep_sleep_at_battery": "< 10%"
        }
