#!/usr/bin/env python3
# yote-logs — CLI tool to stream service logs
import sys
import argparse
import time
from yote.agent import SERVICE_LOG_PATHS

def main():
    parser = argparse.ArgumentParser(description="Yote Logs Streaming CLI")
    parser.add_argument("service", nargs="?", default=None, help="Service name")
    parser.add_argument("--follow", "-f", action="store_true", help="Follow log output")
    args = parser.parse_args()
    
    if not args.service:
        print("Available services:")
        for name in SERVICE_LOG_PATHS:
            print(f"  {name}")
        sys.exit(0)
        
    if args.service not in SERVICE_LOG_PATHS:
        print(f"Error: Unknown service {args.service}", file=sys.stderr)
        sys.exit(1)
        
    log_path = SERVICE_LOG_PATHS[args.service]
    if not log_path.exists():
        print(f"Error: Log file {log_path} not found.", file=sys.stderr)
        sys.exit(1)
        
    if args.follow:
        try:
            with open(log_path, "r") as f:
                # Go to the end of the file
                f.seek(0, 2)
                while True:
                    line = f.readline()
                    if not line:
                        time.sleep(0.1)
                        continue
                    print(line, end="")
        except KeyboardInterrupt:
            sys.exit(0)
    else:
        with open(log_path, "r") as f:
            lines = f.readlines()
            for line in lines[-50:]:
                print(line, end="")

if __name__ == "__main__":
    main()
