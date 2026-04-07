import asyncio
import collections
import time
import inspect
from typing import List, Optional, Callable, Any
from .collector import SystemCollector
from .schemas import SystemMetrics

class SystemDataManager:
    def __init__(self, buffer_size: int = 60):
        self.collector = SystemCollector()
        self.buffer = collections.deque(maxlen=buffer_size)
        self.is_running = False
        self._task: Optional[asyncio.Task] = None
        self.broadcast_callback: Optional[Callable[[SystemMetrics], Any]] = None

    def add_data_point(self, metrics: SystemMetrics):
        """Add a data point to the buffer."""
        self.buffer.append(metrics)
        if self.broadcast_callback:
            if inspect.iscoroutinefunction(self.broadcast_callback):
                asyncio.create_task(self.broadcast_callback(metrics))
            else:
                self.broadcast_callback(metrics)

    def get_history(self) -> List[SystemMetrics]:
        """Return all buffered data points as a list."""
        return list(self.buffer)

    def get_latest(self) -> Optional[SystemMetrics]:
        """Return the latest data point."""
        if self.buffer:
            return self.buffer[-1]
        return None

    async def collect_metrics_loop(self, interval: float = 1.0):
        """Background loop for collecting data."""
        self.is_running = True
        while self.is_running:
            try:
                # Perform the collection
                metrics = self.collector.collect()
                self.add_data_point(metrics)
            except Exception as e:
                # In a real app we'd log this
                print(f"Error collecting data: {e}")
            
            await asyncio.sleep(interval)

    def start(self, interval: float = 1.0):
        """Start the background collection task."""
        if self._task is None or self._task.done():
            # We use asyncio.create_task to run it in the background
            # Note: This requires an already running loop (like in FastAPI)
            self._task = asyncio.create_task(self.collect_metrics_loop(interval))

    def stop(self):
        """Stop the background collection task."""
        self.is_running = False
        if self._task:
            self._task.cancel()
            self._task = None
