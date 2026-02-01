# Guía de Usuario - RKR Phishing Platform

## 📋 Tabla de Contenidos
1. [Introducción](#introducción)
2. [Primeros Pasos](#primeros-pasos)
3. [Panel de Administración](#panel-de-administración)
4. [Dashboard de Cliente](#dashboard-de-cliente)
5. [Creación de Campañas](#creación-de-campañas)
6. [Integración del Tracker](#integración-del-tracker)
7. [Análisis de Resultados](#análisis-de-resultados)
8. [Mejores Prácticas](#mejores-prácticas)

---

## Introducción

RKR Phishing Platform es una herramienta ética de simulación de phishing diseñada para evaluar la concienciación de seguridad en organizaciones. Permite crear campañas controladas, rastrear interacciones de usuarios y generar informes detallados.

### Características Principales
- ✅ Gestión multi-cliente con aislamiento de datos
- ✅ Sistema de tracking en tiempo real
- ✅ Dashboard con métricas visuales
- ✅ Protección de datos sensibles (no almacena contraseñas)
- ✅ API REST para integración

---

## Primeros Pasos

### Requisitos Previos
- Python 3.8+
- MySQL/MariaDB
- Navegador web moderno

### Instalación

1. **Instalar librerías del sistema**
```bash
sudo apt-get install python3-dev default-libmysqlclient-dev build-essential
```

2. **Clonar el repositorio**
```bash
cd /ruta/a/tu/proyecto
```

3. **Crear entorno virtual**
```bash
python3 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

4. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

5. **Configurar base de datos**
Edita `instance/config.py`:
```python
SQLALCHEMY_DATABASE_URI = "mysql://usuario:contraseña@localhost/nombre_bd"
```

6. **Inicializar la base de datos**
```bash
python3 scripts/reset_db.py
python3 scripts/create_admin.py
```

7. **Ejecutar la aplicación**
```bash
python3 wsgi.py
```

Accede a: `http://127.0.0.1:5000`

### Primer Login
- **Usuario:** `admin`
- **Contraseña:** La que configuraste en `create_admin.py`

---

## Panel de Administración

El panel de administración está organizado en **3 pestañas principales**.

### 🏢 Pestaña: Clients

#### Ver Clientes
Muestra todos los clientes registrados con:
- ID único
- Nombre de la organización
- API Key (primeros 12 caracteres)
- Fecha de creación
- Acciones disponibles

#### Crear Nuevo Cliente
1. En el panel derecho, completa el formulario "Create New Client"
2. Introduce el nombre de la organización
3. Haz clic en **Register Client**
4. Se generará automáticamente un API Key único

#### Editar Cliente
1. En "Quick Edit", selecciona el cliente del dropdown
2. Introduce el nuevo nombre
3. Haz clic en **Update Name**

#### Eliminar Cliente
> ⚠️ **ADVERTENCIA:** Esta acción eliminará TODOS los datos asociados (usuarios, campañas, eventos, sesiones)

1. Haz clic en el botón **Delete** junto al cliente
2. Confirma la acción en el diálogo

**Protección:** El cliente "Admin Org" (ID: 1) no puede ser eliminado.

---

### 👥 Pestaña: Users

#### Ver Usuarios
Lista todos los usuarios del sistema con:
- ID
- Username
- Organización a la que pertenecen
- Rol (Admin/Analyst)
- Acciones

#### Crear Nuevo Usuario
1. Selecciona la **organización** del dropdown
2. Introduce el **username**
3. Introduce la **contraseña**
4. Selecciona el **rol**:
   - **Analyst:** Acceso solo al dashboard de su cliente
   - **Administrator:** Acceso completo al panel de admin
5. Haz clic en **Create User**

#### Editar Usuario
1. En "Quick Edit User", selecciona el usuario
2. Modifica los campos que desees:
   - Username (dejar en blanco para mantener)
   - Password (dejar en blanco para mantener)
   - Role
3. Haz clic en **Update User**

#### Eliminar Usuario
> ⚠️ **ADVERTENCIA:** El usuario `admin` no puede ser eliminado

1. Haz clic en **Delete** junto al usuario
2. Confirma la acción

---

### 🎯 Pestaña: Campaigns

#### Ver Campañas
Muestra todas las campañas activas:
- ID de la campaña
- Nombre
- Cliente propietario
- Fecha de creación

#### Crear Nueva Campaña
1. Selecciona la **organización objetivo**
2. Introduce el **nombre de la campaña** (ej: "Q1 Security Audit")
3. Haz clic en **Start Campaign**

**Importante:** Guarda el **Campaign ID** generado, lo necesitarás para el tracker.

---

## Dashboard de Cliente

Cuando un usuario con rol **Analyst** inicia sesión, accede al Dashboard de su organización.

### Información Mostrada

#### Encabezado
- Nombre del usuario logeado
- Organización a la que pertenece
- Selector de campaña (si hay múltiples)

#### Métricas Principales
1. **Total Visits:** Número total de visitas rastreadas
2. **Unique Visitors:** Visitantes únicos (por sesión)
3. **Credentials Captured:** Cantidad de formularios enviados

#### Gráfico de Actividad
Visualización de:
- Visitas totales
- Credenciales capturadas

---

## Creación de Campañas

### Flujo Completo

#### 1. Crear la Campaña
Desde el panel de admin:
- Ve a la pestaña **Campaigns**
- Crea una nueva campaña
- **Anota el Campaign ID y el API Key del cliente**

#### 2. Crear la Landing Page
Crea tu página HTML de phishing simulado. Ejemplo básico:

```html
<!DOCTYPE html>
<html>
<head>
    <title>Login - Microsoft</title>
</head>
<body>
    <h1>Microsoft Account</h1>
    <form id="loginForm">
        <input type="email" name="username" placeholder="Email" required>
        <input type="password" name="password" placeholder="Password" required>
        <button type="submit">Sign In</button>
    </form>

    <!-- Tracker Script -->
    <script 
        src="http://127.0.0.1:5000/static/js/tracker.js"
        data-api-key="TU_API_KEY_AQUI"
        data-campaign-id="TU_CAMPAIGN_ID_AQUI">
    </script>
</body>
</html>
```

#### 3. Configurar el Tracker
Reemplaza en el script:
- `TU_API_KEY_AQUI` → API Key del cliente
- `TU_CAMPAIGN_ID_AQUI` → ID de la campaña creada

#### 4. Desplegar la Landing Page
- Sube la página a un servidor web
- Comparte el enlace con los participantes de la campaña

---

## Integración del Tracker

### ¿Qué Hace el Tracker?

El script `tracker.js` automáticamente:
1. ✅ Registra cada visita a la página
2. ✅ Captura envíos de formularios
3. ✅ Crea sesiones únicas por usuario
4. ✅ **Sanitiza datos sensibles** (contraseñas se reemplazan por `[REDACTED]`)

### Configuración Avanzada

#### Atributos del Script
```html
<script 
    src="http://TU_DOMINIO/static/js/tracker.js"
    data-api-key="abc123..."
    data-campaign-id="5"
    data-landing-id="1">  <!-- Opcional -->
</script>
```

#### Eventos Rastreados

| Evento | Descripción |
|--------|-------------|
| `visit` | Usuario accede a la página |
| `credentials_submitted` | Usuario envía un formulario |

### Seguridad del Tracker

> 🔒 **Protección de Datos Sensibles**

El sistema **NUNCA** almacena:
- Contraseñas
- Números de tarjeta de crédito
- Tokens de seguridad
- Claves API

Campos detectados como sensibles se reemplazan automáticamente por `[REDACTED]`.

---

## Análisis de Resultados

### Métricas Clave

#### 1. Total Visits
- **Qué mide:** Número total de accesos a la landing page
- **Uso:** Evaluar alcance de la campaña

#### 2. Unique Visitors
- **Qué mide:** Usuarios únicos que visitaron
- **Uso:** Tasa de participación real

#### 3. Credentials Captured
- **Qué mide:** Formularios enviados
- **Uso:** Tasa de éxito del phishing simulado
- **Cálculo:** `(Credentials / Visits) × 100 = % de efectividad`

### Interpretación

| Tasa de Captura | Interpretación |
|-----------------|----------------|
| < 5% | ✅ Excelente concienciación |
| 5-15% | ⚠️ Concienciación moderada |
| 15-30% | ⚠️ Requiere formación |
| > 30% | 🚨 Alto riesgo - Formación urgente |

---

## Mejores Prácticas

### Para Administradores

1. **Gestión de Clientes**
   - Crea un cliente por organización
   - Usa nombres descriptivos
   - Guarda las API Keys de forma segura

2. **Gestión de Usuarios**
   - Asigna roles apropiados
   - Usa contraseñas fuertes
   - Revisa periódicamente los accesos

3. **Seguridad**
   - Cambia las credenciales por defecto
   - Mantén actualizado el sistema
   - Realiza backups regulares

### Para Campañas

1. **Planificación**
   - Define objetivos claros
   - Identifica el público objetivo
   - Establece métricas de éxito

2. **Diseño de Landing Pages**
   - Simula sitios reales (con autorización)
   - Incluye elementos visuales creíbles
   - Mantén la ética profesional

3. **Comunicación**
   - Informa a RRHH antes de la campaña
   - Prepara material educativo post-campaña
   - Ofrece formación a los afectados

4. **Análisis Post-Campaña**
   - Revisa las métricas obtenidas
   - Identifica patrones de comportamiento
   - Implementa mejoras de seguridad

### Consideraciones Éticas

> ⚖️ **Uso Responsable**

Esta plataforma debe usarse ÚNICAMENTE para:
- ✅ Formación interna autorizada
- ✅ Auditorías de seguridad contratadas
- ✅ Investigación académica con consentimiento

**NUNCA para:**
- ❌ Phishing real
- ❌ Robo de credenciales
- ❌ Actividades ilegales

---

## Solución de Problemas

### El tracker no registra eventos

**Posibles causas:**
1. API Key incorrecta → Verifica en el panel de admin
2. Campaign ID inválido → Asegúrate de que la campaña existe
3. CORS bloqueado → Verifica la configuración del servidor
4. Script no cargado → Revisa la consola del navegador

**Solución:**
```javascript
// Abre la consola del navegador (F12)
// Busca errores relacionados con "RKR Tracker"
```

### No puedo eliminar un cliente

**Causa:** El cliente tiene datos relacionados
**Solución:** El sistema ahora elimina automáticamente todos los datos relacionados. Si persiste el error, contacta con soporte técnico.

### Las métricas no se actualizan

**Solución:**
1. Refresca la página del dashboard
2. Cambia de campaña y vuelve a la original
3. Verifica que los eventos se están registrando en la base de datos

---

## Soporte y Recursos

### Archivos de Utilidad

Ubicados en `scripts/`:
- `reset_db.py` - Reinicia la base de datos
- `create_admin.py` - Crea usuario administrador
- `check_data.py` - Verifica datos en la BD
- `cleanup_db.py` - Limpia datos de prueba

### Ejecución de Scripts
```bash
cd /ruta/al/proyecto
python3 scripts/nombre_script.py
```

---

## Glosario

- **Client:** Organización que usa la plataforma
- **Campaign:** Simulación de phishing específica
- **Landing Page:** Página web falsa usada en la simulación
- **Tracker:** Script JavaScript que registra interacciones
- **Event:** Acción del usuario (visita, envío de formulario)
- **Session:** Conjunto de eventos de un mismo usuario
- **API Key:** Clave de autenticación única por cliente

---

**Versión:** 1.0  
**Última actualización:** Febrero 2026  
**Desarrollado por:** RKR Security Team

