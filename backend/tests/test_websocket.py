import pytest
import json
import asyncio
from fastapi.testclient import TestClient
import backend.main as main_module
from backend.schemas import SystemMetrics, CPUInfo, MemoryInfo, NetworkInfo, DiskInfo

pytestmark = pytest.mark.anyio

def create_mock_metrics(timestamp: float) -> SystemMetrics:
    return SystemMetrics(
        cpu=CPUInfo(usage_percent=0.0, temp_celsius=0.0),
        memory=MemoryInfo(total_gb=0.0, used_gb=0.0, percent=0.0),
        network=NetworkInfo(rx_kbps=0.0, tx_kbps=0.0),
        disk=DiskInfo(read_kbps=0.0, write_kbps=0.0),
        timestamp=timestamp
    )

async def test_websocket_history_and_broadcast():
    with TestClient(main_module.app) as client:
        if main_module.manager:
            main_module.manager.stop()
            main_module.manager.buffer.clear()
        
        # Add mock history data
        main_module.manager.add_data_point(create_mock_metrics(1.0))
        main_module.manager.add_data_point(create_mock_metrics(2.0))
        
        with client.websocket_connect("/ws/metrics") as websocket:
            # Receive initial history
            data = websocket.receive_text()
            history = json.loads(data)
            assert isinstance(history, list)
            assert len(history) >= 2
            
async def test_websocket_multiple_connections():
    with TestClient(main_module.app) as client:
        with client.websocket_connect("/ws/metrics") as ws1, \
             client.websocket_connect("/ws/metrics") as ws2:
            
            # Receive history on both
            data1 = ws1.receive_text()
            data2 = ws2.receive_text()
            
            assert isinstance(json.loads(data1), list)
            assert isinstance(json.loads(data2), list)
