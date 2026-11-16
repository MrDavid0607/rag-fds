#!/usr/bin/env bash
# Muestra identidad AWS, estado de la instancia del proyecto y su IP.
set -uo pipefail
source "$(dirname "$0")/_comun.sh"
aws sts get-caller-identity --query Arn --output text || { echo "Credenciales vencidas: pide unas nuevas del Learner Lab."; exit 1; }
ID="$(id_instancia)"
if [ -z "$ID" ] || [ "$ID" = "None" ]; then echo "Sin instancia del proyecto."; exit 0; fi
aws ec2 describe-instances --instance-ids "$ID" \
  --query "Reservations[0].Instances[0].[InstanceId,InstanceType,State.Name,PublicIpAddress]" --output text
