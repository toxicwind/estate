#!/bin/bash
echo "=== ESTATE ==="
cd /home/toxic/estate && git branch -vv
echo "---"
cd /home/toxic/estate && git rev-list --left-right --count HEAD...@{u} 2>/dev/null || echo "no upstream"

echo "=== RANCH ==="
cd /home/toxic/estate/ranch && git branch -vv
echo "---"
cd /home/toxic/estate/ranch && git rev-list --left-right --count HEAD...@{u} 2>/dev/null || echo "no upstream"

echo "=== TAU ==="
cd /home/toxic/estate/ranch/tau && git branch -vv
echo "---"
cd /home/toxic/estate/ranch/tau && git rev-list --left-right --count HEAD...@{u} 2>/dev/null || echo "no upstream"