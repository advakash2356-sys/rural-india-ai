"""
Observability & Analytics
Phase 6 Feature
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List
from pathlib import Path
from collections import defaultdict

logger = logging.getLogger(__name__)


class MetricsCollector:
    """Collects system and application metrics."""
    
    def __init__(self, metrics_dir: str = "data/metrics"):
        self.metrics_dir = Path(metrics_dir)
        self.metrics_dir.mkdir(parents=True, exist_ok=True)
        
        self.metrics = defaultdict(list)
        self.start_time = datetime.utcnow()
        
        logger.info("MetricsCollector initialized")
    
    def record_metric(self, name: str, value: float, tags: Dict[str, str] = None):
        """
        Record a metric value.
        
        Args:
            name: Metric name
            value: Metric value
            tags: Optional tags for categorization
        """
        metric = {
            "timestamp": datetime.utcnow().isoformat(),
            "name": name,
            "value": value,
            "tags": tags or {}
        }
        
        self.metrics[name].append(metric)
    
    def record_inference(self, model: str, latency_ms: float, success: bool):
        """Record inference metrics."""
        self.record_metric(
            "inference_latency",
            latency_ms,
            {"model": model, "success": str(success)}
        )
    
    def record_request(self, endpoint: str, latency_ms: float, status_code: int):
        """Record API request metrics."""
        self.record_metric(
            "request_latency",
            latency_ms,
            {"endpoint": endpoint, "status": str(status_code)}
        )
    
    def get_summary(self, metric_name: str, minutes: int = 60) -> Dict[str, float]:
        """
        Get metric summary for recent period.
        
        Args:
            metric_name: Name of metric
            minutes: Look back period in minutes
            
        Returns:
            Summary statistics
        """
        if metric_name not in self.metrics:
            return {}
        
        cutoff = datetime.utcnow() - timedelta(minutes=minutes)
        recent_metrics = [
            m['value'] for m in self.metrics[metric_name]
            if datetime.fromisoformat(m['timestamp']) > cutoff
        ]
        
        if not recent_metrics:
            return {}
        
        import statistics
        return {
            "count": len(recent_metrics),
            "mean": statistics.mean(recent_metrics),
            "median": statistics.median(recent_metrics),
            "min": min(recent_metrics),
            "max": max(recent_metrics),
            "stdev": statistics.stdev(recent_metrics) if len(recent_metrics) > 1 else 0
        }
    
    def export_metrics(self, filename: str = "metrics.json"):
        """Export metrics to JSON file."""
        try:
            filepath = self.metrics_dir / filename
            
            data = {
                "start_time": self.start_time.isoformat(),
                "export_time": datetime.utcnow().isoformat(),
                "metrics": {
                    name: metrics for name, metrics in self.metrics.items()
                }
            }
            
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            
            logger.info(f"Metrics exported to {filepath}")
            
        except Exception as e:
            logger.error(f"Failed to export metrics: {e}")


class UsageAnalytics:
    """Analyzes system usage patterns."""
    
    def __init__(self):
        self.interactions = []
        self.languages_used = defaultdict(int)
        self.domains_accessed = defaultdict(int)
        self.errors_by_type = defaultdict(int)
        
        logger.info("UsageAnalytics initialized")
    
    def record_interaction(self, 
                          query: str,
                          language: str,
                          domain: str,
                          success: bool,
                          latency_ms: float):
        """Record user interaction."""
        interaction = {
            "timestamp": datetime.utcnow().isoformat(),
            "query_length": len(query),
            "language": language,
            "domain": domain,
            "success": success,
            "latency_ms": latency_ms
        }
        
        self.interactions.append(interaction)
        self.languages_used[language] += 1
        self.domains_accessed[domain] += 1
        
        if not success:
            self.errors_by_type[domain] += 1
    
    def record_error(self, error_type: str, domain: str = "general"):
        """Record an error."""
        self.errors_by_type[f"{domain}:{error_type}"] += 1
    
    def get_usage_summary(self) -> Dict[str, Any]:
        """Get usage statistics summary."""
        if not self.interactions:
            return {}
        
        total_interactions = len(self.interactions)
        successful = sum(1 for i in self.interactions if i['success'])
        failed = total_interactions - successful
        
        latencies = [i['latency_ms'] for i in self.interactions]
        
        import statistics
        return {
            "total_interactions": total_interactions,
            "successful": successful,
            "failed": failed,
            "success_rate": successful / total_interactions if total_interactions > 0 else 0,
            "avg_latency_ms": statistics.mean(latencies) if latencies else 0,
            "languages": dict(self.languages_used),
            "domains": dict(self.domains_accessed),
            "errors": dict(self.errors_by_type)
        }
    
    def get_language_distribution(self) -> Dict[str, float]:
        """Get language usage distribution."""
        total = sum(self.languages_used.values())
        
        return {
            lang: (count / total * 100) if total > 0 else 0
            for lang, count in self.languages_used.items()
        }


class HealthMonitor:
    """Monitors system health and performance."""
    
    def __init__(self):
        self.alerts = []
        self.health_checks = []
        
        logger.info("HealthMonitor initialized")
    
    async def check_health(self, orchestrator) -> Dict[str, Any]:
        """
        Perform comprehensive health check.
        
        Args:
            orchestrator: EdgeNodeOrchestrator instance
            
        Returns:
            Health status report
        """
        health = {
            "timestamp": datetime.utcnow().isoformat(),
            "status": "healthy",
            "components": {}
        }
        
        # Check hardware
        hw_status = orchestrator.hardware_monitor.get_status()
        if hw_status.get('alerts'):
            health["status"] = "degraded"
            health["components"]["hardware"] = "warning"
        else:
            health["components"]["hardware"] = "healthy"
        
        # Check connectivity
        mqtt_connected = await orchestrator.mqtt_client.is_connected_async()
        health["components"]["connectivity"] = "healthy" if mqtt_connected else "offline"
        
        if not mqtt_connected:
            health["status"] = "degraded"
        
        # Check models
        loaded_models = len(orchestrator.model_manager.loaded_models)
        health["components"]["models"] = {
            "loaded": loaded_models,
            "status": "ready" if loaded_models > 0 else "no_models"
        }
        
        # Check queue
        queue_size = await orchestrator.request_queue.count_pending()
        health["components"]["queue"] = {
            "pending": queue_size,
            "status": "healthy" if queue_size < 100 else "backlog"
        }
        
        self.health_checks.append(health)
        return health
    
    def create_alert(self, severity: str, component: str, message: str):
        """Create an alert."""
        alert = {
            "timestamp": datetime.utcnow().isoformat(),
            "severity": severity,  # "critical", "warning", "info"
            "component": component,
            "message": message
        }
        
        self.alerts.append(alert)
        
        if severity == "critical":
            logger.critical(f"[ALERT] {component}: {message}")
        elif severity == "warning":
            logger.warning(f"[ALERT] {component}: {message}")
        else:
            logger.info(f"[ALERT] {component}: {message}")
        
        return alert
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get overall health summary."""
        if not self.health_checks:
            return {"status": "unknown"}
        
        latest = self.health_checks[-1]
        
        return {
            "current_status": latest['status'],
            "last_check": latest['timestamp'],
            "components": latest['components'],
            "critical_alerts": sum(
                1 for a in self.alerts 
                if a['severity'] == 'critical' and 
                   datetime.fromisoformat(a['timestamp']) > 
                   datetime.utcnow() - timedelta(hours=1)
            )
        }


