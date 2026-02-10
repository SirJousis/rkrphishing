# Guía de Despliegue - Amazon Web Services (AWS)

## 📋 Tabla de Contenidos
1. [Arquitectura AWS](#arquitectura-aws)
2. [Requisitos Previos](#requisitos-previos)
3. [Configuración de EC2](#configuración-de-ec2)
4. [Configuración de RDS (MySQL)](#configuración-de-rds-mysql)
5. [Instalación de la Aplicación](#instalación-de-la-aplicación)
6. [Configuración de Nginx y Gunicorn](#configuración-de-nginx-y-gunicorn)
7. [Dominio y SSL](#dominio-y-ssl)
8. [Seguridad y Networking](#seguridad-y-networking)
9. [Monitoreo y Logs](#monitoreo-y-logs)
10. [Backup y Recuperación](#backup-y-recuperación)
11. [Optimización de Costos](#optimización-de-costos)
12. [CI/CD (Opcional)](#cicd-opcional)

---

## Arquitectura AWS

```
┌─────────────────────────────────────────────────────────┐
│                     Internet                            │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
         ┌───────────────────────┐
         │   Route 53 (DNS)      │
         │  phishing.example.com │
         └───────────┬───────────┘
                     │
                     ▼
         ┌───────────────────────┐
         │  CloudFront (CDN)     │ ◄── SSL Certificate (ACM)
         │  (Opcional)           │
         └───────────┬───────────┘
                     │
                     ▼
         ┌───────────────────────┐
         │  Application Load     │
         │  Balancer (ALB)       │
         └───────────┬───────────┘
                     │
         ┌───────────┴───────────┐
         │                       │
         ▼                       ▼
┌─────────────────┐     ┌─────────────────┐
│   EC2 Instance  │     │  EC2 Instance   │
│   (Primary)     │     │  (Standby)      │
│                 │     │  (Opcional)     │
│  - Nginx        │     │  - Nginx        │
│  - Gunicorn     │     │  - Gunicorn     │
│  - Flask App    │     │  - Flask App    │
└────────┬────────┘     └────────┬────────┘
         │                       │
         └───────────┬───────────┘
                     │
                     ▼
         ┌───────────────────────┐
         │   RDS MySQL           │
         │   (Multi-AZ)          │
         │                       │
         │  - Backups Auto       │
         │  - Encryption         │
         └───────────────────────┘
```

---

## Requisitos Previos

### Cuenta AWS
- Cuenta de AWS activa
- Tarjeta de crédito registrada
- Acceso a la consola de AWS

### Herramientas Locales
```bash
# AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Configurar credenciales
aws configure
```

**Datos necesarios:**
- AWS Access Key ID
- AWS Secret Access Key
- Default region: `eu-west-1` (Irlanda) o `us-east-1` (Virginia)
- Default output format: `json`

---

## Configuración de EC2

### 1. Crear Instancia EC2

**Acceder a EC2:**
1. Inicia sesión en AWS Console
2. Servicios → EC2 → Launch Instance

**Configuración:**

| Parámetro | Valor |
|-----------|-------|
| **Name** | phishing-platform-prod |
| **AMI** | Ubuntu Server 22.04 LTS |
| **Instance Type** | t3.small (2 vCPU, 2GB RAM) |
| **Key Pair** | Crear nueva: `phishing-key.pem` |
| **Network** | VPC por defecto |
| **Subnet** | Pública (auto-assign IP) |
| **Storage** | 20 GB gp3 SSD |

**Security Group (Firewall):**

Crear nuevo: `phishing-platform-sg`

| Type | Protocol | Port | Source | Description |
|------|----------|------|--------|-------------|
| SSH | TCP | 22 | Mi IP | Admin access |
| HTTP | TCP | 80 | 0.0.0.0/0 | Web traffic |
| HTTPS | TCP | 443 | 0.0.0.0/0 | Secure web |
| Custom TCP | TCP | 8000 | Security Group ID | Gunicorn (interno) |

**Lanzar instancia** → Esperar a que esté "Running"

### 2. Asignar IP Elástica

```bash
# Desde AWS Console
EC2 → Elastic IPs → Allocate Elastic IP address
→ Associate Elastic IP address → Seleccionar instancia
```

**O con AWS CLI:**
```bash
# Asignar IP elástica
aws ec2 allocate-address --domain vpc

# Asociar a instancia
aws ec2 associate-address \
  --instance-id i-1234567890abcdef0 \
  --allocation-id eipalloc-12345678
```

### 3. Conectar por SSH

```bash
# Dar permisos a la clave
chmod 400 phishing-key.pem

# Conectar
ssh -i phishing-key.pem ubuntu@TU_IP_ELASTICA
```

### 4. Configurar el Servidor

```bash
# Actualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar dependencias
sudo apt install -y python3 python3-pip python3-venv python3-dev \
  nginx build-essential libssl-dev libffi-dev \
  default-libmysqlclient-dev pkg-config git curl

# Instalar Certbot
sudo snap install --classic certbot
sudo ln -s /snap/bin/certbot /usr/bin/certbot
```

---

## Configuración de RDS (MySQL)

### 1. Crear Instancia RDS

**Acceder a RDS:**
AWS Console → RDS → Create database

**Configuración:**

| Parámetro | Valor |
|-----------|-------|
| **Engine** | MySQL 8.0 |
| **Template** | Free tier (o Production) |
| **DB Instance ID** | phishing-db |
| **Master username** | admin |
| **Master password** | [Contraseña fuerte] |
| **Instance class** | db.t3.micro (1 vCPU, 1GB) |
| **Storage** | 20 GB gp3 |
| **Auto scaling** | Enabled (max 100 GB) |
| **VPC** | Default VPC |
| **Public access** | No |
| **VPC Security Group** | Crear nuevo: `rds-sg` |
| **Initial database** | phishing_platform |
| **Backup retention** | 7 días |
| **Encryption** | Enabled |

**Security Group de RDS (`rds-sg`):**

| Type | Protocol | Port | Source | Description |
|------|----------|------|--------|-------------|
| MySQL/Aurora | TCP | 3306 | phishing-platform-sg | EC2 access |

### 2. Obtener Endpoint de RDS

```bash
# Desde AWS Console
RDS → Databases → phishing-db → Connectivity & security
→ Copiar "Endpoint"

# Ejemplo: phishing-db.c9akl1234567.eu-west-1.rds.amazonaws.com
```

### 3. Probar Conexión desde EC2

```bash
# Instalar cliente MySQL
sudo apt install -y mysql-client

# Conectar
mysql -h phishing-db.c9akl1234567.eu-west-1.rds.amazonaws.com \
  -u admin -p

# Crear base de datos (si no se creó automáticamente)
CREATE DATABASE phishing_platform CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
EXIT;
```

---

## Instalación de la Aplicación

### 1. Clonar Repositorio

```bash
cd /home/ubuntu
git clone https://github.com/SirJousis/rkrphishing.git app
cd app
```

**O subir con SCP:**
```bash
# Desde tu máquina local
scp -i phishing-key.pem -r /ruta/local/phishing-platform ubuntu@TU_IP:/home/ubuntu/app
```

### 2. Configurar Entorno Virtual

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Configurar Variables de Entorno

```bash
nano .env
```

**Contenido:**
```bash
SECRET_KEY=genera_una_clave_super_segura_aqui
FLASK_ENV=production
SQLALCHEMY_DATABASE_URI=mysql://admin:TU_PASSWORD@phishing-db.c9akl1234567.eu-west-1.rds.amazonaws.com/phishing_platform
```

**Generar SECRET_KEY:**
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### 4. Crear Configuración de Instancia

```bash
mkdir -p instance
nano instance/config.py
```

```python
import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv('SECRET_KEY')
SQLALCHEMY_DATABASE_URI = os.getenv('SQLALCHEMY_DATABASE_URI')
SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_pre_ping': True,
    'pool_recycle': 3600,
}
```

### 5. Inicializar Base de Datos

```bash
python scripts/reset_db.py
python scripts/create_admin.py
```

---

## Configuración de Nginx y Gunicorn

### 1. Configurar Gunicorn como Servicio

```bash
sudo nano /etc/systemd/system/phishing-platform.service
```

```ini
[Unit]
Description=RKR Phishing Platform
After=network.target

[Service]
Type=notify
User=ubuntu
Group=www-data
WorkingDirectory=/home/ubuntu/app
Environment="PATH=/home/ubuntu/app/venv/bin"
ExecStart=/home/ubuntu/app/venv/bin/gunicorn \
    --workers 3 \
    --bind 127.0.0.1:8000 \
    --timeout 120 \
    --access-logfile /var/log/gunicorn/access.log \
    --error-logfile /var/log/gunicorn/error.log \
    --log-level info \
    wsgi:app

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Crear directorio de logs
sudo mkdir -p /var/log/gunicorn
sudo chown ubuntu:www-data /var/log/gunicorn

# Habilitar y arrancar
sudo systemctl daemon-reload
sudo systemctl enable phishing-platform
sudo systemctl start phishing-platform
sudo systemctl status phishing-platform
```

### 2. Configurar Nginx

```bash
sudo nano /etc/nginx/sites-available/phishing-platform
```

```nginx
server {
    listen 80;
    server_name domain;  # Cambiar por tu dominio después

    access_log /var/log/nginx/phishing_access.log;
    error_log /var/log/nginx/phishing_error.log;

    client_max_body_size 10M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    location /static {
        alias /home/ubuntu/app/app/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
}
```

```bash
# Habilitar sitio
sudo ln -s /etc/nginx/sites-available/phishing-platform /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default

# Verificar y reiniciar
sudo nginx -t
sudo systemctl restart nginx
```

### 3. Verificar Funcionamiento

```bash
# Desde el servidor
curl http://localhost

# Desde tu navegador
http://TU_IP_ELASTICA
```

---

## Dominio y SSL

### Opción A: Route 53 + ACM (Recomendado)

#### 1. Registrar Dominio en Route 53

**AWS Console → Route 53 → Register domain**
- Buscar dominio disponible
- Completar información de registro
- Costo: ~$12/año (.com)

#### 2. Crear Hosted Zone

```bash
# Automático al registrar dominio
# O crear manualmente:
Route 53 → Hosted zones → Create hosted zone
```

#### 3. Crear Registro A

```bash
Route 53 → Hosted zones → tu-dominio.com → Create record

Name: phishing (o www)
Type: A
Value: TU_IP_ELASTICA
TTL: 300
```

#### 4. Solicitar Certificado SSL (ACM)

```bash
AWS Console → Certificate Manager → Request certificate

Domain name: phishing.tu-dominio.com
Validation: DNS validation
→ Create records in Route 53 (automático)
```

**Esperar validación** (~5-10 minutos)

#### 5. Configurar ALB (Application Load Balancer)

**Crear ALB:**
```bash
EC2 → Load Balancers → Create Load Balancer
→ Application Load Balancer

Name: phishing-alb
Scheme: Internet-facing
IP address type: IPv4
VPC: Default
Subnets: Seleccionar 2 zonas de disponibilidad
Security group: Crear nuevo (HTTP 80, HTTPS 443)
```

**Listeners:**
- HTTP:80 → Redirect to HTTPS
- HTTPS:443 → Forward to Target Group

**Target Group:**
```bash
Create target group
Target type: Instances
Name: phishing-targets
Protocol: HTTP
Port: 80
Health check path: /auth/login
→ Register targets: Seleccionar tu EC2
```

**Asociar Certificado SSL:**
```bash
Listeners → HTTPS:443 → Edit
→ Default SSL certificate: Seleccionar certificado ACM
```

#### 6. Actualizar Route 53

```bash
Route 53 → Hosted zones → tu-dominio.com
→ Editar registro A

Type: A - Alias
Alias target: ALB (phishing-alb)
```

### Opción B: Let's Encrypt (Gratis)

```bash
# Actualizar Nginx con tu dominio
sudo nano /etc/nginx/sites-available/phishing-platform
# Cambiar: server_name phishing.tu-dominio.com;

sudo nginx -t
sudo systemctl reload nginx

# Obtener certificado
sudo certbot --nginx -d phishing.tu-dominio.com

# Renovación automática (ya configurada)
sudo systemctl status certbot.timer
```

---

## Seguridad y Networking

### 1. Configurar Security Groups

**EC2 Security Group:**
```bash
# Restringir SSH solo a tu IP
aws ec2 authorize-security-group-ingress \
  --group-id sg-12345678 \
  --protocol tcp \
  --port 22 \
  --cidr TU_IP/32
```

### 2. IAM Roles (Opcional)

**Crear rol para EC2:**
```bash
IAM → Roles → Create role
→ AWS service → EC2
→ Permissions: CloudWatchAgentServerPolicy, AmazonSSMManagedInstanceCore
→ Name: EC2-Phishing-Role
```

**Asociar a instancia:**
```bash
EC2 → Instances → Actions → Security → Modify IAM role
→ Seleccionar EC2-Phishing-Role
```

### 3. Habilitar CloudWatch Logs

```bash
# Instalar agente
wget https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb
sudo dpkg -i amazon-cloudwatch-agent.deb

# Configurar
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-config-wizard
```

### 4. Configurar WAF (Opcional)

```bash
AWS Console → WAF & Shield → Create web ACL
→ Asociar a ALB
→ Añadir reglas:
  - Rate limiting (1000 req/5min)
  - SQL injection protection
  - XSS protection
```

---

## Monitoreo y Logs

### 1. CloudWatch Metrics

**Métricas automáticas:**
- CPU Utilization
- Network In/Out
- Disk Read/Write
- Status Checks

**Crear alarmas:**
```bash
CloudWatch → Alarms → Create alarm

Metric: EC2 → CPUUtilization
Threshold: > 80% for 5 minutes
Action: Send SNS notification
```

### 2. CloudWatch Logs

**Configurar logs de aplicación:**
```bash
sudo nano /opt/aws/amazon-cloudwatch-agent/etc/config.json
```

```json
{
  "logs": {
    "logs_collected": {
      "files": {
        "collect_list": [
          {
            "file_path": "/var/log/nginx/phishing_access.log",
            "log_group_name": "/aws/ec2/phishing/nginx/access",
            "log_stream_name": "{instance_id}"
          },
          {
            "file_path": "/var/log/gunicorn/error.log",
            "log_group_name": "/aws/ec2/phishing/gunicorn/error",
            "log_stream_name": "{instance_id}"
          }
        ]
      }
    }
  }
}
```

```bash
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
  -a fetch-config -m ec2 -s -c file:/opt/aws/amazon-cloudwatch-agent/etc/config.json
```

### 3. Logs Insights

```bash
CloudWatch → Logs Insights

# Query ejemplo: Errores en últimas 24h
fields @timestamp, @message
| filter @message like /ERROR/
| sort @timestamp desc
| limit 100
```

---

## Backup y Recuperación

### 1. Snapshots de EC2

**Manual:**
```bash
EC2 → Instances → Actions → Image and templates → Create image

Name: phishing-backup-2026-02-01
Description: Pre-deployment backup
```

**Automatizado con AWS Backup:**
```bash
AWS Backup → Create backup plan
→ Build a new plan

Name: phishing-daily-backup
Frequency: Daily at 3:00 AM UTC
Retention: 7 days
Resources: EC2 instance (phishing-platform-prod)
```

### 2. Backups de RDS

**Automáticos:**
- Ya configurados (7 días de retención)
- Se ejecutan durante la ventana de mantenimiento

**Manual:**
```bash
RDS → Databases → phishing-db → Actions → Take snapshot

Name: phishing-db-manual-2026-02-01
```

**Restaurar desde snapshot:**
```bash
RDS → Snapshots → Seleccionar snapshot → Actions → Restore snapshot
```

### 3. Backup de Archivos (S3)

```bash
# Instalar AWS CLI (ya instalado)
# Crear bucket S3
aws s3 mb s3://phishing-platform-backups

# Script de backup
nano /home/ubuntu/backup.sh
```

```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BUCKET="s3://phishing-platform-backups"

# Backup de archivos
tar -czf /tmp/app_$DATE.tar.gz /home/ubuntu/app

# Subir a S3
aws s3 cp /tmp/app_$DATE.tar.gz $BUCKET/

# Limpiar
rm /tmp/app_$DATE.tar.gz

# Eliminar backups antiguos (más de 30 días)
aws s3 ls $BUCKET/ | while read -r line; do
  createDate=$(echo $line | awk '{print $1" "$2}')
  createDate=$(date -d "$createDate" +%s)
  olderThan=$(date -d "30 days ago" +%s)
  if [[ $createDate -lt $olderThan ]]; then
    fileName=$(echo $line | awk '{print $4}')
    aws s3 rm $BUCKET/$fileName
  fi
done
```

```bash
chmod +x /home/ubuntu/backup.sh

# Programar con cron
crontab -e
```

```bash
0 3 * * * /home/ubuntu/backup.sh >> /var/log/backup.log 2>&1
```

---

## Optimización de Costos

### Estimación Mensual

| Servicio | Configuración | Costo/mes |
|----------|---------------|-----------|
| EC2 t3.small | 2 vCPU, 2GB RAM | ~$15 |
| RDS db.t3.micro | 1 vCPU, 1GB RAM | ~$15 |
| EBS Storage | 40 GB (EC2+RDS) | ~$4 |
| Elastic IP | 1 IP asociada | $0 |
| Data Transfer | 10 GB/mes | ~$1 |
| Route 53 | Hosted zone | $0.50 |
| **TOTAL** | | **~$35-40/mes** |

### Estrategias de Ahorro

#### 1. Reserved Instances (1-3 años)

```bash
EC2 → Reserved Instances → Purchase Reserved Instances
→ Ahorro: ~40% vs On-Demand
```

#### 2. Savings Plans

```bash
AWS Cost Management → Savings Plans
→ Compute Savings Plans
→ Ahorro: ~30-40%
```

#### 3. Auto-Scaling (para tráfico variable)

```bash
EC2 → Auto Scaling Groups → Create Auto Scaling group

Min: 1 instance
Desired: 1 instance
Max: 3 instances

Scaling policy:
- Scale up: CPU > 70%
- Scale down: CPU < 30%
```

#### 4. Usar Spot Instances (No recomendado para producción)

```bash
# Ahorro: ~70% pero puede interrumpirse
EC2 → Spot Requests
```

#### 5. Optimizar RDS

```bash
# Cambiar a Aurora Serverless (pago por uso)
RDS → Create database → Amazon Aurora → Serverless

# O usar RDS Proxy para conexiones eficientes
```

---

## CI/CD (Opcional)

### Opción 1: GitHub Actions

**Crear `.github/workflows/deploy.yml`:**

```yaml
name: Deploy to AWS

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v2
      with:
        aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
        aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        aws-region: eu-west-1
    
    - name: Deploy to EC2
      run: |
        ssh -i ${{ secrets.SSH_PRIVATE_KEY }} ubuntu@${{ secrets.EC2_IP }} << 'EOF'
          cd /home/ubuntu/app
          git pull origin main
          source venv/bin/activate
          pip install -r requirements.txt
          sudo systemctl restart phishing-platform
        EOF
```

### Opción 2: AWS CodeDeploy

```bash
# Instalar agente en EC2
sudo apt install -y ruby wget
cd /tmp
wget https://aws-codedeploy-eu-west-1.s3.eu-west-1.amazonaws.com/latest/install
chmod +x ./install
sudo ./install auto

# Crear appspec.yml en el proyecto
```

```yaml
version: 0.0
os: linux
files:
  - source: /
    destination: /home/ubuntu/app
hooks:
  AfterInstall:
    - location: scripts/install_dependencies.sh
      timeout: 300
  ApplicationStart:
    - location: scripts/start_server.sh
      timeout: 300
```

---

## Verificación Final

### Checklist de Despliegue AWS

- [ ] Instancia EC2 creada y corriendo
- [ ] IP Elástica asignada
- [ ] Security Groups configurados correctamente
- [ ] RDS MySQL creado y accesible desde EC2
- [ ] Aplicación instalada y configurada
- [ ] Gunicorn corriendo como servicio
- [ ] Nginx configurado y funcionando
- [ ] Dominio configurado en Route 53
- [ ] Certificado SSL activo (ACM o Let's Encrypt)
- [ ] ALB configurado (si se usa)
- [ ] CloudWatch Logs habilitado
- [ ] Alarmas de CloudWatch configuradas
- [ ] Backups automáticos configurados
- [ ] Acceso SSH restringido a tu IP
- [ ] WAF configurado (opcional)

### Pruebas

```bash
# 1. Verificar aplicación
curl https://phishing.tu-dominio.com

# 2. Verificar SSL
openssl s_client -connect phishing.tu-dominio.com:443

# 3. Verificar logs
sudo journalctl -u phishing-platform -f

# 4. Verificar conexión a RDS
mysql -h ENDPOINT_RDS -u admin -p

# 5. Test de carga (opcional)
ab -n 1000 -c 10 https://phishing.tu-dominio.com/
```

---

## Solución de Problemas

### Error de conexión a RDS

```bash
# Verificar Security Group
aws ec2 describe-security-groups --group-ids sg-12345678

# Verificar conectividad
telnet ENDPOINT_RDS 3306

# Ver logs de RDS
RDS → Databases → phishing-db → Logs & events
```

### Aplicación no arranca

```bash
# Ver logs detallados
sudo journalctl -u phishing-platform -n 100 --no-pager

# Verificar variables de entorno
cat /home/ubuntu/app/.env

# Probar manualmente
cd /home/ubuntu/app
source venv/bin/activate
gunicorn wsgi:app
```

### SSL no funciona

```bash
# Verificar certificado ACM
aws acm list-certificates --region eu-west-1

# Verificar listener de ALB
aws elbv2 describe-listeners --load-balancer-arn ARN_DEL_ALB

# Renovar Let's Encrypt
sudo certbot renew --force-renewal
```

---

## Ventajas y Desventajas AWS

### ✅ Ventajas
- Alta disponibilidad (99.99% SLA)
- Escalabilidad automática
- Backups gestionados
- Seguridad robusta
- Monitoreo integrado
- Soporte 24/7 (con plan)

### ❌ Desventajas
- Costo mensual recurrente (~$35-40)
- Curva de aprendizaje
- Facturación compleja
- Vendor lock-in

---

## Comparación: Home Server vs AWS

| Aspecto | Home Server | AWS |
|---------|-------------|-----|
| **Costo inicial** | €100-300 | $0 |
| **Costo mensual** | ~€2 | ~$35-40 |
| **Disponibilidad** | 95-98% | 99.99% |
| **Escalabilidad** | Manual | Automática |
| **Mantenimiento** | Alto | Bajo |
| **Seguridad** | Tu responsabilidad | Compartida |
| **Backups** | Manual | Automático |
| **Soporte** | Ninguno | Disponible |

---

**Versión:** 1.0  
**Última actualización:** Febrero 2026  
**Soporte:** RKR Security Team
