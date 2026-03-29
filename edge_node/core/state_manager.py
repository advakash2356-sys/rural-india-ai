"""
State Manager - Maintains edge node state and handles persistence.
Ensures resilience during power loss and connectivity failures.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class StateManager:
    """
    Manages persistent state for edge nodes.
    
    Handles:
    - State persistence to local storage
    - State recovery after power loss
    - State synchronization with cloud
    - Atomic writes to prevent corruption
    """
    
    def __init__(self, state_dir: str):
        """
        Initialize state manager.
        
        Args:
            state_dir: Directory for state files
        """
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.state_file = self.state_dir / "node_state.json"
        self.state = self._load_state()
        
        logger.info(f"StateManager initialized with directory: {state_dir}")
    
    def _load_state(self) -> Dict[str, Any]:
        """Load state from persistent storage."""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load state: {e}")
                return self._default_state()
        return self._default_state()
    
    @staticmethod
    def _default_state() -> Dict[str, Any]:
        """Return default state structure."""
        return {
            "initialized": False,
            "last_sync": None,
            "pending_requests": [],
            "model_versions": {},
            "sync_status": "idle"
        }
    
    def _save_state(self) -> bool:
        """
        Persist state to disk atomically.
        
        Returns:
            True if successful
        """
        try:
            # Write to temporary file first
            temp_file = self.state_file.with_suffix('.json.tmp')
            with open(temp_file, 'w') as f:
                json.dump(self.state, f, indent=2)
            
            # Atomic rename
            temp_file.replace(self.state_file)
            return True
        except Exception as e:
            logger.error(f"Failed to save state: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get state value."""
        return self.state.get(key, default)
    
    def set(self, key: str, value: Any) -> bool:
        """
        Set state value and persist.
        
        Returns:
            True if successful
        """
        self.state[key] = value
        return self._save_state()
    
    def append_pending_request(self, request: Dict[str, Any]) -> bool:
        """Append request to pending queue."""
        if "pending_requests" not in self.state:
            self.state["pending_requests"] = []
        
        self.state["pending_requests"].append({
            "id": request.get("id"),
            "timestamp": datetime.utcnow().isoformat(),
            "data": request
        })
        
        return self._save_state()
    
    def get_pending_requests(self) -> list:
        """Get all pending requests."""
        return self.state.get("pending_requests", [])
    
    def clear_pending_request(self, request_id: str) -> bool:
        """Remove a request from pending queue."""
        self.state["pending_requests"] = [
            req for req in self.state.get("pending_requests", [])
            if req.get("id") != request_id
        ]
        return self._save_state()
    
    def update_last_sync(self) -> bool:
        """Update last synchronization timestamp."""
        self.state["last_sync"] = datetime.utcnow().isoformat()
        return self._save_state()
    
    def set_sync_status(self, status: str) -> bool:
        """
        Set synchronization status.
        
        Args:
            status: One of 'idle', 'syncing', 'error'
        """
        if status not in ["idle", "syncing", "error"]:
            logger.error(f"Invalid sync status: {status}")
            return False
        
        self.state["sync_status"] = status
        return self._save_state()
