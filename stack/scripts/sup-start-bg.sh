#!/bin/bash
cd /home/toxic/sovereign
rm -f /home/toxic/.local/state/pitchfork/state.toml
rm -f /home/toxic/.local/state/pitchfork/sock/*
/home/toxic/.local/bin/pitchfork supervisor start </dev/null >/dev/null 2>&1
echo "DONE rc=$?"
