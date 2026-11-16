#!/usr/bin/env bash
# Copia el repo local (incluidos los PDFs de data/raw) a la EC2 con tar sobre SSH
# (en Windows no hay rsync). Excluye .git, entornos virtuales y cachés.
set -euo pipefail
source "$(dirname "$0")/_comun.sh"
exigir_instancia
IP="$(ip_publica "$ID")"
cd "$RAIZ_REPO"
tar --exclude=.git --exclude=.venv --exclude=venv --exclude=__pycache__ --exclude='*.pem' --exclude=.env \
    --exclude=infra/.tipo_instancia -czf - . \
  | ssh "${OPCIONES_SSH[@]}" "${USUARIO_EC2}@${IP}" "mkdir -p ~/${DIR_REMOTO} && tar -xzf - -C ~/${DIR_REMOTO}"
echo "Subido a ~/${DIR_REMOTO} en ${IP}"
