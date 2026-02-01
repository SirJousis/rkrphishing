# Guía de Despliegue - Servidor Casero con Port Forwarding

## 📋 Tabla de Contenidos
1. [Requisitos Previos](#requisitos-previos)
2. [Preparación del Servidor](#preparación-del-servidor)
3. [Instalación de la Aplicación](#instalación-de-la-aplicación)
4. [Configuración de Nginx](#configuración-de-nginx)
5. [Configuración de Gunicorn](#configuración-de-gunicorn)
6. [Configuración del Router (Port Forwarding)](#configuración-del-router-port-forwarding)
7. [DNS Dinámico](#dns-dinámico)
8. [SSL/TLS con Let's Encrypt](#ssltls-con-lets-encrypt)
9. [Seguridad](#seguridad)
10. [Monitoreo y Mantenimiento](#monitoreo-y-mantenimiento)

---

## Requisitos Previos

### Hardware Mínimo
- **CPU:** 2 cores
- **RAM:** 2 GB
- **Disco:** 20 GB SSD
- **Red:** Conexión estable con IP pública

### Software
- **OS:** Ubuntu Server 22.04 LTS (recomendado)
- **Acceso:** SSH habilitado
- **Permisos:** Usuario con sudo

### Networking
- Router con acceso administrativo
- IP pública (verificar con `curl ifconfig.me`)
- Puerto 80 y 443 disponibles

---

## Preparación del Servidor

### 1. Actualizar el Sistema

```bash
sudo apt update && sudo apt upgrade -y
```

### 2. Instalar Dependencias del Sistema

```bash
# Python y herramientas
sudo apt install -y python3 python3-pip python3-venv python3-dev

# MySQL/MariaDB
sudo apt install -y mariadb-server mariadb-client

# Nginx
sudo apt install -y nginx

# Herramientas de compilación (para mysqlclient)
sudo apt install -y build-essential libssl-dev libffi-dev
sudo apt install -y default-libmysqlclient-dev pkg-config

# Certbot para SSL
sudo apt install -y certbot python3-certbot-nginx

# Utilidades
sudo apt install -y git curl ufw
```

### 3. Configurar MySQL

```bash
# Asegurar instalación
sudo mysql_secure_installation
```

**Respuestas recomendadas:**
- Set root password: **YES** (elige una contraseña fuerte)
- Remove anonymous users: **YES**
- Disallow root login remotely: **YES**
- Remove test database: **YES**
- Reload privilege tables: **YES**

**Crear base de datos:**

```bash
sudo mysql -u root -p
```

```sql
CREATE DATABASE phishing_platform CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'phishing_user'@'localhost' IDENTIFIED BY 'TU_CONTRASEÑA_SEGURA';
GRANT ALL PRIVILEGES ON phishing_platform.* TO 'phishing_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### 4. Configurar Firewall

```bash
# Permitir SSH
sudo ufw allow 22/tcp

# Permitir HTTP y HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Habilitar firewall
sudo ufw enable

# Verificar estado
sudo ufw status
```

---

## Instalación de la Aplicación

### 1. Crear Usuario de Sistema

```bash
sudo useradd -m -s /bin/bash phishing
sudo usermod -aG www-data phishing
```

### 2. Clonar/Subir el Proyecto

**Opción A: Desde Git**
```bash
sudo -u phishing git clone https://github.com/SirJousis/rkrphishing.git /home/phishing/app
```

**Opción B: Subir manualmente**
```bash
# Desde tu máquina local
scp -r /ruta/local/phishing-platform usuario@TU_IP_PUBLICA:/tmp/

# En el servidor
sudo mv /tmp/phishing-platform /home/phishing/app
sudo chown -R phishing:phishing /home/phishing/app
```

### 3. Configurar Entorno Virtual

```bash
cd /home/phishing/app
sudo -u phishing python3 -m venv venv
sudo -u phishing venv/bin/pip install --upgrade pip
sudo -u phishing venv/bin/pip install -r requirements.txt
```

### 4. Configurar Variables de Entorno

```bash
sudo -u phishing nano /home/phishing/app/.env
```

**Contenido:**
```bash
SECRET_KEY=genera_una_clave_aleatoria_muy_larga_aqui
FLASK_ENV=production
SQLALCHEMY_DATABASE_URI=mysql://phishing_user:TU_CONTRASEÑA_SEGURA@localhost/phishing_platform
```

**Generar SECRET_KEY:**
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### 5. Crear Configuración de Instancia

```bash
sudo -u phishing mkdir -p /home/phishing/app/instance
sudo -u phishing nano /home/phishing/app/instance/config.py
```

**Contenido:**
```python
import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv('SECRET_KEY')
SQLALCHEMY_DATABASE_URI = os.getenv('SQLALCHEMY_DATABASE_URI')
SQLALCHEMY_TRACK_MODIFICATIONS = False
```

### 6. Inicializar Base de Datos

```bash
cd /home/phishing/app
sudo -u phishing venv/bin/python scripts/reset_db.py
sudo -u phishing venv/bin/python scripts/create_admin.py
```

---

## Configuración de Nginx

### 1. Crear Configuración del Sitio

```bash
sudo nano /etc/nginx/sites-available/phishing-platform
```

**Contenido:**
```nginx
server {
    listen 80;
    server_name tu-dominio.duckdns.org;  # Cambiar por tu dominio

    # Logs
    access_log /var/log/nginx/phishing_access.log;
    error_log /var/log/nginx/phishing_error.log;

    # Límite de tamaño de request
    client_max_body_size 10M;

    # Proxy a Gunicorn
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Archivos estáticos
    location /static {
        alias /home/phishing/app/app/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
}
```

### 2. Habilitar el Sitio

```bash
# Crear enlace simbólico
sudo ln -s /etc/nginx/sites-available/phishing-platform /etc/nginx/sites-enabled/

# Eliminar sitio por defecto
sudo rm /etc/nginx/sites-enabled/default

# Verificar configuración
sudo nginx -t

# Reiniciar Nginx
sudo systemctl restart nginx
```

---

## Configuración de Gunicorn

### 1. Crear Archivo de Servicio Systemd

```bash
sudo nano /etc/systemd/system/phishing-platform.service
```

**Contenido:**
```ini
[Unit]
Description=RKR Phishing Platform
After=network.target mysql.service
Requires=mysql.service

[Service]
Type=notify
User=phishing
Group=www-data
WorkingDirectory=/home/phishing/app
Environment="PATH=/home/phishing/app/venv/bin"
ExecStart=/home/phishing/app/venv/bin/gunicorn \
    --workers 3 \
    --bind 127.0.0.1:8000 \
    --timeout 120 \
    --access-logfile /var/log/gunicorn/access.log \
    --error-logfile /var/log/gunicorn/error.log \
    --log-level info \
    wsgi:app

# Restart policy
Restart=always
RestartSec=10

# Security
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

### 2. Crear Directorio de Logs

```bash
sudo mkdir -p /var/log/gunicorn
sudo chown phishing:www-data /var/log/gunicorn
```

### 3. Habilitar y Arrancar el Servicio

```bash
# Recargar systemd
sudo systemctl daemon-reload

# Habilitar inicio automático
sudo systemctl enable phishing-platform

# Iniciar servicio
sudo systemctl start phishing-platform

# Verificar estado
sudo systemctl status phishing-platform

# Ver logs en tiempo real
sudo journalctl -u phishing-platform -f
```

---

## Configuración del Router (Port Forwarding)

### Pasos Generales

1. **Acceder al Router**
   - Abre un navegador
   - Dirígete a: `http://192.168.1.1` o `http://192.168.0.1`
   - Inicia sesión (usuario/contraseña del router)

2. **Localizar Port Forwarding**
   - Busca secciones como:
     - "Port Forwarding"
     - "Virtual Server"
     - "NAT"
     - "Aplicaciones y Juegos"

3. **Crear Reglas**

   **Regla 1: HTTP**
   - **Nombre:** Phishing-HTTP
   - **Puerto Externo:** 80
   - **Puerto Interno:** 80
   - **IP Interna:** 192.168.X.X (IP de tu servidor)
   - **Protocolo:** TCP

   **Regla 2: HTTPS**
   - **Nombre:** Phishing-HTTPS
   - **Puerto Externo:** 443
   - **Puerto Interno:** 443
   - **IP Interna:** 192.168.X.X
   - **Protocolo:** TCP

4. **Guardar y Aplicar**

### Obtener IP Interna del Servidor

```bash
ip addr show | grep "inet " | grep -v 127.0.0.1
```

### Verificar IP Pública

```bash
curl ifconfig.me
```

### Configurar IP Estática Local

**Opción A: Reserva DHCP en el Router**
- Asocia la MAC del servidor con una IP fija

**Opción B: IP Estática en el Servidor**

```bash
sudo nano /etc/netplan/00-installer-config.yaml
```

```yaml
network:
  version: 2
  ethernets:
    eth0:  # Cambiar por tu interfaz (usa 'ip a' para ver)
      dhcp4: no
      addresses:
        - 192.168.1.100/24  # Tu IP estática
      gateway4: 192.168.1.1  # IP del router
      nameservers:
        addresses:
          - 8.8.8.8
          - 8.8.4.4
```

```bash
sudo netplan apply
```

---

## DNS Dinámico

Si tu ISP cambia tu IP pública frecuentemente, usa un servicio de DNS dinámico.

### Opción 1: DuckDNS (Gratis)

1. **Registrarse**
   - Ve a: https://www.duckdns.org
   - Inicia sesión con Google/GitHub
   - Crea un subdominio: `tu-nombre.duckdns.org`

2. **Instalar Cliente**

```bash
# Crear directorio
mkdir -p /home/phishing/duckdns
cd /home/phishing/duckdns

# Crear script
nano duck.sh
```

**Contenido de duck.sh:**
```bash
#!/bin/bash
echo url="https://www.duckdns.org/update?domains=TU_SUBDOMINIO&token=TU_TOKEN&ip=" | curl -k -o /home/phishing/duckdns/duck.log -K -
```

```bash
# Dar permisos
chmod 700 duck.sh

# Probar
./duck.sh
cat duck.log  # Debe mostrar "OK"
```

3. **Automatizar con Cron**

```bash
crontab -e
```

Añadir:
```bash
*/5 * * * * /home/phishing/duckdns/duck.sh >/dev/null 2>&1
```

### Opción 2: No-IP (Gratis con limitaciones)

Similar a DuckDNS, visita: https://www.noip.com

---

## SSL/TLS con Let's Encrypt

### 1. Obtener Certificado

```bash
sudo certbot --nginx -d tu-dominio.duckdns.org
```

**Respuestas:**
- Email: tu-email@example.com
- Términos: **A** (Agree)
- Compartir email: **N** (No)
- Redirect HTTP to HTTPS: **2** (Redirect)

### 2. Verificar Configuración

```bash
sudo nginx -t
sudo systemctl reload nginx
```

### 3. Renovación Automática

Certbot instala un cron automáticamente. Verificar:

```bash
sudo systemctl status certbot.timer
```

**Probar renovación:**
```bash
sudo certbot renew --dry-run
```

### 4. Configuración Final de Nginx (con SSL)

Certbot modifica automáticamente el archivo, pero verifica:

```bash
sudo nano /etc/nginx/sites-available/phishing-platform
```

Debe incluir:
```nginx
server {
    listen 443 ssl http2;
    server_name tu-dominio.duckdns.org;

    ssl_certificate /etc/letsencrypt/live/tu-dominio.duckdns.org/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/tu-dominio.duckdns.org/privkey.pem;
    
    # SSL optimizations
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    
    # ... resto de la configuración
}

server {
    listen 80;
    server_name tu-dominio.duckdns.org;
    return 301 https://$server_name$request_uri;
}
```

---

## Seguridad

### 1. Fail2Ban (Protección contra Fuerza Bruta)

```bash
sudo apt install -y fail2ban
```

**Configurar:**
```bash
sudo nano /etc/fail2ban/jail.local
```

```ini
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5

[nginx-http-auth]
enabled = true

[nginx-noscript]
enabled = true

[nginx-badbots]
enabled = true
```

```bash
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

### 2. Limitar Acceso SSH

```bash
sudo nano /etc/ssh/sshd_config
```

Cambiar:
```bash
PermitRootLogin no
PasswordAuthentication no  # Solo si usas claves SSH
Port 2222  # Cambiar puerto por defecto (opcional)
```

```bash
sudo systemctl restart sshd
```

### 3. Actualizaciones Automáticas

```bash
sudo apt install -y unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

### 4. Monitoreo de Logs

```bash
# Ver intentos de login fallidos
sudo grep "Failed password" /var/log/auth.log

# Ver accesos a la aplicación
sudo tail -f /var/log/nginx/phishing_access.log

# Ver errores de la aplicación
sudo journalctl -u phishing-platform -f
```

---

## Monitoreo y Mantenimiento

### Comandos Útiles

```bash
# Estado del servicio
sudo systemctl status phishing-platform

# Reiniciar aplicación
sudo systemctl restart phishing-platform

# Ver logs en tiempo real
sudo journalctl -u phishing-platform -f

# Ver uso de recursos
htop

# Espacio en disco
df -h

# Backup de base de datos
mysqldump -u phishing_user -p phishing_platform > backup_$(date +%Y%m%d).sql
```

### Script de Backup Automático

```bash
sudo nano /home/phishing/backup.sh
```

```bash
#!/bin/bash
BACKUP_DIR="/home/phishing/backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup BD
mysqldump -u phishing_user -pTU_CONTRASEÑA phishing_platform > $BACKUP_DIR/db_$DATE.sql

# Backup archivos
tar -czf $BACKUP_DIR/app_$DATE.tar.gz /home/phishing/app

# Eliminar backups antiguos (más de 7 días)
find $BACKUP_DIR -type f -mtime +7 -delete

echo "Backup completado: $DATE"
```

```bash
chmod +x /home/phishing/backup.sh

# Programar backup diario a las 3 AM
sudo crontab -e
```

Añadir:
```bash
0 3 * * * /home/phishing/backup.sh >> /var/log/backup.log 2>&1
```

---

## Verificación Final

### Checklist de Despliegue

- [ ] MySQL configurado y base de datos creada
- [ ] Aplicación instalada en `/home/phishing/app`
- [ ] Entorno virtual creado y dependencias instaladas
- [ ] Variables de entorno configuradas (`.env`)
- [ ] Base de datos inicializada
- [ ] Usuario admin creado
- [ ] Gunicorn configurado como servicio systemd
- [ ] Nginx configurado y funcionando
- [ ] Port forwarding configurado en el router
- [ ] DNS dinámico configurado (DuckDNS/No-IP)
- [ ] SSL/TLS configurado con Let's Encrypt
- [ ] Firewall (UFW) habilitado
- [ ] Fail2Ban instalado y configurado
- [ ] Backups automáticos programados

### Pruebas

1. **Acceso Local**
   ```bash
   curl http://localhost
   ```

2. **Acceso desde Internet**
   - Abre un navegador en tu móvil (usando datos, no WiFi)
   - Visita: `https://tu-dominio.duckdns.org`

3. **Verificar SSL**
   - Debe mostrar el candado verde
   - Certificado válido de Let's Encrypt

4. **Probar Login**
   - Usuario: `admin`
   - Contraseña: la configurada

---

## Solución de Problemas

### La aplicación no arranca

```bash
# Ver logs detallados
sudo journalctl -u phishing-platform -n 50

# Verificar que Gunicorn puede ejecutarse manualmente
cd /home/phishing/app
sudo -u phishing venv/bin/gunicorn wsgi:app
```

### No puedo acceder desde Internet

```bash
# Verificar que Nginx está escuchando
sudo netstat -tlnp | grep nginx

# Verificar port forwarding
# Desde fuera de tu red, usa: https://www.yougetsignal.com/tools/open-ports/

# Verificar IP pública
curl ifconfig.me
```

### Error 502 Bad Gateway

```bash
# Verificar que Gunicorn está corriendo
sudo systemctl status phishing-platform

# Verificar que Nginx puede conectar a Gunicorn
curl http://127.0.0.1:8000
```

### SSL no funciona

```bash
# Verificar certificados
sudo certbot certificates

# Renovar manualmente
sudo certbot renew --force-renewal

# Verificar configuración de Nginx
sudo nginx -t
```

---

## Costos Estimados

| Concepto | Costo |
|----------|-------|
| Hardware (servidor usado) | €100-300 (una vez) |
| Electricidad (~10W 24/7) | ~€2/mes |
| Internet (ya tienes) | €0 |
| DuckDNS | **GRATIS** |
| Let's Encrypt SSL | **GRATIS** |
| **TOTAL MENSUAL** | **~€2** |

---

## Ventajas y Desventajas

### ✅ Ventajas
- Control total del hardware
- Sin costos mensuales de hosting
- Privacidad de datos
- Aprendizaje técnico

### ❌ Desventajas
- Dependencia de tu conexión a internet
- IP pública puede cambiar
- Responsable de mantenimiento y seguridad
- Consumo eléctrico continuo
- Riesgo si se cae la luz

---

**Versión:** 1.0  
**Última actualización:** Febrero 2026  
**Soporte:** RKR Security Team
