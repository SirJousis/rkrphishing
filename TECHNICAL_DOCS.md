# Documentación Técnica - RKR Phishing Platform

## 📋 Tabla de Contenidos
1. [Arquitectura del Sistema](#arquitectura-del-sistema)
2. [Estructura del Proyecto](#estructura-del-proyecto)
3. [Modelos de Datos](#modelos-de-datos)
4. [Rutas y Endpoints](#rutas-y-endpoints)
5. [Sistema de Autenticación](#sistema-de-autenticación)
6. [Tracker JavaScript](#tracker-javascript)
7. [Frontend](#frontend)
8. [Seguridad](#seguridad)
9. [Base de Datos](#base-de-datos)
10. [Despliegue](#despliegue)

---

## Arquitectura del Sistema

### Stack Tecnológico

```
┌─────────────────────────────────────────┐
│           Frontend (HTML/CSS/JS)        │
│  - Jinja2 Templates                     │
│  - Chart.js (visualización)             │
│  - Vanilla JavaScript (tracker)         │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│         Backend (Flask/Python)          │
│  - Flask 2.x                            │
│  - Flask-Login (sesiones)               │
│  - Flask-SQLAlchemy (ORM)               │
│  - Flask-CORS                           │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│       Base de Datos (MySQL/MariaDB)     │
│  - InnoDB Engine                        │
│  - Relaciones con Foreign Keys          │
└─────────────────────────────────────────┘
```

### Patrón de Diseño

**MVC (Model-View-Controller)**
- **Models:** `app/models/` - Definición de entidades
- **Views:** `app/templates/` - Plantillas Jinja2
- **Controllers:** `app/routes/` - Lógica de negocio

**Blueprints de Flask:**
- Modularización de rutas
- Separación de responsabilidades
- Escalabilidad

---

## Estructura del Proyecto

```
phishing-platform/
├── app/
│   ├── __init__.py              # Factory de la aplicación
│   ├── extensions.py            # Inicialización de extensiones
│   ├── auth/
│   │   ├── api_key.py          # Decorador de autenticación API
│   │   └── routes.py           # Rutas de login/logout
│   ├── config/
│   │   └── settings.py         # Configuración global
│   ├── models/
│   │   ├── client.py           # Modelo Client
│   │   ├── user.py             # Modelo User
│   │   ├── campaign.py         # Modelo Campaign
│   │   ├── landing.py          # Modelo Landing
│   │   ├── session.py          # Modelo VisitSession
│   │   └── event.py            # Modelo Event
│   ├── routes/
│   │   ├── admin.py            # Panel de administración
│   │   ├── dashboard.py        # Dashboard de clientes
│   │   └── track.py            # Endpoint de tracking
│   ├── static/
│   │   ├── css/
│   │   │   └── styles.css      # Estilos globales
│   │   └── js/
│   │       ├── tracker.js      # Script de tracking
│   │       └── charts.js       # Configuración de gráficos
│   └── templates/
│       ├── base.html           # Template base
│       ├── auth/
│       │   └── login.html      # Página de login
│       ├── admin/
│       │   └── index.html      # Panel de admin
│       └── dashboard/
│           └── index.html      # Dashboard de cliente
├── instance/
│   └── config.py               # Configuración de instancia
├── scripts/
│   ├── reset_db.py             # Reiniciar BD
│   ├── create_admin.py         # Crear admin
│   ├── check_data.py           # Verificar datos
│   └── cleanup_db.py           # Limpiar datos
├── wsgi.py                     # Punto de entrada
└── requirements.txt            # Dependencias
```

---

## Modelos de Datos

### Diagrama ER

```mermaid
erDiagram
    CLIENT ||--o{ USER : has
    CLIENT ||--o{ CAMPAIGN : owns
    CLIENT ||--o{ LANDING : has
    CLIENT ||--o{ VISIT_SESSION : tracks
    CLIENT ||--o{ EVENT : records
    
    CAMPAIGN ||--o{ LANDING : includes
    CAMPAIGN ||--o{ VISIT_SESSION : belongs_to
    
    LANDING ||--o{ VISIT_SESSION : generates
    
    VISIT_SESSION ||--o{ EVENT : contains
    
    CLIENT {
        int id PK
        string name
        string api_key UK
        datetime created_at
    }
    
    USER {
        int id PK
        int client_id FK
        string username UK
        string password_hash
        enum role
        datetime created_at
    }
    
    CAMPAIGN {
        int id PK
        int client_id FK
        string name
        datetime start_date
        datetime end_date
        datetime created_at
    }
    
    LANDING {
        int id PK
        int client_id FK
        int campaign_id FK
        string name
        string url
        datetime created_at
    }
    
    VISIT_SESSION {
        int id PK
        int client_id FK
        int campaign_id FK
        int landing_id FK
        string session_uuid UK
        string ip_address
        text user_agent
        datetime started_at
    }
    
    EVENT {
        int id PK
        int client_id FK
        int session_id FK
        enum event_type
        json event_data
        datetime created_at
    }
```

### Client (`app/models/client.py`)

```python
class Client(db.Model):
    __tablename__ = "clients"
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False)
    api_key = db.Column(db.String(64), unique=True, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
```

**Propósito:** Representa una organización que usa la plataforma.

**Características:**
- API Key única generada automáticamente
- Aislamiento de datos por cliente
- Relaciones con usuarios, campañas y eventos

**Métodos:**
- `generate_api_key()`: Genera un token SHA-256 único

### User (`app/models/user.py`)

```python
class User(UserMixin, db.Model):
    __tablename__ = "users"
    
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey("clients.id"))
    username = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum("admin", "analyst"), default="analyst")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
```

**Propósito:** Usuarios del sistema con diferentes roles.

**Roles:**
- `admin`: Acceso completo al panel de administración
- `analyst`: Acceso solo al dashboard de su cliente

**Integración con Flask-Login:**
- Hereda de `UserMixin`
- Implementa `load_user()` para gestión de sesiones

### Campaign (`app/models/campaign.py`)

```python
class Campaign(db.Model):
    __tablename__ = "campaigns"
    
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey("clients.id"))
    name = db.Column(db.String(255), nullable=False)
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
```

**Propósito:** Representa una campaña de phishing simulado.

**Uso:**
- Agrupa eventos y sesiones
- Permite análisis por campaña
- Filtrado en dashboard

### VisitSession (`app/models/session.py`)

```python
class VisitSession(db.Model):
    __tablename__ = "visit_sessions"
    
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey("clients.id"))
    campaign_id = db.Column(db.Integer, db.ForeignKey("campaigns.id"))
    landing_id = db.Column(db.Integer, db.ForeignKey("landings.id"))
    session_uuid = db.Column(db.String(64), unique=True, index=True)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
```

**Propósito:** Agrupa eventos de un mismo usuario/navegador.

**Identificación:**
- UUID único almacenado en `localStorage`
- Permite tracking entre páginas
- Asociación con IP y User-Agent

### Event (`app/models/event.py`)

```python
class Event(db.Model):
    __tablename__ = "events"
    
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey("clients.id"))
    session_id = db.Column(db.Integer, db.ForeignKey("visit_sessions.id"))
    event_type = db.Column(db.Enum(
        "visit", "click", "credentials_submitted", "time_on_page"
    ))
    event_data = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
```

**Propósito:** Registra acciones individuales del usuario.

**Tipos de Eventos:**
- `visit`: Acceso a la página
- `credentials_submitted`: Envío de formulario
- `click`: Click en elemento (futuro)
- `time_on_page`: Tiempo de permanencia (futuro)

**event_data (JSON):**
```json
{
  "username": "user@example.com",
  "password": "[REDACTED]",
  "form_id": "loginForm"
}
```

---

## Rutas y Endpoints

### Autenticación (`app/auth/routes.py`)

#### `GET /auth/login`
Muestra el formulario de login.

**Template:** `auth/login.html`

#### `POST /auth/login`
Procesa el login del usuario.

**Parámetros:**
- `username` (string): Nombre de usuario
- `password` (string): Contraseña

**Respuesta:**
- Éxito: Redirección a `/dashboard` o `/admin`
- Error: Mensaje flash + formulario

**Código:**
```python
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            if user.role == "admin":
                return redirect(url_for("admin.index"))
            return redirect(url_for("dashboard.index"))
        
        flash("Invalid credentials")
    
    return render_template("auth/login.html")
```

#### `GET /auth/logout`
Cierra la sesión del usuario.

**Respuesta:** Redirección a `/auth/login`

---

### Admin (`app/routes/admin.py`)

**Middleware:** Todas las rutas requieren `@login_required` y `role == "admin"`

#### `GET /admin/`
Panel de administración principal.

**Datos pasados al template:**
```python
{
    "clients": Client.query.all(),
    "campaigns": Campaign.query.all(),
    "users": User.query.all()
}
```

#### `POST /admin/client/create`
Crea un nuevo cliente.

**Parámetros:**
- `name` (string): Nombre del cliente

**Lógica:**
```python
new_client = Client(name=name)
db.session.add(new_client)
db.session.commit()
```

#### `POST /admin/client/update/<int:id>`
Actualiza el nombre de un cliente.

**Parámetros:**
- `name` (string): Nuevo nombre

#### `POST /admin/client/delete/<int:id>`
Elimina un cliente y todos sus datos relacionados.

**Orden de eliminación:**
1. Events
2. VisitSessions
3. Landings
4. Campaigns
5. Users
6. Client

**Protección:** No permite eliminar `client_id == 1`

#### `POST /admin/user/create`
Crea un nuevo usuario.

**Parámetros:**
- `client_id` (int)
- `username` (string)
- `password` (string)
- `role` (enum): "admin" | "analyst"

**Hash de contraseña:**
```python
from werkzeug.security import generate_password_hash
password_hash = generate_password_hash(password)
```

#### `POST /admin/user/update/<int:id>`
Actualiza datos de un usuario.

**Parámetros opcionales:**
- `username`
- `password`
- `client_id`
- `role`

#### `POST /admin/user/delete/<int:id>`
Elimina un usuario.

**Protección:** No permite eliminar `username == "admin"`

#### `POST /admin/campaign/create`
Crea una nueva campaña.

**Parámetros:**
- `client_id` (int)
- `name` (string)

---

### Dashboard (`app/routes/dashboard.py`)

#### `GET /dashboard/`
Dashboard del cliente.

**Acceso:** Solo usuarios con `role == "analyst"` o admin

**Lógica:**
```python
@dashboard_bp.route("/")
@login_required
def index():
    if current_user.role == "admin":
        return redirect(url_for("admin.index"))
    
    client = current_user.client
    
    # Métricas
    total_visits = Event.query.filter_by(
        client_id=client.id,
        event_type="visit"
    ).count()
    
    unique_visitors = VisitSession.query.filter_by(
        client_id=client.id
    ).distinct(VisitSession.session_uuid).count()
    
    credentials_captured = Event.query.filter_by(
        client_id=client.id,
        event_type="credentials_submitted"
    ).count()
    
    campaigns = Campaign.query.filter_by(client_id=client.id).all()
    
    return render_template("dashboard/index.html", ...)
```

---

### Tracking (`app/routes/track.py`)

#### `POST /track`
Endpoint para registrar eventos desde el tracker JavaScript.

**Autenticación:** `@require_api_key` (vía header o query param)

**Parámetros JSON:**
```json
{
  "session_uuid": "abc123...",
  "event_type": "visit" | "credentials_submitted",
  "campaign_id": 5,
  "landing_id": 2,
  "event_data": {
    "username": "user@example.com",
    "password": "secret123"
  }
}
```

**Flujo:**
1. Validar API Key → Obtener `client`
2. Validar `campaign_id` pertenece al cliente
3. Buscar o crear `VisitSession`
4. **Sanitizar `event_data`** (eliminar contraseñas)
5. Crear `Event`
6. Commit a BD

**Sanitización:**
```python
def sanitize_event_data(event_data):
    if not event_data or not isinstance(event_data, dict):
        return event_data
    
    sensitive_fields = [
        'password', 'passwd', 'pwd', 'pass',
        'secret', 'token', 'api_key',
        'credit_card', 'cvv', 'ssn', 'pin'
    ]
    
    sanitized = event_data.copy()
    
    for key in list(sanitized.keys()):
        if key.lower() in sensitive_fields:
            sanitized[key] = "[REDACTED]"
    
    return sanitized
```

**Respuesta:**
```json
{
  "status": "ok",
  "session_uuid": "abc123..."
}
```

---

## Sistema de Autenticación

### Flask-Login

**Configuración (`app/__init__.py`):**
```python
from flask_login import LoginManager

login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.init_app(app)
```

**User Loader (`app/models/user.py`):**
```python
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
```

### API Key Authentication

**Decorador (`app/auth/api_key.py`):**
```python
from functools import wraps
from flask import request, jsonify

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get("X-API-Key") or \
                  request.args.get("api_key")
        
        if not api_key:
            return jsonify({"error": "API key required"}), 401
        
        client = Client.query.filter_by(api_key=api_key).first()
        
        if not client:
            return jsonify({"error": "Invalid API key"}), 403
        
        # Inyectar cliente en el request
        request.client = client
        
        return f(*args, **kwargs)
    
    return decorated_function
```

**Uso:**
```python
@track_bp.route("/track", methods=["POST"])
@require_api_key
def track():
    client = request.client  # Cliente autenticado
    # ...
```

---

## Tracker JavaScript

### Archivo: `app/static/js/tracker.js`

**Funcionalidad:**
1. Auto-inicialización al cargar la página
2. Gestión de sesiones con `localStorage`
3. Registro automático de visitas
4. Captura de envíos de formularios

### Inicialización

```javascript
(function() {
    const currentScript = document.currentScript;
    const API_KEY = currentScript.getAttribute('data-api-key');
    const CAMPAIGN_ID = currentScript.getAttribute('data-campaign-id');
    const LANDING_ID = currentScript.getAttribute('data-landing-id');
    
    // Determinar URL del endpoint
    let API_URL;
    const urlObj = new URL(currentScript.src);
    if (urlObj.protocol === 'file:') {
        API_URL = 'http://127.0.0.1:5000/track';
    } else {
        API_URL = `${urlObj.protocol}//${urlObj.host}/track`;
    }
    
    // Obtener o crear session UUID
    let sessionUUID = localStorage.getItem('rkr_session_uuid');
    if (!sessionUUID) {
        sessionUUID = generateUUID();
        localStorage.setItem('rkr_session_uuid', sessionUUID);
    }
    
    // Registrar visita automáticamente
    trackEvent('visit', {});
})();
```

### Función de Tracking

```javascript
function trackEvent(eventType, eventData) {
    const payload = {
        session_uuid: sessionUUID,
        event_type: eventType,
        campaign_id: CAMPAIGN_ID ? parseInt(CAMPAIGN_ID) : null,
        landing_id: LANDING_ID ? parseInt(LANDING_ID) : null,
        event_data: eventData
    };
    
    fetch(API_URL, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-API-Key': API_KEY
        },
        body: JSON.stringify(payload)
    })
    .then(response => response.json())
    .then(data => {
        console.log('[RKR Tracker] Event tracked:', eventType);
    })
    .catch(error => {
        console.error('[RKR Tracker] Error:', error);
    });
}
```

### Captura de Formularios

```javascript
document.addEventListener('DOMContentLoaded', function() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            // Capturar datos del formulario
            const formData = new FormData(form);
            const data = {};
            
            formData.forEach((value, key) => {
                data[key] = value;
            });
            
            // Registrar evento
            trackEvent('credentials_submitted', data);
            
            // Prevenir envío real (opcional)
            // e.preventDefault();
        });
    });
});
```

### Generación de UUID

```javascript
function generateUUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        const r = Math.random() * 16 | 0;
        const v = c === 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}
