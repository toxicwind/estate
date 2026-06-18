#!/usr/bin/env python3
# yote-process — CLI tool to check processes
import sys
import argparse
from yote.agent import YoteAgent

def main():
    parser = argparse.ArgumentParser(description="Yote Process Status CLI")
    parser.add_argument("--check", action="store_true", help="Check if all processes are running")
    args = parser.parse_args()
    
    agent = YoteAgent()
    all_running = True
    for name in agent.config["services"]:
        running = agent._process_running(name)
        if running:
            print(f"{name}: RUNNING")
        else:
            print(f"{name}: STOPPED")
            all_running = False
            
    if not all_running:
        sys.exit(1)

if __name__ == "__main__":
    main()
