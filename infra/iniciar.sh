#!/usr/bin/env bash
# Arranca la EC2 (si está detenida) y muestra su IP pública actual.
set -euo pipefail
source "$(dirname "$0")/_comun.sh"
exigir_instancia
bash "$(dirname "$0")/actualizar_ip.sh"
ESTADO="$(estado_instancia "$ID")"
if [ "$ESTADO" = "stopped" ]; then
  aws ec2 start-instances --instance-ids "$ID" >/dev/null
fi
aws ec2 wait instance-running --instance-ids "$ID"
echo "Instancia $ID en ejecución. IP pública: $(ip_publica "$ID")"