```

---

## Frontend

### Sistema de Tabs (Admin Panel)

**HTML:**
```html
<div class="tabs-nav">
    <button class="tab-btn active" onclick="showTab('clients', event)">Clients</button>
    <button class="tab-btn" onclick="showTab('users', event)">Users</button>
    <button class="tab-btn" onclick="showTab('campaigns', event)">Campaigns</button>
</div>

<div id="clients" class="tab-pane active">
    <!-- Contenido de Clients -->
</div>

<div id="users" class="tab-pane">
    <!-- Contenido de Users -->
</div>

<div id="campaigns" class="tab-pane">
    <!-- Contenido de Campaigns -->
</div>
```

**JavaScript:**
```javascript
function showTab(tabId, event) {
    // Ocultar todos los panes
    document.querySelectorAll('.tab-pane').forEach(p => 
        p.classList.remove('active')
    );
    
    // Desactivar todos los botones
    document.querySelectorAll('.tab-btn').forEach(b => 
        b.classList.remove('active')
    );
    
    // Mostrar el seleccionado
    document.getElementById(tabId).classList.add('active');
    event.currentTarget.classList.add('active');
}
```

**CSS:**
```css
.tab-pane {
    display: none;
}

.tab-pane.active {
    display: grid;
    grid-template-columns: 1fr 350px;
    gap: 1.5rem;
    animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}
