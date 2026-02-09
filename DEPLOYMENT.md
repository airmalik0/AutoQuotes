# Production Deployment Guide – AutoQuotes

Инструкция по развёртыванию проекта на сервер.

---

## Quick Access (Production)

```bash
# SSH подключение
ssh root@178.128.244.116

# Директория проекта
cd /opt/autoquotes

# Проверка состояния
systemctl status autoquotes          # Статус сервиса
journalctl -u autoquotes -f          # Логи бота + API
docker compose ps                    # Статус PostgreSQL

# Git статус
git status
git log --oneline -5

# Health check
curl -s https://sup.solutions/api/cars | head -c 100

# Быстрое обновление
git pull origin main && cd webapp && npm run build && cd .. && systemctl restart autoquotes
```

**URLs:**
- https://sup.solutions/static/ — Mini App
- https://sup.solutions/api/cars — API (проверка)

---

## 1. Предварительные требования

### DNS записи
Настройте A-запись на IP сервера:
```
sup.solutions → 178.128.244.116
```

### Требования к серверу
- Ubuntu 24.04
- Минимум 1GB RAM
- SSH доступ под `root`

---

## 2. Подготовка сервера

```bash
ssh root@178.128.244.116

# Обновления и базовые пакеты
apt-get update
apt-get install -y docker.io docker-compose-v2 nodejs npm nginx certbot python3-certbot-nginx python3-venv python3-pip

# Включить Docker
systemctl enable --now docker
```

---

## 3. Deploy Key для GitHub

```bash
# Генерация ключа
ssh-keygen -t ed25519 -C "autoquotes-deploy" -f /root/.ssh/autoquotes_deploy -N ""

# Показать публичный ключ
cat /root/.ssh/autoquotes_deploy.pub
```

Добавьте ключ в GitHub:
- Repository → Settings → Deploy keys → Add deploy key
- Title: `Production Server`
- Key: вставьте содержимое `autoquotes_deploy.pub`

Настройте SSH:
```bash
cat >> /root/.ssh/config << 'EOF'
Host github.com
    HostName github.com
    User git
    IdentityFile /root/.ssh/autoquotes_deploy
    IdentitiesOnly yes
EOF
chmod 600 /root/.ssh/config
ssh-keyscan github.com >> /root/.ssh/known_hosts

# Проверка
ssh -T git@github.com
```

---

## 4. Клонирование репозитория

```bash
git clone git@github.com:airmalik0/AutoQuotes.git /opt/autoquotes
cd /opt/autoquotes
```

---

## 5. Настройка окружения

```bash
cat > /opt/autoquotes/.env << 'EOF'
BOT_TOKEN=ваш_токен_от_BotFather
DATABASE_URL=postgresql+asyncpg://autoquotes:autoquotes@localhost:5432/autoquotes
WEBAPP_URL=https://sup.solutions/static/
EOF
```

---

## 6. PostgreSQL

```bash
cd /opt/autoquotes
docker compose up -d

# Проверка
docker compose ps
docker compose logs postgres
```

---

## 7. Python окружение

```bash
cd /opt/autoquotes
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## 8. Миграции БД

```bash
cd /opt/autoquotes
source venv/bin/activate
PYTHONPATH=/opt/autoquotes alembic revision --autogenerate -m "initial"
PYTHONPATH=/opt/autoquotes alembic upgrade head
```

---

## 9. Сборка Mini App

```bash
cd /opt/autoquotes/webapp
npm install
npm run build
# Результат: ../api/static/
```

---

## 10. Nginx + SSL

```bash
# Конфигурация Nginx
cat > /etc/nginx/sites-available/autoquotes << 'NGINXEOF'
server {
    listen 80;
    server_name sup.solutions;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        client_max_body_size 10M;
    }
}
NGINXEOF

ln -sf /etc/nginx/sites-available/autoquotes /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx

# Открыть порты
ufw allow 22
ufw allow 80
ufw allow 443
ufw enable

# SSL сертификат
certbot --nginx -d sup.solutions --non-interactive --agree-tos --register-unsafely-without-email --redirect
```

---

## 11. Systemd сервис

```bash
cat > /etc/systemd/system/autoquotes.service << 'EOF'
[Unit]
Description=AutoQuotes Telegram Bot + API
After=network.target docker.service
Requires=docker.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/autoquotes
Environment=PYTHONPATH=/opt/autoquotes
ExecStart=/opt/autoquotes/venv/bin/python -m bot.main
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable autoquotes
systemctl start autoquotes
```

---

## 12. Полезные команды

```bash
# Логи
journalctl -u autoquotes -f              # Логи бота в реальном времени
journalctl -u autoquotes --since "1h ago" # За последний час

# Управление сервисом
systemctl status autoquotes
systemctl restart autoquotes
systemctl stop autoquotes

# PostgreSQL
docker compose ps
docker compose logs postgres
docker compose exec postgres psql -U autoquotes -d autoquotes

# Резервное копирование БД
docker compose exec postgres pg_dump -U autoquotes autoquotes > backup_$(date +%Y%m%d).sql

# Nginx
nginx -t
systemctl reload nginx
cat /etc/nginx/sites-available/autoquotes
```

---

## 13. Обновление кода

```bash
cd /opt/autoquotes
git pull origin main
cd webapp && npm run build && cd ..
systemctl restart autoquotes
```

---

## 14. Чек-лист деплоя

- [ ] DNS запись `sup.solutions → 178.128.244.116`
- [ ] Docker установлен и запущен
- [ ] Deploy key добавлен в GitHub
- [ ] Репозиторий склонирован (`/opt/autoquotes`)
- [ ] `.env` заполнен (BOT_TOKEN, DATABASE_URL, WEBAPP_URL)
- [ ] PostgreSQL запущен (`docker compose ps`)
- [ ] Python venv создан, зависимости установлены
- [ ] Миграции выполнены (`alembic upgrade head`)
- [ ] Mini App собрана (`npm run build`)
- [ ] Nginx настроен + SSL сертификат
- [ ] systemd сервис запущен (`systemctl status autoquotes`)
- [ ] `https://sup.solutions/api/cars` возвращает JSON
- [ ] `https://sup.solutions/static/` открывается
- [ ] Бот отвечает на `/start`

---

## 15. Troubleshooting

### Бот не стартует
```bash
journalctl -u autoquotes -n 50 --no-pager
# Проверить .env
cat /opt/autoquotes/.env
```

### PostgreSQL не доступен
```bash
docker compose ps
docker compose logs postgres
# Перезапуск
docker compose restart postgres
```

### SSL сертификат истёк
```bash
certbot renew
# Certbot автоматически обновляет сертификаты, но можно проверить:
certbot certificates
```

### Mini App не открывается
```bash
# Проверить что static собран
ls /opt/autoquotes/api/static/
# Пересобрать
cd /opt/autoquotes/webapp && npm run build
```
