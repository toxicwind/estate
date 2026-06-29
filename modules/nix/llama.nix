{ LLAMA_FLAGS, ... }: {
  _module.args = {
    llamaServerCmd = ''
      exec /home/toxic/projects/beellama.cpp/build/bin/llama-server \
            -m "${"$"}{MODEL_PATH}" --host 0.0.0.0 --port "${"$"}{LLAMA_SERVER_PORT}" \
            -c ${toString LLAMA_FLAGS.ctx-size} --slots ${toString LLAMA_FLAGS.slots} \
            -b ${toString LLAMA_FLAGS.batch} -ub ${toString LLAMA_FLAGS.ubatch} \
            --flash-attn -ngl ${toString LLAMA_FLAGS.ngl} -t ${toString LLAMA_FLAGS.threads} \
            --no-mmap --mlock --embeddings --pooling cls \
            --cache-type-k ${LLAMA_FLAGS.cache-type-k} --cache-type-v ${LLAMA_FLAGS.cache-type-v} \
            --draft "${"$"}{DRAFT_MODEL_PATH}" \
            --draft-n-ctx ${toString LLAMA_FLAGS.draft-n-ctx} \
            --draft-n-predict ${toString LLAMA_FLAGS.draft-n-predict} \
            --draft-n-gpu-layers ${toString LLAMA_FLAGS.draft-ngl} \
            --metrics --log-format json
    '';
  };
}