class Dashboard:
    """
    Simple dashboard for observability insights.
    Provides structured data for visualization.
    """
    
    def __init__(self, 
                 metrics: MetricsCollector,
                 analytics: UsageAnalytics,
                 health: HealthMonitor):
        self.metrics = metrics
        self.analytics = analytics
        self.health = health
        
        logger.info("Dashboard initialized")
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive dashboard data."""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "health": self.health.get_health_summary(),
            "usage": self.analytics.get_usage_summary(),
            "languages": self.analytics.get_language_distribution(),
            "performance": {
                "inference": self.metrics.get_summary("inference_latency", minutes=60),
                "requests": self.metrics.get_summary("request_latency", minutes=60)
            },
            "recent_alerts": self.health.alerts[-5:]  # Last 5 alerts
        }
    
    def print_summary(self):
        """Print a text summary to logs."""
        data = self.get_dashboard_data()
        
        logger.info("\n" + "=" * 60)
        logger.info("SYSTEM DASHBOARD SUMMARY")
        logger.info("=" * 60)
        
        # Health
        logger.info(f"Status: {data['health']['status']}")
        
        # Usage
        usage = data['usage']
        if usage:
            logger.info(f"Total Interactions: {usage.get('total_interactions', 0)}")
            logger.info(f"Success Rate: {usage.get('success_rate', 0):.1%}")
            logger.info(f"Avg Latency: {usage.get('avg_latency_ms', 0):.0f}ms")
        
        # Languages
        langs = data.get('languages', {})
        if langs:
            logger.info("Top Languages:")
            for lang, pct in sorted(langs.items(), 
                                  key=lambda x: x[1], 
                                  reverse=True)[:3]:
                logger.info(f"  {lang}: {pct:.1f}%")
        
        logger.info("=" * 60 + "\n")
