#!/usr/bin/env bash
# Se ejecuta DENTRO de la EC2 (Ubuntu 24.04), no en el PC:
#   infra/ssh.sh 'bash -s' < infra/setup_remoto.sh
# Instala utilidades, Python con venv y Ollama (solo en 127.0.0.1), y descarga los modelos.
set -euo pipefail

MODELOS_OLLAMA=(${MODELOS_OLLAMA:-bge-m3 qwen2.5:7b-instruct llama3.1:8b})

export DEBIAN_FRONTEND=noninteractive
sudo apt-get update -y
sudo apt-get install -y python3-venv python3-pip rsync curl zstd git build-essential poppler-utils

mkdir -p ~/rag-fds
python3 -m venv ~/rag-fds/.venv
~/rag-fds/.venv/bin/pip install --upgrade pip

if ! command -v ollama >/dev/null; then
  curl -fsSL https://ollama.com/install.sh | sh
fi

# Ollama escucha solo en loopback; se accede por túnel SSH. Una pasada por modelo a la vez.
sudo mkdir -p /etc/systemd/system/ollama.service.d
sudo tee /etc/systemd/system/ollama.service.d/rag-fds.conf >/dev/null <<'EOF'
[Service]
Environment="OLLAMA_HOST=127.0.0.1:11434"
Environment="OLLAMA_MAX_LOADED_MODELS=1"
Environment="OLLAMA_NUM_PARALLEL=1"
EOF
sudo systemctl daemon-reload
sudo systemctl enable --now ollama
sudo systemctl restart ollama
sleep 5

for M in "${MODELOS_OLLAMA[@]}"; do
  echo "== Descargando $M =="
  ollama pull "$M"
done

echo "== Resumen =="
python3 --version
ollama --version
ollama list
ss -ltnp 2>/dev/null | grep 11434 || true
