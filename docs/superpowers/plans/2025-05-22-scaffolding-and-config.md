# Task 1: Scaffolding & Config Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create the basic configuration, data models, and FastAPI skeleton for the Linux System Monitor Dashboard.

**Architecture:** 
- `config.yaml`: Centralized configuration using YAML.
- `schemas.py`: Pydantic models for data validation and API documentation.
- `main.py`: FastAPI application entry point with a `/api/config` endpoint.

**Tech Stack:** FastAPI, Pydantic, PyYAML, Uvicorn.

---

### Task 1.1: Create `backend/config.yaml`

**Files:**
- Create: `backend/config.yaml`

- [ ] **Step 1: Write `backend/config.yaml`**

```yaml
core:
  interval: 1.0        # Data collection interval in seconds
  buffer_size: 100     # Number of data points to keep in memory
  host: "0.0.0.0"      # Server host
  port: 8000           # Server port

metrics:
  cpu: true
  memory: true
  network: true
  disk: true

appearance:
  theme: "dark"
  primary_color: "#3498db"
  chart_type: "line"
```

- [ ] **Step 2: Commit**

```bash
git add backend/config.yaml
git commit -m "feat: add config.yaml"
```

---

### Task 1.2: Create `backend/schemas.py`

**Files:**
- Create: `backend/schemas.py`

- [ ] **Step 1: Write `backend/schemas.py`**

```python
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
```

- [ ] **Step 2: Commit**

```bash
git add backend/schemas.py
git commit -m "feat: add pydantic schemas"
```

---

### Task 1.3: Create `backend/main.py`

**Files:**
- Create: `backend/main.py`

- [ ] **Step 1: Write `backend/main.py`**

```python
import yaml
from pathlib import Path
from fastapi import FastAPI
from .schemas import AppConfig

app = FastAPI(title="Linux System Monitor API")

def load_config() -> AppConfig:
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path, "r") as f:
        config_data = yaml.safe_load(f)
    return AppConfig(**config_data)

@app.get("/api/config", response_model=AppConfig)
async def get_config():
    return load_config()

if __name__ == "__main__":
    import uvicorn
    config = load_config()
    uvicorn.run(app, host=config.core.host, port=config.core.port)
```

- [ ] **Step 2: Commit**

```bash
git add backend/main.py
git commit -m "feat: add fastapi skeleton and config endpoint"
```

---

### Task 1.4: Verification

**Files:**
- None

- [ ] **Step 1: Install dependencies**

Run: `pip install fastapi uvicorn PyYAML pydantic`
Expected: Installation completes successfully.

- [ ] **Step 2: Start the server**

Run: `uvicorn backend.main:app --host 0.0.0.0 --port 8000`
Expected: Server starts and listens on port 8000.

- [ ] **Step 3: Test the `/api/config` endpoint**

Run: `curl http://localhost:8000/api/config`
Expected: JSON response matching `config.yaml`.

- [ ] **Step 4: Commit**

```bash
git commit -m "chore: verify Task 1 implementation"
```
