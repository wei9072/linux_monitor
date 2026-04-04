import pytest
import asyncio
from backend.manager import SystemDataManager
from backend.schemas import SystemMetrics, CPUInfo, MemoryInfo, NetworkInfo, DiskInfo

def create_mock_metrics(timestamp: float) -> SystemMetrics:
    return SystemMetrics(
        cpu=CPUInfo(usage_percent=0.0, temp_celsius=0.0),
        memory=MemoryInfo(total_gb=0.0, used_gb=0.0, percent=0.0),
        network=NetworkInfo(rx_kbps=0.0, tx_kbps=0.0),
        disk=DiskInfo(read_kbps=0.0, write_kbps=0.0),
        timestamp=timestamp
    )

def test_buffer_fill_and_eviction():
    # Test with small maxlen for quick verification
    manager = SystemDataManager(buffer_size=5)
    
    # Fill buffer
    for i in range(5):
        manager.add_data_point(create_mock_metrics(float(i)))
    
    history = manager.get_history()
    assert len(history) == 5
    assert history[0].timestamp == 0.0
    assert history[4].timestamp == 4.0
    
    # Add one more point, should evict the first one
    manager.add_data_point(create_mock_metrics(5.0))
    history = manager.get_history()
    assert len(history) == 5
    assert history[0].timestamp == 1.0
    assert history[4].timestamp == 5.0

def test_background_task():
    async def run_test():
        # Test with very small interval
        manager = SystemDataManager(buffer_size=10)
        
        # Start loop manually (or use start() which uses asyncio.create_task)
        # Since we want to control timing, we can run it for a bit
        task = asyncio.create_task(manager.collect_metrics_loop(interval=0.1))
        
        await asyncio.sleep(0.35) # Should collect about 3-4 points
        
        manager.is_running = False # Stop the loop
        try:
            await asyncio.wait_for(task, timeout=1.0)
        except asyncio.TimeoutError:
            pass
        
        history = manager.get_history()
        assert len(history) >= 2 # At least 2 points collected
        
        latest = manager.get_latest()
        assert latest is not None
        assert latest == history[-1]
    
    asyncio.run(run_test())
