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
    MODEL_PATH = "/home/toxic/models/gemma-4-12B-it-uncensored-Q4_K_M.gguf";
    PYTHONUNBUFFERED = "1";
    TELEGRAM_BOT_TOKEN = "8932201107:AAEZ7I2NBcGR_CcJvT9IjKwbZ8honLNc_zM";
    OPENFANG_LISTEN = "127.0.0.1:25004";
    TELEGRAM_ALLOWED_USERS = "716302190,13036673831";
    PYTHONPATH = "/home/toxic/sovereign";
  };

  # Define processes to run under process-compose
  processes = {
    llama-server.exec = "/home/toxic/ik_llama.cpp-main/build/bin/llama-server -m /home/toxic/models/gemma-4-12B-it-uncensored-Q4_K_M.gguf --host 0.0.0.0 --port 25001 -c 32768 --parallel 1 -b 4096 -ub 1024 -ctk q4_0 -ctv q4_0 --flash-attn 1 -ngl 99 -t 8 --context-shift on --jinja --ctx-checkpoints 32 --ctx-checkpoints-interval 512 --graph-reuse --cache-ram 8192 --no-mmap --embeddings --pooling cls";
    
    nfcot_proxy.exec = "python3 /home/toxic/sovereign/modules/nfcot_proxy.py";
    
    openfang.exec = "/home/toxic/.openfang/bin/openfang start";
    
    sovereign_watchdog.exec = "python3 /home/toxic/sovereign/modules/sovereign_watchdog.py";
    
  };
}
