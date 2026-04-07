---
title: Linux Monitor
emoji: 📈
colorFrom: indigo
colorTo: gray
sdk: docker
pinned: false
license: apache-2.0
---

# 🐧 Linux Monitor | System Intelligence Dashboard

A high-performance, real-time Linux system monitoring solution with a modern, data-dense interface. Designed for system administrators and power users who need instant visibility into their infrastructure.

## ✨ Key Features

- **🚀 Real-time Monitoring**: Sub-second updates for critical system metrics using WebSockets.
- **📊 Modern Intelligence UI**:
  - **OLED Dark Mode**: Deep black aesthetic optimized for low-light environments and eye comfort.
  - **Glassmorphism Design**: Sophisticated translucent interface with backdrop-blur effects.
  - **Bento Grid Layout**: Efficient, responsive grid system for high information density.
  - **Pro Typography**: Utilizing *Fira Code* and *Fira Sans* for technical precision and readability.
- **📈 Comprehensive Metrics**:
  - **CPU Utilization**: Real-time load and multi-core performance tracking.
  - **Memory Load**: Instant RAM and swap usage analytics.
  - **Network Throughput**: Live monitoring of RX/TX traffic.
  - **Storage I/O**: Real-time disk read/write activity.
- **🛠️ Fully Configurable**: Adjust collection intervals, buffer sizes, and interface themes via YAML.

## 🏗️ Technology Stack

- **Backend**: Python 3.12, FastAPI, Psutil, PyYAML.
- **Frontend**: Vue 3 (Composition API), ECharts 5, Tailwind CSS 3.
- **Communication**: High-speed WebSockets for bidirectional data streaming.
- **Deployment**: Optimized Docker container for universal compatibility.

## 🚀 Quick Start

### 1. Using Docker (Recommended)

```bash
docker build -t linux-monitor .
docker run -p 8000:8000 linux-monitor
```

### 2. Manual Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Run the server
python -m backend.main
```

The dashboard will be available at `http://localhost:8000`.

## ⚙️ Configuration

Modify `backend/config.yaml` to customize your instance:

```yaml
core:
  interval: 1.0        # Data collection interval (seconds)
  buffer_size: 100     # Data points kept in memory
  port: 8000           # Server port

metrics:
  cpu: true
  memory: true
  network: true
  disk: true
```

---
*Created with 💙 for the Linux Community.*
