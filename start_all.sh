#!/bin/bash
cd "$(dirname "$0")"

if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

echo "Iniciando vLLM..."
nohup ./start_server.sh >> server.log 2>&1 &

echo "Esperando 10 segundos..."
sleep 10

echo "Iniciando Auth API..."
nohup .venv/bin/uvicorn auth.main:app --host 0.0.0.0 --port 9000 >> auth.log 2>&1 &

echo "Iniciando Nginx..."
sudo service nginx start 2>/dev/null || service nginx start

echo "✅ Todos los servicios iniciados"
echo "📊 Monitorea vLLM: tail -f server.log"
echo "🌐 URL: http://localhost"
