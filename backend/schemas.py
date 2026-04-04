from pydantic import BaseModel
from typing import Dict, Any

class CPUInfo(BaseModel):
    usage_percent: float
    temp_celsius: float

class MemoryInfo(BaseModel):
    total_gb: float
    used_gb: float
    percent: float

class NetworkInfo(BaseModel):
    rx_kbps: float
    tx_kbps: float

class DiskInfo(BaseModel):
    read_kbps: float
    write_kbps: float

class SystemMetrics(BaseModel):
    cpu: CPUInfo
    memory: MemoryInfo
    network: NetworkInfo
    disk: DiskInfo
    timestamp: float

class CoreConfig(BaseModel):
    interval: float
    buffer_size: int
    host: str
    port: int

class MetricsConfig(BaseModel):
    cpu: bool
    memory: bool
    network: bool
    disk: bool

class AppearanceConfig(BaseModel):
    theme: str
    primary_color: str
    chart_type: str

class AppConfig(BaseModel):
    core: CoreConfig
    metrics: MetricsConfig
    appearance: AppearanceConfig
