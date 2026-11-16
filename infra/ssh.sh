#!/usr/bin/env bash
# Abre una sesión SSH en la EC2 (o ejecuta el comando que se pase como argumentos).
set -euo pipefail
source "$(dirname "$0")/_comun.sh"
exigir_instancia
IP="$(ip_publica "$ID")"
[ "$IP" != "None" ] || { echo "La instancia no tiene IP (¿está detenida? usa infra/iniciar.sh)"; exit 1; }
exec ssh "${OPCIONES_SSH[@]}" "${USUARIO_EC2}@${IP}" "$@"
