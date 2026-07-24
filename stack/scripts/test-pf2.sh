#!/bin/bash
echo "pre-pitchfork"
# Redirect /dev/tty too since pitchfork writes there directly
/home/toxic/.local/bin/pitchfork --version </dev/null >/dev/null 2>&1 </dev/tty 2>/dev/null
echo "post-pitchfork"
