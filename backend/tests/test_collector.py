import unittest
from unittest.mock import patch, mock_open
import os
from backend.collector import SystemCollector
from backend.schemas import SystemMetrics

class TestSystemCollector(unittest.TestCase):
    def setUp(self):
        self.collector = SystemCollector()

    @patch("builtins.open")
    @patch("os.path.exists")
    @patch("glob.glob")
    @patch("time.time")
    def test_collect_initial(self, mock_time, mock_glob, mock_exists, mock_file):
        # Initial collection should return 0 for delta-based metrics
        mock_time.return_value = 1000.0
        mock_glob.return_value = ["/sys/class/thermal/thermal_zone0/temp"]
        mock_exists.side_effect = lambda p: p == "/sys/block/sda"
        
        # Mock file content
        file_contents = {
            "/proc/stat": "cpu  100 0 50 2000 10 0 0 0 0 0\n",
            "/proc/meminfo": "MemTotal:       16000000 kB\nMemAvailable:    8000000 kB\n",
            "/proc/net/dev": "header\nheader\n  eth0:    1024 0 0 0 0 0 0 0     2048 0 0 0 0 0 0 0\n",
            "/proc/diskstats": "   8       0 sda 0 0 2048 0 0 0 4096 0 0 0 0\n",
            "/sys/class/thermal/thermal_zone0/temp": "50000\n"
        }
        
        def open_side_effect(path, mode="r"):
            if path in file_contents:
                return mock_open(read_data=file_contents[path])(path, mode)
            raise FileNotFoundError(path)
            
        mock_file.side_effect = open_side_effect
        
        metrics = self.collector.collect()
        
        self.assertIsInstance(metrics, SystemMetrics)
        self.assertEqual(metrics.cpu.usage_percent, 0.0)
        self.assertEqual(metrics.cpu.temp_celsius, 50.0)
        self.assertEqual(metrics.memory.total_gb, round(16000000 / (1024*1024), 2))
        self.assertEqual(metrics.memory.percent, 50.0)
        self.assertEqual(metrics.network.rx_kbps, 0.0)
        self.assertEqual(metrics.network.tx_kbps, 0.0)
        self.assertEqual(metrics.disk.read_kbps, 0.0)
        self.assertEqual(metrics.disk.write_kbps, 0.0)

    @patch("builtins.open")
    @patch("os.path.exists")
    @patch("glob.glob")
    @patch("time.time")
    def test_collect_delta(self, mock_time, mock_glob, mock_exists, mock_file):
        mock_glob.return_value = ["/sys/class/thermal/thermal_zone0/temp"]
        mock_exists.side_effect = lambda p: p == "/sys/block/sda"
        
        # Sample 1
        mock_time.return_value = 1000.0
        file_contents_1 = {
            "/proc/stat": "cpu  100 0 50 2000 10 0 0 0 0 0\n",
            "/proc/meminfo": "MemTotal:       16000000 kB\nMemAvailable:    8000000 kB\n",
            "/proc/net/dev": "header\nheader\n  eth0:    1024 0 0 0 0 0 0 0     2048 0 0 0 0 0 0 0\n",
            "/proc/diskstats": "   8       0 sda 0 0 2048 0 0 0 4096 0 0 0 0\n",
            "/sys/class/thermal/thermal_zone0/temp": "50000\n"
        }
        
        def open_side_effect_1(path, mode="r"):
            return mock_open(read_data=file_contents_1.get(path, ""))(path, mode)
        
        mock_file.side_effect = open_side_effect_1
        self.collector.collect()
        
        # Sample 2 (1 second later)
        mock_time.return_value = 1001.0
        # CPU: Delta Total = 175, Delta Idle = 105, Usage = 40%
        # Net: Delta RX = 1024 bytes, Delta TX = 2048 bytes -> 1 kbps, 2 kbps
        # Disk: Delta Read = 1024 * 512 bytes = 512 KB, Delta Write = 2048 * 512 bytes = 1024 KB -> 512 kbps, 1024 kbps
        file_contents_2 = {
            "/proc/stat": "cpu  150 0 70 2100 15 0 0 0 0 0\n",
            "/proc/meminfo": "MemTotal:       16000000 kB\nMemAvailable:    8000000 kB\n",
            "/proc/net/dev": "header\nheader\n  eth0:    2048 0 0 0 0 0 0 0     4096 0 0 0 0 0 0 0\n",
            "/proc/diskstats": "   8       0 sda 0 0 3072 0 0 0 6144 0 0 0 0\n",
            "/sys/class/thermal/thermal_zone0/temp": "55000\n"
        }
        
        def open_side_effect_2(path, mode="r"):
            return mock_open(read_data=file_contents_2.get(path, ""))(path, mode)
            
        mock_file.side_effect = open_side_effect_2
        metrics = self.collector.collect()
        
        self.assertEqual(metrics.cpu.usage_percent, 40.0)
        self.assertEqual(metrics.cpu.temp_celsius, 55.0)
        self.assertEqual(metrics.network.rx_kbps, 1.0)
        self.assertEqual(metrics.network.tx_kbps, 2.0)
        self.assertEqual(metrics.disk.read_kbps, 512.0)
        self.assertEqual(metrics.disk.write_kbps, 1024.0)

if __name__ == "__main__":
    unittest.main()
