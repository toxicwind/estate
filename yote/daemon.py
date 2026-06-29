#!/usr/bin/env python3
"""Yote Daemon — Background scheduler"""
import time
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("yote-daemon")

def main():
    logger.info("Yote daemon started")
    while True:
        time.sleep(60)

if __name__ == "__main__":
    main()
