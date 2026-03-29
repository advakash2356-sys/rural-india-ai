"""
Edge Node Configuration - Centralized settings for village edge deployments.
Supports multiple hardware profiles and deployment scenarios.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class EdgeConfig:
    """
    Configuration manager for edge node deployments.
    
    Handles:
    - Hardware-specific settings (CPU cores, memory limits)
    - Connectivity parameters (MQTT broker, backup networks)
    - Model selection and memory budgets
    - Power management (solar, battery thresholds)
    - Deployment location context (village, state, language)
    """
    
    # Hardware profiles for different Raspberry Pi/edge device configurations
    HARDWARE_PROFILES = {
        "raspi5-4gb": {
            "device": "Raspberry Pi 5",
            "cpu_cores": 4,
            "memory_mb": 4096,
            "max_model_memory_mb": 1800,
            "thermal_threshold": 75,
            "memory_threshold": 85
        },
        "raspi5-8gb": {
            "device": "Raspberry Pi 5 (8GB)",
            "cpu_cores": 4,
            "memory_mb": 8192,
            "max_model_memory_mb": 4000,
            "thermal_threshold": 75,
            "memory_threshold": 85
        },
        "gram-panchayat-server": {
            "device": "Mini PC Server",
            "cpu_cores": 8,
            "memory_mb": 16384,
            "max_model_memory_mb": 8000,
            "thermal_threshold": 80,
            "memory_threshold": 80
        }
    }
    
    def __init__(self):
        """Initialize with default configuration."""
        self.node_id = "edge_node_001"
        self.hardware_profile = "raspi5-4gb"
        self.location = {
            "state": "Uttar Pradesh",
            "district": "Example District",
            "gram_panchayat": "Example Village",
            "lat": 0.0,
            "lon": 0.0
        }
        self.language = "hi"  # Hindi
        
        # Hardware
        self.thermal_threshold = 75.0
        self.memory_threshold = 85.0
        self.max_model_memory_mb = 1800
        
        # Networking
        self.mqtt_broker = "mqtt.example.com"
        self.mqtt_port = 1883
        self.mqtt_topics = {
            "requests": f"edge/{self.node_id}/requests",
            "responses": f"edge/{self.node_id}/responses",
            "telemetry": f"edge/{self.node_id}/telemetry",
            "updates": f"updates/{self.node_id}"
        }
        
        # Storage
        self.models_path = "./models"
        self.queue_db_path = "./data/queue.db"
        self.state_dir = "./data/state"
        self.max_queue_size = 10000
        
        # Power
        self.has_solar = True
        self.battery_low_threshold = 20.0
        
        # OTA Updates
        self.ota_check_interval_hours = 24
        self.ota_download_window_start_hour = 2  # 2:00 AM (off-peak)
    
    @classmethod
    def load(cls, config_path: Optional[str] = None) -> "EdgeConfig":
        """
        Load configuration from file or use defaults.
        
        Args:
            config_path: Path to JSON config file
            
        Returns:
            EdgeConfig instance
        """
        config = cls()
        
        if config_path and Path(config_path).exists():
            try:
                with open(config_path, 'r') as f:
                    data = json.load(f)
                config._apply_config_dict(data)
                logger.info(f"Configuration loaded from {config_path}")
            except Exception as e:
                logger.error(f"Failed to load config from {config_path}: {e}")
        else:
            logger.info("Using default edge node configuration")
        
        return config
    
    def _apply_config_dict(self, data: Dict[str, Any]) -> None:
        """Apply configuration from dictionary."""
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def save(self, path: str) -> bool:
        """
        Save configuration to file.
        
        Args:
            path: Path to save config
            
        Returns:
            True if successful
        """
        try:
            config_dict = {
                "node_id": self.node_id,
                "hardware_profile": self.hardware_profile,
                "location": self.location,
                "language": self.language,
                "thermal_threshold": self.thermal_threshold,
                "memory_threshold": self.memory_threshold,
                "mqtt_broker": self.mqtt_broker,
                "models_path": self.models_path,
                "has_solar": self.has_solar,
                "battery_low_threshold": self.battery_low_threshold
            }
            
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            
            with open(path, 'w') as f:
                json.dump(config_dict, f, indent=2)
            
            logger.info(f"Configuration saved to {path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            return False
    
    def get_hardware_profile(self) -> Dict[str, Any]:
        """Get hardware profile specifications."""
        return self.HARDWARE_PROFILES.get(
            self.hardware_profile,
            self.HARDWARE_PROFILES["raspi5-4gb"]
        )
    
    def apply_hardware_profile(self, profile_name: str) -> bool:
        """
        Apply a hardware profile.
        
        Args:
            profile_name: Name of hardware profile
            
        Returns:
            True if profile applied
        """
        if profile_name not in self.HARDWARE_PROFILES:
            logger.error(f"Unknown hardware profile: {profile_name}")
            return False
        
        profile = self.HARDWARE_PROFILES[profile_name]
        self.hardware_profile = profile_name
        self.thermal_threshold = profile["thermal_threshold"]
        self.memory_threshold = profile["memory_threshold"]
        self.max_model_memory_mb = profile["max_model_memory_mb"]
        
        logger.info(f"Hardware profile applied: {profile_name}")
        return True
    
    def __str__(self) -> str:
        """Get summary of configuration."""
        return f"""
EdgeConfig Summary:
  Node ID: {self.node_id}
  Hardware: {self.hardware_profile}
  Location: {self.location['gram_panchayat']}, {self.location['state']}
  Language: {self.language}
  MQTT Broker: {self.mqtt_broker}:{self.mqtt_port}
  Max Model Memory: {self.max_model_memory_mb}MB
  Solar Enabled: {self.has_solar}
        """.strip()
