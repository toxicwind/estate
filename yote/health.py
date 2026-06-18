#!/usr/bin/env python3
# yote-health — CLI tool to check stack health and return JSON
import json
import argparse
from yote.agent import YoteAgent, SERVICE_PORTS

def main():
    parser = argparse.ArgumentParser(description="Yote Health Check CLI")
    parser.add_argument("--json", action="store_true", help="Print status in JSON format")
    args = parser.parse_args()
    
    agent = YoteAgent()
    status_data = {}
    for name in agent.config["services"]:
        port = SERVICE_PORTS.get(name)
        is_healthy = False
        if port:
            is_healthy = agent._health_check(name, port)
        else:
            is_healthy = agent._process_running(name)
        status_data[name] = "healthy" if is_healthy else "offline"
        
    if args.json:
        print(json.dumps(status_data, indent=2))
    else:
        for name, status in status_data.items():
            print(f"{name}: {status}")

if __name__ == "__main__":
    main()
