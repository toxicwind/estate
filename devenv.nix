{ config, pkgs, ... }:
{
  # Define packages
  packages = with pkgs; [
    caddy
    process-compose
  ];

  # Define environment variables
  env = {
    SOVEREIGN_HOME = "/home/toxic/sovereign";
    MODEL_PATH = "/home/toxic/models/Qwen3.6-27B-Heretic-UD/heretic-UD-27B-Q5_K_XL.gguf";
    PYTHONUNBUFFERED = "1";
    TELEGRAM_BOT_TOKEN = "8932201107:AAEZ7I2NBcGR_CcJvT9IjKwbZ8honLNc_zM";
    OPENFANG_LISTEN = "127.0.0.1:25004";
    TELEGRAM_ALLOWED_USERS = "716302190,13036673831";
    PYTHONPATH = "/home/toxic/sovereign";
  };

  # Define processes to run under process-compose
  processes = {
    llama-server.exec = "/home/toxic/sovereign/bin/llama-server -m /home/toxic/models/Qwen3.6-27B-Heretic-UD/heretic-UD-27B-Q5_K_XL.gguf --mmproj /home/toxic/models/Qwen3.6-27B-Heretic-UD/mmproj-27B-F16.gguf --host 0.0.0.0 --port 25001 --jinja --n-gpu-layers 60 --ctx-size 77824 --cache-type-k q4_0 --cache-type-v q4_0 --flash-attn on --no-context-shift --parallel 4 --cont-batching --defrag-thold 0.1 --slot-prompt-similarity 0.6 --reasoning on --reasoning-format deepseek --parallel-tool-calls --samplers \"top_k;top_p;min_p;temperature\" --temp 0.4 --top-k 40 --top-p 0.9 --min-p 0.05 --repeat-penalty 1.08 --repeat-last-n 1024 --metrics -b 4096 -ub 1024 --webui none";
    
    nfcot_proxy.exec = "python3 /home/toxic/sovereign/modules/nfcot_proxy.py";
    
    openfang.exec = "/home/toxic/.openfang/bin/openfang start";
    
    sovereign_watchdog.exec = "python3 /home/toxic/sovereign/modules/sovereign_watchdog.py";
    
    yote_telegram.exec = "python3 /home/toxic/sovereign/modules/yote_telegram.py";
    
    yote_daemon.exec = "python3 -m yote.daemon --port 25042";
    
    telethon_overlord.exec = "/home/toxic/agents/telethon_overlord/venv/bin/python3 /home/toxic/agents/telethon_overlord/overlord.py";
  };
}
