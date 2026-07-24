#!/bin/bash
export WAYLAND_DISPLAY=wayland-1
export XDG_RUNTIME_DIR=/run/user/1000
export DISPLAY=:0

google-chrome \
  --no-sandbox \
  --ozone-platform=wayland \
  --new-window \
  "https://build.nvidia.com" \
  "https://openrouter.ai/keys" \
  "https://console.groq.com/keys" \
  "https://platform.deepseek.com" \
  "https://open.bigmodel.cn" \
  "https://dash.llm7.io" \
  "https://huggingface.co/settings/tokens" \
  "https://context7.com/dashboard" \
  "https://cloud.cerebras.ai" \
  "https://console.clerk.com" \
  "https://dash.cloudflare.com/profile/api-tokens" \
  "https://sentry.io/settings/auth-tokens" \
  "https://github.com/settings/tokens" \
  "https://makersuite.google.com/app/apikey" &