```

### Chart.js Integration

**Template (`dashboard/index.html`):**
```html
<div class="chart-container">
    <canvas id="activityChart"></canvas>
</div>

<script>
const chartData = {
    visits: {{ total_visits | default(0) }},
    credentials: {{ credentials_captured | default(0) }}
};
</script>
<script src="{{ url_for('static', filename='js/charts.js') }}"></script>
```

**JavaScript (`charts.js`):**
```javascript
const ctx = document.getElementById('activityChart').getContext('2d');

new Chart(ctx, {
    type: 'doughnut',
    data: {
        labels: ['Visits', 'Credentials Captured'],
        datasets: [{
            data: [chartData.visits, chartData.credentials],
            backgroundColor: ['#6366f1', '#ef4444']
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false
    }
});
```

---

## Seguridad

### Protección de Datos Sensibles

**Sanitización en Backend:**
- Campos detectados: `password`, `secret`, `token`, `cvv`, etc.
- Reemplazo: `[REDACTED]`
- Ubicación: `app/routes/track.py::sanitize_event_data()`

### Hashing de Contraseñas

```python
from werkzeug.security import generate_password_hash, check_password_hash

# Al crear usuario
password_hash = generate_password_hash(password)

# Al verificar login
if check_password_hash(user.password_hash, password):
    # Login exitoso
```

**Algoritmo:** PBKDF2-SHA256 (por defecto en Werkzeug)

### CORS Configuration

```python
from flask_cors import CORS

CORS(app, resources={
    r"/track": {
        "origins": "*",
        "methods": ["POST"],
        "allow_headers": ["Content-Type", "X-API-Key"]
    }
})
```

### SQL Injection Prevention

**SQLAlchemy ORM** previene automáticamente inyección SQL mediante:
- Prepared statements
- Parametrización de queries

**Ejemplo seguro:**
```python
# ✅ SEGURO
User.query.filter_by(username=username).first()

# ❌ INSEGURO (nunca hacer)
db.session.execute(f"SELECT * FROM users WHERE username='{username}'")
```

### XSS Prevention

**Jinja2 Auto-escaping:**
```html
<!-- Automáticamente escapado -->
<p>{{ user.username }}</p>

<!-- Renderizado sin escapar (PELIGROSO) -->
<p>{{ user.bio | safe }}</p>
```

---

## Base de Datos

### Configuración

**Archivo:** `instance/config.py`
```python
SQLALCHEMY_DATABASE_URI = "mysql://user:pass@localhost/dbname"
SQLALCHEMY_TRACK_MODIFICATIONS = False
```

### Migraciones (Futuro)

Para implementar Flask-Migrate:

```bash
pip install Flask-Migrate
```

```python
# app/__init__.py
from flask_migrate import Migrate

migrate = Migrate(app, db)
```

```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

### Índices

**Optimizaciones aplicadas:**
```python
# Índice en API Key para búsquedas rápidas
api_key = db.Column(db.String(64), unique=True, index=True)

# Índice en session_uuid
session_uuid = db.Column(db.String(64), unique=True, index=True)
```

### Backup

**Script de backup:**
```bash
#!/bin/bash
mysqldump -u user -p dbname > backup_$(date +%Y%m%d).sql
```

---

## Despliegue

### Producción con Gunicorn

**Instalación:**
```bash
pip install gunicorn
```

**Ejecución:**
```bash
gunicorn -w 4 -b 0.0.0.0:8000 wsgi:app
```

**Configuración recomendada:**
- Workers: `(2 × CPU cores) + 1`
- Timeout: `120` segundos
- Keep-alive: `5` segundos

### Nginx como Reverse Proxy

**Configuración:**
```nginx
server {
    listen 80;
    server_name phishing.example.com;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
    
    location /static {
        alias /path/to/app/static;
        expires 30d;
    }
}
```

### Variables de Entorno

**Archivo `.env`:**
```bash
SECRET_KEY=your-secret-key-here
SQLALCHEMY_DATABASE_URI=mysql://user:pass@localhost/dbname
FLASK_ENV=production
```

**Carga en Python:**
```python
from dotenv import load_dotenv
load_dotenv()
```

### Systemd Service

**Archivo:** `/etc/systemd/system/rkr-phishing.service`
```ini
[Unit]
Description=RKR Phishing Platform
After=network.target

[Service]
User=www-data
WorkingDirectory=/var/www/phishing-platform
Environment="PATH=/var/www/phishing-platform/venv/bin"
ExecStart=/var/www/phishing-platform/venv/bin/gunicorn -w 4 -b 127.0.0.1:8000 wsgi:app

[Install]
WantedBy=multi-user.target
```

**Comandos:**
```bash
sudo systemctl enable rkr-phishing
sudo systemctl start rkr-phishing
sudo systemctl status rkr-phishing
```

---

## Extensiones Futuras

### Funcionalidades Propuestas

1. **Reportes PDF**
   - Generación automática con ReportLab
   - Gráficos y estadísticas

2. **Notificaciones Email**
   - Alertas de campañas completadas
   - Resúmenes semanales

3. **Análisis Avanzado**
   - Machine Learning para detección de patrones
   - Predicción de vulnerabilidad

4. **Multi-idioma**
   - Flask-Babel para internacionalización
   - Soporte para ES, EN, FR

5. **API REST Completa**
   - Endpoints para integración externa
   - Documentación con Swagger/OpenAPI

---

## Glosario Técnico

- **Blueprint:** Módulo de Flask para organizar rutas
- **ORM:** Object-Relational Mapping (SQLAlchemy)
- **Middleware:** Función que intercepta requests
- **Decorator:** Función que modifica el comportamiento de otra
- **Session:** Datos persistentes del usuario (Flask-Login)
- **UUID:** Identificador único universal
- **CORS:** Cross-Origin Resource Sharing
- **CSRF:** Cross-Site Request Forgery
- **XSS:** Cross-Site Scripting

---

**Versión:** 1.0  
**Última actualización:** Febrero 2026  
**Mantenedor:** RKR Security Team
