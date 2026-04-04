import time
import os
import glob
from typing import Dict, Tuple, Optional
from .schemas import SystemMetrics, CPUInfo, MemoryInfo, NetworkInfo, DiskInfo

class SystemCollector:
    def __init__(self):
        self.prev_cpu: Optional[Tuple[float, float]] = None # (idle, total)
        self.prev_net: Optional[Tuple[float, float, float]] = None # (timestamp, rx, tx)
        self.prev_disk: Optional[Tuple[float, float, float]] = None # (timestamp, read, write)

    def _read_proc_stat(self) -> Tuple[float, float]:
        """Read /proc/stat and return (idle, total) times."""
        with open("/proc/stat", "r") as f:
            line = f.readline()
            if not line.startswith("cpu "):
                raise ValueError("Could not find CPU info in /proc/stat")
            
            parts = [float(p) for p in line.split()[1:]]
            # user, nice, system, idle, iowait, irq, softirq, steal, guest, guest_nice
            # total_time = sum(all_values)
            # idle_time = idle + iowait
            idle = parts[3] + parts[4] # idle + iowait
            total = sum(parts)
            return idle, total

    def _read_meminfo(self) -> Dict[str, float]:
        """Read /proc/meminfo and return metrics in kB."""
        metrics = {}
        with open("/proc/meminfo", "r") as f:
            for line in f:
                parts = line.split(":")
                if len(parts) == 2:
                    name = parts[0].strip()
                    value = parts[1].split()[0].strip()
                    metrics[name] = float(value)
        return metrics

    def _read_net_dev(self) -> Tuple[float, float]:
        """Read /proc/net/dev and return (rx_bytes, tx_bytes) summed across interfaces."""
        rx_total = 0.0
        tx_total = 0.0
        with open("/proc/net/dev", "r") as f:
            lines = f.readlines()[2:] # Skip header
            for line in lines:
                parts = line.split(":")
                if len(parts) == 2:
                    iface = parts[0].strip()
                    if iface == "lo":
                        continue
                    stats = parts[1].split()
                    rx_total += float(stats[0])
                    tx_total += float(stats[8])
        return rx_total, tx_total

    def _read_diskstats(self) -> Tuple[float, float]:
        """Read /proc/diskstats and return (read_bytes, write_bytes)."""
        read_total = 0.0
        write_total = 0.0
        # Sector size is usually 512 bytes
        SECTOR_SIZE = 512
        with open("/proc/diskstats", "r") as f:
            for line in f:
                parts = line.split()
                # Field 3 is device name, field 5 is sectors read, field 9 is sectors written
                # According to kernel docs, field 4-7 are read related, 8-11 are write related.
                # Actually, in modern kernels:
                # 0: major, 1: minor, 2: name, 3: reads completed, 4: reads merged, 5: sectors read, 6: time spent reading
                # 7: writes completed, 8: writes merged, 9: sectors written, 10: time spent writing
                # We skip partitions and only count main disks (e.g., sda, nvme0n1)
                # Simple rule: if it ends with a digit (like sda1), skip? No, nvme0n1 ends with 1.
                # Usually we want to aggregate or just take everything.
                # Let's aggregate everything that looks like a main disk or just aggregate all.
                # Actually, summing everything might double count (disk + partitions).
                # A common heuristic is to only count devices without digits or with specific names.
                # Let's just sum everything and divide by 2? No, that's not good.
                # For simplicity, let's sum only if it doesn't match common partition patterns or just sum all for now.
                # Better: only include devices that are directly in /sys/block/
                dev_name = parts[2]
                if os.path.exists(f"/sys/block/{dev_name}"):
                    read_total += float(parts[5]) * SECTOR_SIZE
                    write_total += float(parts[9]) * SECTOR_SIZE
        return read_total, write_total

    def _read_temp(self) -> float:
        """Read temperature from /sys/class/thermal/thermal_zone*/temp."""
        temps = []
        for path in glob.glob("/sys/class/thermal/thermal_zone*/temp"):
            try:
                with open(path, "r") as f:
                    # temp is in millicelsius
                    temps.append(float(f.read().strip()) / 1000.0)
            except (OSError, ValueError):
                continue
        return max(temps) if temps else 0.0

    def collect(self) -> SystemMetrics:
        now = time.time()
        
        # CPU
        curr_idle, curr_total = self._read_proc_stat()
        cpu_usage = 0.0
        if self.prev_cpu:
            prev_idle, prev_total = self.prev_cpu
            delta_idle = curr_idle - prev_idle
            delta_total = curr_total - prev_total
            if delta_total > 0:
                cpu_usage = (1.0 - delta_idle / delta_total) * 100.0
        self.prev_cpu = (curr_idle, curr_total)
        
        # Temp
        temp_c = self._read_temp()
        
        # Memory
        mem = self._read_meminfo()
        total_gb = mem.get("MemTotal", 0) / (1024 * 1024)
        available_gb = mem.get("MemAvailable", mem.get("MemFree", 0) + mem.get("Buffers", 0) + mem.get("Cached", 0)) / (1024 * 1024)
        used_gb = total_gb - available_gb
        mem_percent = (used_gb / total_gb * 100.0) if total_gb > 0 else 0.0
        
        # Network
        curr_rx, curr_tx = self._read_net_dev()
        rx_kbps = 0.0
        tx_kbps = 0.0
        if self.prev_net:
            prev_time, prev_rx, prev_tx = self.prev_net
            delta_time = now - prev_time
            if delta_time > 0:
                rx_kbps = (curr_rx - prev_rx) / delta_time / 1024.0
                tx_kbps = (curr_tx - prev_tx) / delta_time / 1024.0
        self.prev_net = (now, curr_rx, curr_tx)
        
        # Disk
        curr_read, curr_write = self._read_diskstats()
        read_kbps = 0.0
        write_kbps = 0.0
        if self.prev_disk:
            prev_time, prev_read, prev_write = self.prev_disk
            delta_time = now - prev_time
            if delta_time > 0:
                read_kbps = (curr_read - prev_read) / delta_time / 1024.0
                write_kbps = (curr_write - prev_write) / delta_time / 1024.0
        self.prev_disk = (now, curr_read, curr_write)

        return SystemMetrics(
            cpu=CPUInfo(usage_percent=round(cpu_usage, 2), temp_celsius=round(temp_c, 2)),
            memory=MemoryInfo(total_gb=round(total_gb, 2), used_gb=round(used_gb, 2), percent=round(mem_percent, 2)),
            network=NetworkInfo(rx_kbps=round(rx_kbps, 2), tx_kbps=round(tx_kbps, 2)),
            disk=DiskInfo(read_kbps=round(read_kbps, 2), write_kbps=round(write_kbps, 2)),
            timestamp=now
        )
