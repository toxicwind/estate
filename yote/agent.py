#!/usr/bin/env python3
# yote-agent — Yote autonomous process supervisor
# Monitors services, auto-restarts failures, logs to central store

import os
import sys
import time
import json
import yaml
import signal
import logging
import subprocess
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor

# Configuration defaults
CONFIG_PATHS = [
    Path("/home/toxic/sovereign/config/yote_agent.yaml"),
    Path.home() / ".config" / "yote" / "agent.yaml",
]

SERVICE_PORTS = {
    "vllm": 25001,
    "pegaflow": 25002,
    "openfang": 25004,
    "ouroboros": 25005,
    "caddy": 25000,
    "yote-daemon": 25042,
}

SERVICE_COMMANDS = {
    "vllm": ["pixi", "run", "--environment", "inference", "vllm"],
    "pegaflow": ["pixi", "run", "--environment", "inference", "pegaflow"],
    "openfang": ["pixi", "run", "--environment", "inference", "openfang"],
    "ouroboros": ["pixi", "run", "--environment", "app", "ouroboros"],
    "caddy": ["pixi", "run", "--environment", "edge", "caddy"],
    "yote-daemon": ["pixi", "run", "--environment", "inference", "yote-daemon"],
}

SERVICE_LOG_PATHS = {
    "vllm": Path("/home/toxic/sovereign/logs/vllm.log"),
    "pegaflow": Path("/home/toxic/sovereign/logs/pegaflow.log"),
    "openfang": Path("/home/toxic/sovereign/logs/openfang.log"),
    "ouroboros": Path("/home/toxic/sovereign/logs/ouroboros.log"),
    "caddy": Path("/home/toxic/sovereign/logs/caddy.log"),
    "yote-daemon": Path("/home/toxic/sovereign/logs/yote-daemon.log"),
}

@dataclass
class ServiceState:
    name: str
    pid: Optional[int] = None
    status: str = "unknown"  # unknown, running, stopped, crashed
    last_health: Optional[float] = None
    restart_count: int = 0
    last_restart: Optional[float] = None

