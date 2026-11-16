#!/usr/bin/env bash
# Deja el puerto 22 del Security Group abierto SOLO a la IP pública actual del autor.
# Ejecutar cada vez que cambie la IP (otra red, otro día).
set -euo pipefail
source "$(dirname "$0")/_comun.sh"

MI_IP="$(curl -s https://checkip.amazonaws.com | tr -d '[:space:]')"
VPC_ID="$(aws ec2 describe-vpcs --filters Name=isDefault,Values=true --query 'Vpcs[0].VpcId' --output text)"
SG_ID="$(aws ec2 describe-security-groups --filters "Name=group-name,Values=${NOMBRE_SG}" "Name=vpc-id,Values=${VPC_ID}" --query 'SecurityGroups[0].GroupId' --output text)"
[ "$SG_ID" != "None" ] || { echo "No existe el SG ${NOMBRE_SG}; ejecuta infra/crear.sh"; exit 1; }

ACTUAL="$(aws ec2 describe-security-groups --group-ids "$SG_ID" --query 'SecurityGroups[0].IpPermissions[?FromPort==`22`].IpRanges[].CidrIp' --output text)"
if [ "$ACTUAL" = "${MI_IP}/32" ]; then
  echo "SG ya permite SSH solo desde ${MI_IP}/32"
  exit 0
fi

# Quita reglas viejas del puerto 22 y agrega la IP actual
for CIDR in $ACTUAL; do
  aws ec2 revoke-security-group-ingress --group-id "$SG_ID" --protocol tcp --port 22 --cidr "$CIDR" >/dev/null
done
aws ec2 authorize-security-group-ingress --group-id "$SG_ID" --protocol tcp --port 22 --cidr "${MI_IP}/32" >/dev/null
echo "SG ${SG_ID}: puerto 22 abierto solo a ${MI_IP}/32"
