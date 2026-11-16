#!/usr/bin/env bash
# Detiene la EC2 para no gastar presupuesto del Learner Lab (el disco se conserva).
set -euo pipefail
source "$(dirname "$0")/_comun.sh"
exigir_instancia
aws ec2 stop-instances --instance-ids "$ID" >/dev/null
echo "Deteniendo $ID ..."
aws ec2 wait instance-stopped --instance-ids "$ID"
echo "Instancia detenida."
