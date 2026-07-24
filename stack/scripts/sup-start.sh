#!/bin/bash
echo "step1: cleaning state"
rm -f /home/toxic/.local/state/pitchfork/state.toml
rm -f /home/toxic/.local/state/pitchfork/sock/*
echo "step2: state cleaned"
echo "step3: starting supervisor"
cd /home/toxic/sovereign
/home/toxic/.local/bin/pitchfork supervisor start </dev/null >/dev/null 2>&1
echo "step4: supervisor_start_done rc=$?"
