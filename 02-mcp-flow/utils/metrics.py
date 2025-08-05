from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import asyncio
import json
import os
from collections import defaultdict
import statistics


class MetricType:
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


class Metric:
    def __init__(
        self,
        name: str,
        type: str,
        description: str,
        labels: Optional[Dict[str, str]] = None,
    ):
        self.name = name
        self.type = type
        self.description = description
        self.labels = labels or {}
        self.value = 0
        self.values = []  # For histogram/summary
        self.timestamp = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": self.type,
            "description": self.description,
            "labels": self.labels,
            "value": self.value
            if self.type in [MetricType.COUNTER, MetricType.GAUGE]
            else None,
            "values": self.values
            if self.type in [MetricType.HISTOGRAM, MetricType.SUMMARY]
            else None,
            "timestamp": self.timestamp.isoformat(),
        }


class MetricsCollector:
    def __init__(
        self,
        server_name: str,
        storage_path: str = "metrics",
        retention_days: int = 7,
        flush_interval: int = 60,
    ):
        self.server_name = server_name
        self.storage_path = storage_path
        self.retention_days = retention_days
        self.flush_interval = flush_interval

        self.metrics: Dict[str, Metric] = {}
        self.metric_values: Dict[str, List[float]] = defaultdict(list)

        # Ensure storage directory exists
        os.makedirs(storage_path, exist_ok=True)

        # Background tasks
        self._flush_task = None
        self._cleanup_task = None

    def create_counter(
        self, name: str, description: str, labels: Optional[Dict[str, str]] = None
    ) -> None:
        """Create a counter metric"""
        self.metrics[name] = Metric(name, MetricType.COUNTER, description, labels)

    def create_gauge(
        self, name: str, description: str, labels: Optional[Dict[str, str]] = None
    ) -> None:
        """Create a gauge metric"""
        self.metrics[name] = Metric(name, MetricType.GAUGE, description, labels)

    def create_histogram(
        self, name: str, description: str, labels: Optional[Dict[str, str]] = None
    ) -> None:
        """Create a histogram metric"""
        self.metrics[name] = Metric(name, MetricType.HISTOGRAM, description, labels)

    def create_summary(
        self, name: str, description: str, labels: Optional[Dict[str, str]] = None
    ) -> None:
        """Create a summary metric"""
        self.metrics[name] = Metric(name, MetricType.SUMMARY, description, labels)

    def increment(self, name: str, value: float = 1) -> None:
        """Increment a counter"""
        if name not in self.metrics:
            raise ValueError(f"Metric {name} not found")
        if self.metrics[name].type != MetricType.COUNTER:
            raise ValueError(f"Metric {name} is not a counter")
        self.metrics[name].value += value
        self.metrics[name].timestamp = datetime.now()

    def set_gauge(self, name: str, value: float) -> None:
        """Set a gauge value"""
        if name not in self.metrics:
            raise ValueError(f"Metric {name} not found")
        if self.metrics[name].type != MetricType.GAUGE:
            raise ValueError(f"Metric {name} is not a gauge")
        self.metrics[name].value = value
        self.metrics[name].timestamp = datetime.now()

    def observe(self, name: str, value: float) -> None:
        """Record an observation for histogram/summary"""
        if name not in self.metrics:
            raise ValueError(f"Metric {name} not found")
        if self.metrics[name].type not in [MetricType.HISTOGRAM, MetricType.SUMMARY]:
            raise ValueError(f"Metric {name} is not a histogram/summary")
        self.metrics[name].values.append(value)
        self.metrics[name].timestamp = datetime.now()

    def get_metric(self, name: str) -> Dict[str, Any]:
        """Get current value of a metric"""
        if name not in self.metrics:
            raise ValueError(f"Metric {name} not found")

        metric = self.metrics[name]
        result = metric.to_dict()

        if metric.type == MetricType.SUMMARY:
            values = metric.values
            if values:
                result.update(
                    {
                        "count": len(values),
                        "sum": sum(values),
                        "min": min(values),
                        "max": max(values),
                        "mean": statistics.mean(values),
                        "median": statistics.median(values),
                        "stddev": statistics.stdev(values) if len(values) > 1 else 0,
                    }
                )

        return result

    def get_all_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Get all metrics"""
        return {name: self.get_metric(name) for name in self.metrics}

    async def start(self) -> None:
        """Start background tasks"""
        self._flush_task = asyncio.create_task(self._flush_loop())
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def stop(self) -> None:
        """Stop background tasks"""
        if self._flush_task:
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass

        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        # Final flush
        await self._flush_metrics()

    async def _flush_loop(self) -> None:
        """Periodically flush metrics to storage"""
        while True:
            await asyncio.sleep(self.flush_interval)
            await self._flush_metrics()

    async def _cleanup_loop(self) -> None:
        """Periodically clean up old metric files"""
        while True:
            await asyncio.sleep(86400)  # Daily cleanup
            await self._cleanup_old_metrics()

    async def _flush_metrics(self) -> None:
        """Write current metrics to storage"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(
            self.storage_path, f"{self.server_name}_metrics_{timestamp}.json"
        )

        try:
            metrics_data = {
                "timestamp": datetime.now().isoformat(),
                "server": self.server_name,
                "metrics": self.get_all_metrics(),
            }

            with open(filename, "w") as f:
                json.dump(metrics_data, f, indent=2)
        except Exception as e:
            print(f"Error flushing metrics: {str(e)}")

    async def _cleanup_old_metrics(self) -> None:
        """Remove metric files older than retention period"""
        cutoff = datetime.now() - timedelta(days=self.retention_days)

        try:
            for filename in os.listdir(self.storage_path):
                if filename.startswith(f"{self.server_name}_metrics_"):
                    filepath = os.path.join(self.storage_path, filename)
                    file_time = datetime.fromtimestamp(os.path.getctime(filepath))

                    if file_time < cutoff:
                        os.remove(filepath)
        except Exception as e:
            print(f"Error cleaning up old metrics: {str(e)}")


def metric_collector(collector: MetricsCollector, metric_name: str):
    """Decorator to collect function execution metrics"""

    def decorator(func):
        async def wrapper(*args, **kwargs):
            start_time = datetime.now()
            try:
                result = await func(*args, **kwargs)
                duration = (datetime.now() - start_time).total_seconds()
                collector.observe(f"{metric_name}_duration", duration)
                collector.increment(f"{metric_name}_total")
                collector.increment(f"{metric_name}_success")
                return result
            except Exception:
                collector.increment(f"{metric_name}_errors")
                raise

        return wrapper

    return decorator
