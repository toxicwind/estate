#!/usr/bin/env python3
# yote-daemon — Yote API daemon serving health status and logs to the dashboard
import os
import sys
import argparse
from pathlib import Path
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from yote.agent import YoteAgent, SERVICE_PORTS, SERVICE_LOG_PATHS

app = FastAPI(title="Yote Daemon API", version="1.0.0")

# Enable CORS so the dashboard can access the API from different origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ActionRequest(BaseModel):
    action: str  # start, stop, restart

@app.get("/health")
def get_health():
    return {"status": "healthy"}

@app.get("/status")
def get_status():
    try:
        agent = YoteAgent()
        # Query health status of all configured services
        status_data = {}
        for name in agent.config["services"]:
            port = SERVICE_PORTS.get(name)
            is_healthy = False
            if port:
                is_healthy = agent._health_check(name, port)
            else:
                is_healthy = agent._process_running(name)
            
            # Check PID
            pid = None
            pid_file = Path(f"/home/toxic/sovereign/pids/{name}.pid")
            if pid_file.exists():
                try:
                    pid = int(pid_file.read_text().strip())
                except:
                    pass
            
            status_data[name] = {
                "status": "healthy" if is_healthy else "offline",
                "pid": pid,
                "port": port
            }
        return status_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/logs/{service}")
def get_logs(service: str, lines: int = 50):
    if service not in SERVICE_LOG_PATHS:
        raise HTTPException(status_code=404, detail="Service not found")
    
    log_path = SERVICE_LOG_PATHS[service]
    if not log_path.exists():
        return {"service": service, "logs": [], "error": f"Log file {log_path} not found"}
    
    try:
        with open(log_path, "r") as f:
            content = f.readlines()
        return {"service": service, "logs": [line.strip() for line in content[-lines:]]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/actions/{service}")
def trigger_action(service: str, req: ActionRequest):
    agent = YoteAgent()
    if service not in agent.config["services"]:
        raise HTTPException(status_code=404, detail="Service not found")
    
    action = req.action.lower()
    if action == "start":
        success = agent._start_service(service)
    elif action == "stop":
        success = agent._stop_service(service)
    elif action == "restart":
        agent._stop_service(service)
        import time
        time.sleep(2)
        success = agent._start_service(service)
    else:
        raise HTTPException(status_code=400, detail="Invalid action. Use: start, stop, restart")
        
    return {"service": service, "action": action, "success": success}

def main():
    parser = argparse.ArgumentParser(description="Yote Daemon API Server")
    parser.add_argument("--port", type=int, default=25010, help="Port to listen on")
    args = parser.parse_args()
    
    uvicorn.run("yote.daemon:app", host="0.0.0.0", port=args.port, reload=False)

if __name__ == "__main__":
    main()
