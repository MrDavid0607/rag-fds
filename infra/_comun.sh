#!/usr/bin/env bash
# Variables y funciones comunes de los scripts de infra/.
# Se usa con:  source "$(dirname "$0")/_comun.sh"
# Requiere AWS CLI v2 y el perfil [academy] (credenciales temporales del Learner Lab).

export AWS_PROFILE="${AWS_PROFILE:-academy}"
export AWS_DEFAULT_REGION="us-east-1"
export MSYS_NO_PATHCONV=1   # evita que Git Bash reescriba rutas tipo /aws/service/... al llamar aws.exe

NOMBRE_PROYECTO="rag-fds"
NOMBRE_SG="rag-fds-sg"
NOMBRE_LLAVE="rag-fds"
LLAVE="$HOME/.ssh/rag-fds.pem"      # fuera del repositorio, nunca se sube
USUARIO_EC2="ubuntu"
RAIZ_REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIR_REMOTO="rag-fds"                # relativo a /home/ubuntu

# La IP pública cambia en cada arranque: siempre se consulta por tag, nunca se escribe fija.
id_instancia() {
  aws ec2 describe-instances \
    --filters "Name=tag:Project,Values=${NOMBRE_PROYECTO}" "Name=instance-state-name,Values=pending,running,stopping,stopped" \
    --query "Reservations[].Instances[].InstanceId | [0]" --output text
}

estado_instancia() {
  aws ec2 describe-instances --instance-ids "$1" --query "Reservations[0].Instances[0].State.Name" --output text
}

ip_publica() {
  aws ec2 describe-instances --instance-ids "$1" --query "Reservations[0].Instances[0].PublicIpAddress" --output text
}

exigir_instancia() {
  ID="$(id_instancia)"
  if [ -z "$ID" ] || [ "$ID" = "None" ]; then
    echo "No hay instancia con tag Project=${NOMBRE_PROYECTO}. Ejecuta infra/crear.sh" >&2
    exit 1
  fi
}

OPCIONES_SSH=(-i "$LLAVE" -o StrictHostKeyChecking=accept-new -o ServerAliveInterval=30 -o ServerAliveCountMax=10)
