dnf update -y
dnf install -y docker
systemctl enable --now docker
ACCOUNT_ID=${account_id}
aws ecr get-login-password --region ${aws_region} | docker login --username AWS --password-stdin "$ACCOUNT_ID.dkr.ecr.${aws_region}.amazonaws.com"
docker pull "$ACCOUNT_ID.dkr.ecr.${aws_region}.amazonaws.com/${ecr_repo}:latest" || true
docker rm -f ${app_name} 2>/dev/null || true
docker system prune -af || true
docker run -d --name ${app_name} -p 80:8000 \
  "$ACCOUNT_ID.dkr.ecr.${aws_region}.amazonaws.com/${ecr_repo}:latest"
