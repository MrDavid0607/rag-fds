#!/usr/bin/env bash
# Crea (una sola vez) la llave SSH, el Security Group y la instancia EC2 del proyecto.
# Es idempotente: si algo ya existe, lo reutiliza.
set -euo pipefail
source "$(dirname "$0")/_comun.sh"

# Tipos a intentar en orden (el Learner Lab no siempre permite todos). No se prueban GPU.
# Probado el 2026-11-16: la política Pvoclabs2 del lab deniega m5.2xlarge, t3.2xlarge, m5.xlarge y,
# en general, todo tamaño mayor a "large". r5.large (2 vCPU, 16 GB) es el de más RAM permitido.
TIPOS=(${TIPOS_EC2:-m5.2xlarge t3.2xlarge m5.xlarge r5.large r6i.large t3.large})
DISCO_GB="${DISCO_GB:-80}"

echo "== Llave SSH =="
if aws ec2 describe-key-pairs --key-names "$NOMBRE_LLAVE" >/dev/null 2>&1; then
  echo "Key pair '$NOMBRE_LLAVE' ya existe en AWS."
  [ -f "$LLAVE" ] || { echo "ERROR: existe en AWS pero falta $LLAVE localmente."; exit 1; }
else
  mkdir -p "$HOME/.ssh"
  aws ec2 create-key-pair --key-name "$NOMBRE_LLAVE" --query KeyMaterial --output text > "$LLAVE"
  chmod 600 "$LLAVE"
  echo "Llave creada en $LLAVE"
fi

echo "== Security Group =="
VPC_ID="$(aws ec2 describe-vpcs --filters Name=isDefault,Values=true --query 'Vpcs[0].VpcId' --output text)"
SG_ID="$(aws ec2 describe-security-groups --filters "Name=group-name,Values=${NOMBRE_SG}" "Name=vpc-id,Values=${VPC_ID}" --query 'SecurityGroups[0].GroupId' --output text)"
if [ "$SG_ID" = "None" ]; then
  SG_ID="$(aws ec2 create-security-group --group-name "$NOMBRE_SG" --description "rag-fds: solo SSH desde la IP del autor" --vpc-id "$VPC_ID" --query GroupId --output text)"
  aws ec2 create-tags --resources "$SG_ID" --tags "Key=Project,Value=${NOMBRE_PROYECTO}"
  echo "SG creado: $SG_ID"
fi
bash "$(dirname "$0")/actualizar_ip.sh"

echo "== Instancia =="
EXISTENTE="$(id_instancia)"
if [ -n "$EXISTENTE" ] && [ "$EXISTENTE" != "None" ]; then
  echo "Ya existe la instancia $EXISTENTE (estado: $(estado_instancia "$EXISTENTE")). No se crea otra."
  exit 0
fi

AMI_ID="$(aws ssm get-parameter --name /aws/service/canonical/ubuntu/server/24.04/stable/current/amd64/hvm/ebs-gp3/ami-id --query Parameter.Value --output text 2>/dev/null || true)"
if [ -z "$AMI_ID" ]; then
  AMI_ID="$(aws ec2 describe-images --owners 099720109477 \
    --filters "Name=name,Values=ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*" "Name=state,Values=available" \
    --query 'sort_by(Images,&CreationDate)[-1].ImageId' --output text)"
fi
echo "AMI: $AMI_ID"

for TIPO in "${TIPOS[@]}"; do
  echo "Intentando $TIPO ..."
  if ID="$(aws ec2 run-instances \
      --image-id "$AMI_ID" --instance-type "$TIPO" --key-name "$NOMBRE_LLAVE" \
      --security-group-ids "$SG_ID" \
      --iam-instance-profile Name=LabInstanceProfile \
      --block-device-mappings "DeviceName=/dev/sda1,Ebs={VolumeSize=${DISCO_GB},VolumeType=gp3,DeleteOnTermination=true}" \
      --metadata-options "HttpTokens=required,HttpEndpoint=enabled" \
      --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=rag-fds},{Key=Project,Value=${NOMBRE_PROYECTO}}]" \
                           "ResourceType=volume,Tags=[{Key=Project,Value=${NOMBRE_PROYECTO}}]" \
      --query 'Instances[0].InstanceId' --output text 2>/tmp/err_run.txt)"; then
    echo "Instancia creada: $ID ($TIPO)"
    echo "$TIPO" > "$RAIZ_REPO/infra/.tipo_instancia"
    aws ec2 wait instance-running --instance-ids "$ID"
    echo "IP pública: $(ip_publica "$ID")"
    exit 0
  else
    echo "  No se pudo con $TIPO: $(tail -n 2 /tmp/err_run.txt | tr '\n' ' ')"
  fi
done
echo "ERROR: ningún tipo de instancia fue aceptado." >&2
exit 1
