# Bootstrap only — app image is deployed by GitHub Actions via SSM (avoids race with user_data).
dnf update -y
dnf install -y docker
systemctl enable --now docker
