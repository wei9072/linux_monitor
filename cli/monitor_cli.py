import asyncio
import json
import sys
import argparse
import requests
import websockets
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.panel import Panel
from rich.layout import Layout
from datetime import datetime

console = Console()

def get_color(value: float, warning: float = 70.0, danger: float = 90.0) -> str:
    """Return color based on value thresholds."""
    if value >= danger:
        return "bold red"
    if value >= warning:
        return "bold yellow"
    return "green"

def create_dashboard(metrics: dict) -> Layout:
    """Create a rich layout for the dashboard."""
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="main"),
        Layout(name="footer", size=3)
    )
    
    # Header
    time_str = datetime.fromtimestamp(metrics.get("timestamp", 0)).strftime("%Y-%m-%d %H:%M:%S")
    layout["header"].update(Panel(f"[bold cyan]Linux System Monitor[/bold cyan] | Last Updated: {time_str}", style="blue"))
    
    # Main content - Table
    table = Table(expand=True)
    table.add_column("Category", style="cyan", no_wrap=True)
    table.add_column("Metric", style="magenta")
    table.add_column("Value", justify="right")
    
    # CPU
    cpu = metrics.get("cpu", {})
    usage = cpu.get("usage_percent", 0)
    table.add_row("CPU", "Usage %", f"[{get_color(usage)}]{usage}%[/]")
    table.add_row("CPU", "Temperature", f"{cpu.get('temp_celsius', 0)}°C")
    
    # Memory
    mem = metrics.get("memory", {})
    m_usage = mem.get("percent", 0)
    table.add_row("Memory", "Usage %", f"[{get_color(m_usage)}]{m_usage}%[/]")
    table.add_row("Memory", "Used/Total (GB)", f"{mem.get('used_gb', 0)} / {mem.get('total_gb', 0)} GB")
    
    # Network
    net = metrics.get("network", {})
    table.add_row("Network", "Download (rx)", f"[green]{net.get('rx_kbps', 0)} KB/s[/]")
    table.add_row("Network", "Upload (tx)", f"[blue]{net.get('tx_kbps', 0)} KB/s[/]")
    
    # Disk
    disk = metrics.get("disk", {})
    table.add_row("Disk", "Read Speed", f"{disk.get('read_kbps', 0)} KB/s")
    table.add_row("Disk", "Write Speed", f"{disk.get('write_kbps', 0)} KB/s")
    
    layout["main"].update(table)
    layout["footer"].update(Panel("[dim]Press Ctrl+C to exit monitoring mode[/dim]", style="white"))
    
    return layout

async def run_watch(api_url: str, ws_url: str):
    """Run in continuous watch mode."""
    try:
        async with websockets.connect(ws_url) as websocket:
            # First message might be a list (history)
            initial_data = await websocket.recv()
            data = json.loads(initial_data)
            
            # Use the latest data point from history or initial point
            latest_metrics = data[-1] if isinstance(data, list) else data
            
            with Live(create_dashboard(latest_metrics), refresh_per_second=4, screen=True) as live:
                while True:
                    msg = await websocket.recv()
                    latest_metrics = json.loads(msg)
                    live.update(create_dashboard(latest_metrics))
    except Exception as e:
        console.print(f"[bold red]Error in WebSocket connection:[/bold red] {e}")

def run_once(api_url: str, ws_url: str):
    """Fetch data once and exit."""
    try:
        # We still use WebSocket to get the latest data point
        async def fetch():
            async with websockets.connect(ws_url) as websocket:
                initial_data = await websocket.recv()
                data = json.loads(initial_data)
                latest_metrics = data[-1] if isinstance(data, list) else data
                console.print(create_dashboard(latest_metrics))
        
        asyncio.run(fetch())
    except Exception as e:
        console.print(f"[bold red]Error fetching data:[/bold red] {e}")

def main():
    parser = argparse.ArgumentParser(description="Linux System Monitor CLI Client")
    parser.add_argument("--host", default="localhost", help="Server host")
    parser.add_argument("--port", default="8000", help="Server port")
    parser.add_argument("--watch", action="store_true", help="Enable continuous monitoring mode")
    
    args = parser.parse_args()
    
    api_url = f"http://{args.host}:{args.port}/api/config"
    ws_url = f"ws://{args.host}:{args.port}/ws/metrics"
    
    # Verify server is up
    try:
        resp = requests.get(api_url, timeout=2)
        resp.raise_for_status()
        config = resp.json()
        console.print(f"[green]Connected to Monitor API ({config['appearance']['theme']} theme)[/green]")
    except Exception as e:
        console.print(f"[bold red]Could not connect to server at {api_url}:[/bold red] {e}")
        sys.exit(1)
        
    if args.watch:
        try:
            asyncio.run(run_watch(api_url, ws_url))
        except KeyboardInterrupt:
            console.print("\n[yellow]Monitoring stopped by user.[/yellow]")
    else:
        run_once(api_url, ws_url)

if __name__ == "__main__":
    main()
