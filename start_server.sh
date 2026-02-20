#!/bin/bash
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

MODEL_NAME=${MODEL_NAME:-"Qwen/Qwen2-VL-7B-Instruct"}
API_KEY=${API_KEY:-"token-llm-chat-secret-2025"}

echo "Iniciando vLLM con modelo: $MODEL_NAME"

.venv/bin/vllm serve "$MODEL_NAME" \
    --dtype auto \
    --api-key "$API_KEY" \
    --host 0.0.0.0 \
    --port 8000 \
    --gpu-memory-utilization 0.95 \
    --max-model-len 8192
