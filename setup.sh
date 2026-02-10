#!/bin/bash

# RKR Phishing Platform - Comprehensive Setup Script
# Run with: chmod +x setup.sh && ./setup.sh

set -e # Exit on error

echo "--- 1. Instalando dependencias del sistema ---"
sudo apt update
sudo apt install -y python3 python3-pip python3-venv python3-dev \
    mariadb-server mariadb-client nginx build-essential \
    libssl-dev libffi-dev default-libmysqlclient-dev pkg-config \
    certbot python3-certbot-nginx git curl ufw

echo "--- 2. Iniciando y configurando MariaDB ---"
sudo systemctl start mariadb
sudo systemctl enable mariadb

# Variables de la base de datos
DB_NAME="rkrphishing"
DB_USER="rkr_user"
DB_PASS="6303ade57187a1a69d13fa540eb01725dc4b103de7cbd7592b07de9d302721d4"

echo "Configurando base de datos y usuario..."
sudo mariadb -u root <<EOF
CREATE DATABASE IF NOT EXISTS $DB_NAME;
CREATE USER IF NOT EXISTS '$DB_USER'@'localhost' IDENTIFIED BY '$DB_PASS';
GRANT ALL PRIVILEGES ON $DB_NAME.* TO '$DB_USER'@'localhost';
ALTER USER '$DB_USER'@'localhost' IDENTIFIED BY '$DB_PASS';
FLUSH PRIVILEGES;
EOF

echo "Importando esquema desde database_schema.sql..."
if [ -f "database_schema.sql" ]; then
    sudo mariadb -u root $DB_NAME < database_schema.sql
else
    echo "¡ADVERTENCIA! No se encontró database_schema.sql. Saltando importación."
fi

echo "--- 3. Configurando entorno de Python ---"
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "Entorno virtual creado."
fi

source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "--- 4. Preparando archivo .env ---"
if [ ! -f ".env" ]; then
    cat <<EOF > .env
SECRET_KEY=8508386623d2749190817b754e4c492889717eb4f258b59b4c128a4ecb32d57b
DATABASE_URL=mysql://$DB_USER:$DB_PASS@127.0.0.1/$DB_NAME
FLASK_ENV=development
FLASK_DEBUG=1
EOF
    echo "Archivo .env creado."
else
    echo "El archivo .env ya existe. No se ha modificado."
fi