# 🛡️ Chat Room — Admin Panel

A lightweight web-based administration panel for the **[Chat Room](https://github.com/44114/room)** real-time messaging server. Built with **Python Flask** and **MySQL**, sharing the same database as the main chat server. **This project depends on the main Chat Room server — it cannot operate without it.**

> 🤖 **Developed with assistance from [Claude Code](https://claude.ai/code) (Anthropic)**

---

## ⚠️ Critical Security Notice

**The admin panel has unrestricted access to all user data and chat records. Follow these steps IN ORDER before exposing it to any network:**

### 1. Set the admin password FIRST

On first run, visit `http://127.0.0.1:9889/auth/setup` from the server itself (localhost only). Create a **strong** admin password (minimum 8 characters, mix of uppercase, lowercase, digits, and special characters). The admin panel is completely unprotected until this step is completed.

### 2. NEVER expose the admin panel directly to the internet

The panel listens on `127.0.0.1:9889` by default. **Do not change this to `0.0.0.0`** without first configuring a reverse proxy with TLS encryption and IP whitelisting.

### 3. Always use a reverse proxy with HTTPS (TLS 1.2+)

If remote access is needed, place Nginx in front with:
- **TLS 1.2 or higher** (TLS 1.3 recommended)
- **Let's Encrypt** for free automated certificates
- **IP whitelisting** to restrict access to trusted networks
- **HTTP Basic Auth** as an additional layer

### 4. Use a strong admin password

- Minimum 12 characters recommended for production
- Use a password manager to generate and store it
- Never reuse the admin password elsewhere
- The password is stored as Argon2id hash — it cannot be recovered if lost

---

## Features

- **First-Run Setup** — Automatically detects empty database and prompts admin account creation
- **Dashboard** — Overview of active users, messages, and uploaded files
- **User Management** — View, disable, reactivate users; reset passwords
- **Message Management** — View, delete individual messages; clear all chat history
- **File Overview** — List all uploaded files with metadata

---

## Installation

Two methods are available.

### Method 1: Via Main Project's One-Click Script (Recommended)

The [main Chat Room setup script](https://github.com/44114/room/blob/main/setup.sh) can install the admin panel alongside the chat server automatically:

```bash
curl -fsSL https://raw.githubusercontent.com/44114/room/main/setup.sh -o setup.sh
sudo bash setup.sh
```

When prompted *"Also install the Admin Panel (room-admin)?"*, answer **Y**. The script handles everything: system dependencies, MySQL, venv, `.env` generation, and systemd service.

---

### Method 2: Manual Installation

#### Prerequisites

Same as the [main Chat Room server](https://github.com/44114/room): Python 3.10+, MySQL 8.0+/MariaDB 10.11+.

#### Steps

```bash
git clone https://github.com/44114/room-admin.git
cd room-admin
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### Configuration

```bash
cp .env.example .env
```

Edit `.env` with your MySQL credentials. **Use the same database** as the main Chat Room server.

Required environment variables:

| Variable | Description |
|----------|-------------|
| `MYSQL_HOST` | MySQL host (default: `127.0.0.1`) |
| `MYSQL_PORT` | MySQL port (default: `3306`) |
| `MYSQL_DB` | Database name (default: `chatroom`) |
| `MYSQL_USER` | MySQL username |
| `MYSQL_PASSWORD` | MySQL password |
| `SECRET_KEY` | Flask session signing key (run `python3 -c "import secrets; print(secrets.token_hex(64))"`) |

#### Run (local only)

```bash
python app.py
# Starts on http://127.0.0.1:9889
```

On first run, visit `http://127.0.0.1:9889/auth/setup` and create your admin account.

### Production (Nginx reverse proxy + HTTPS)

> **Do this BEFORE changing the admin panel's bind address from 127.0.0.1.**

```bash
sudo apt install -y nginx certbot python3-certbot-nginx
```

Create `/etc/nginx/sites-available/room-admin`:

```nginx
server {
    listen 443 ssl http2;
    server_name admin.example.com;

    # TLS 1.2+ (mandatory)
    ssl_certificate     /etc/letsencrypt/live/admin.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/admin.example.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;

    # IP whitelist — restrict to trusted networks only
    allow 192.168.1.0/24;
    allow 10.0.0.0/8;
    deny all;

    # Optional: HTTP Basic Auth as extra layer
    auth_basic "Admin Panel";
    auth_basic_user_file /etc/nginx/.htpasswd;

    location / {
        proxy_pass http://127.0.0.1:9889;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/room-admin /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
sudo certbot --nginx -d admin.example.com
sudo systemctl enable certbot.timer

# Create HTTP Basic Auth credentials (extra security)
sudo apt install -y apache2-utils
sudo htpasswd -c /etc/nginx/.htpasswd admin
```

---

## Default Port

`9889` — different from the main chat server (`9888`). Override with `ADMIN_PORT` in `.env`.

---

## License

This project is licensed under the [MIT License](LICENSE).