class YoteAgent:
    def __init__(self, config_path: Optional[Path] = None):
        self.services: Dict[str, ServiceState] = {}
        self.running = True
        self.config = self._load_config(config_path)
        self._setup_logging()
        
    def _load_config(self, config_path: Optional[Path] = None) -> dict:
        """Load YAML configuration or use defaults."""
        if config_path and config_path.exists():
            with open(config_path) as f:
                return yaml.safe_load(f)
        
        for path in CONFIG_PATHS:
            if path.exists():
                with open(path) as f:
                    return yaml.safe_load(f)
        
        # Default configuration
        return {
            "check_interval": 30,
            "health_timeout": 3,
            "max_restarts": 5,
            "restart_window": 300,  # seconds
            "log_retention_days": 7,
            "services": list(SERVICE_PORTS.keys()),
        }
    
    def _setup_logging(self):
        """Configure structured logging."""
        log_dir = Path("/home/toxic/sovereign/logs")
        log_dir.mkdir(parents=True, exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(message)s",
            handlers=[
                logging.FileHandler(log_dir / "agent.log"),
                logging.StreamHandler(),
            ],
        )
        self.logger = logging.getLogger("yote-agent")
    
    def _health_check(self, service_name: str, port: int, timeout: int = 3) -> bool:
        """Check service health via HTTP endpoint."""
        import urllib.request
        import urllib.error
        
        try:
            url = f"http://localhost:{port}/health"
            if service_name == "openfang":
                url = f"http://localhost:{port}/api/health"
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.status == 200
        except (urllib.error.URLError, TimeoutError, ConnectionRefusedError):
            return False
    
    def _process_running(self, service_name: str, pid_file: Optional[Path] = None) -> bool:
        """Check if process is running via PID file or pgrep."""
        pid_file = pid_file or Path(f"/home/toxic/sovereign/pids/{service_name}.pid")
        
        if pid_file.exists():
            try:
                pid = int(pid_file.read_text().strip())
                os.kill(pid, 0)
                return True
            except (ValueError, ProcessLookupError, FileNotFoundError):
                pass
        
        # Fallback: pgrep
        result = subprocess.run(
            ["pgrep", "-f", service_name],
            capture_output=True,
            text=True,
        )
        return result.returncode == 0
    
    def _start_service(self, service_name: str) -> bool:
        """Start a service using its pixi command."""
        if service_name not in SERVICE_COMMANDS:
            self.logger.error(f"No start command defined for {service_name}")
            return False
        
        cmd = SERVICE_COMMANDS[service_name]
        self.logger.info(f"Starting {service_name}: {' '.join(cmd)}")
        
        try:
            # Start process, capture PID
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True,
            )
            
            # Write PID file
            pid_file = Path(f"/home/toxic/sovereign/pids/{service_name}.pid")
            pid_file.parent.mkdir(parents=True, exist_ok=True)
            pid_file.write_text(str(process.pid))
            
            # Update state
            if service_name in self.services:
                self.services[service_name].pid = process.pid
                self.services[service_name].restart_count += 1
                self.services[service_name].last_restart = time.time()
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to start {service_name}: {e}")
            return False
    
    def _stop_service(self, service_name: str) -> bool:
        """Gracefully stop a service."""
        pid_file = Path(f"/home/toxic/sovereign/pids/{service_name}.pid")
        
        if pid_file.exists():
            try:
                pid = int(pid_file.read_text().strip())
                os.kill(pid, signal.SIGTERM)
                time.sleep(2)
                
                # Force kill if still running
                try:
                    os.kill(pid, 0)
                    os.kill(pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                
                pid_file.unlink(missing_ok=True)
                return True
            except Exception as e:
                self.logger.warning(f"Error stopping {service_name}: {e}")
        
        # Fallback: pkill
        subprocess.run(["pkill", "-f", service_name], capture_output=True)
        return True
    
    def _check_and_recover(self, service_name: str) -> None:
        """Check a single service and attempt recovery if needed."""
        state = self.services.get(service_name)
        if not state:
            state = ServiceState(name=service_name)
            self.services[service_name] = state
        
        port = SERVICE_PORTS.get(service_name)
        is_healthy = False
        
        if port:
            is_healthy = self._health_check(service_name, port)
        else:
            is_healthy = self._process_running(service_name)
        
        if is_healthy:
            if state.status != "running":
                self.logger.info(f"{service_name} recovered and healthy")
                state.status = "running"
                state.restart_count = 0
            return
        
        # Service is unhealthy
        self.logger.warning(f"{service_name} unhealthy, checking restart limits...")
        
        # Check restart limits
        if state.restart_count >= self.config["max_restarts"]:
            elapsed = time.time() - (state.last_restart or 0)
            if elapsed < self.config["restart_window"]:
                self.logger.error(f"{service_name} exceeded restart limit, manual intervention required")
                state.status = "crashed"
                return
        
        # Attempt restart
        self.logger.info(f"Restarting {service_name} (attempt {state.restart_count + 1})")
        self._stop_service(service_name)
        time.sleep(2)
        
        if self._start_service(service_name):
            self.logger.info(f"{service_name} restarted successfully")
            state.status = "running"
        else:
            self.logger.error(f"{service_name} failed to start")
            state.status = "crashed"
    
    def run(self):
        """Main supervisor loop."""
        self.logger.info("🐺 YOTE Agent starting — supervising services")
        
        # Initial service state
        for name in self.config["services"]:
            if name not in SERVICE_PORTS:
                self.logger.warning(f"No port defined for {name}, will use process checking only")
            self.services[name] = ServiceState(name=name)
        
        # Register signal handlers for graceful shutdown
        def shutdown_handler(signum, frame):
            self.logger.info("Received shutdown signal, stopping all services...")
            self.running = False
            
            for name in self.services:
                self._stop_service(name)
            
            sys.exit(0)
        
        signal.signal(signal.SIGINT, shutdown_handler)
        signal.signal(signal.SIGTERM, shutdown_handler)
        
        # Main supervision loop
        while self.running:
            for name in self.config["services"]:
                self._check_and_recover(name)
            
            time.sleep(self.config["check_interval"])
    
    def status_json(self) -> str:
        """Return service status as JSON."""
        return json.dumps({
            name: {
                "status": state.status,
                "pid": state.pid,
                "restart_count": state.restart_count,
                "last_restart": state.last_restart,
            }
            for name, state in self.services.items()
        }, indent=2)

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Yote Autonomous Service Agent")
    parser.add_argument("--config", type=Path, help="Path to YAML config file")
    parser.add_argument("--status", action="store_true", help="Print JSON status and exit")
    parser.add_argument("--start", metavar="SERVICE", help="Start a service")
    parser.add_argument("--stop", metavar="SERVICE", help="Stop a service")
    parser.add_argument("--restart", metavar="SERVICE", help="Restart a service")
    
    args = parser.parse_args()
    agent = YoteAgent(config_path=args.config)
    
    if args.status:
        print(agent.status_json())
    elif args.start:
        agent._start_service(args.start)
    elif args.stop:
        agent._stop_service(args.stop)
    elif args.restart:
        agent._stop_service(args.restart)
        time.sleep(2)
        agent._start_service(args.restart)
    else:
        agent.run()

if __name__ == "__main__":
    main()
