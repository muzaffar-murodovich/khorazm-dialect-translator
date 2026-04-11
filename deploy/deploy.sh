#!/bin/bash
# ============================================================
# Khorezm Dialect Translator — Deployment Script
# Hetzner server (Ubuntu 24.04) — deploy user orqali
# Mavjud ochiqkurs loyihasi bilan birga ishlaydi
# ============================================================
# Ishlatish:
#   1. Loyiha fayllarini serverga koʻchiring (pastda koʻrsatilgan)
#   2. SSH orqali serverga kiring: ssh deploy@46.62.145.27
#   3. chmod +x ~/translator/deploy.sh && ~/translator/deploy.sh
# ============================================================

set -euo pipefail

# ======================== SOZLAMALAR ========================
DOMAIN="xorazmcha.muzaffar.zip"
PROJECT_DIR="/home/deploy/translator"
SERVICE_NAME="gunicorn-translator"
# ============================================================

echo "=== 1. Tizim paketlarini yangilash ==="
sudo apt update
sudo apt install -y python3 python3-venv

echo "=== 2. Virtual environment yaratish ==="
cd "$PROJECT_DIR"
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate

echo "=== 3. Gunicorn systemd service yaratish ==="
sudo tee /etc/systemd/system/${SERVICE_NAME}.service > /dev/null << EOF
[Unit]
Description=Khorezm Dialect Translator (Gunicorn)
After=network.target

[Service]
User=deploy
Group=deploy
WorkingDirectory=$PROJECT_DIR
ExecStart=$PROJECT_DIR/venv/bin/gunicorn --workers 2 --bind unix:$PROJECT_DIR/gunicorn.sock wsgi:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable "$SERVICE_NAME"
sudo systemctl start "$SERVICE_NAME"

echo "=== 4. Nginx konfiguratsiya ==="
sudo tee /etc/nginx/sites-available/translator > /dev/null << 'NGINX'
server {
    listen 80;
    server_name xorazmcha.muzaffar.zip;

    location / {
        proxy_pass http://unix:/home/deploy/translator/gunicorn.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /home/deploy/translator/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
NGINX

sudo ln -sf /etc/nginx/sites-available/translator /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

echo "=== 5. Sudo huquqini sozlash (restart uchun) ==="
echo "deploy ALL=(ALL) NOPASSWD: /usr/bin/systemctl restart ${SERVICE_NAME}" \
    | sudo tee /etc/sudoers.d/translator > /dev/null

echo ""
echo "============================================"
echo "  DEPLOY MUVAFFAQIYATLI YAKUNLANDI!"
echo "  Sayt: https://$DOMAIN"
echo "============================================"
echo ""
echo "Foydali buyruqlar:"
echo "  sudo systemctl status $SERVICE_NAME     — ilova holati"
echo "  sudo systemctl restart $SERVICE_NAME    — qayta ishga tushirish"
echo "  sudo journalctl -u $SERVICE_NAME -f     — loglarni kuzatish"
echo ""
