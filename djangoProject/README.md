# 🚀 Proyecto Kairos - Plataforma de Trading Algorítmico

Plataforma web profesional para gestión de productos financieros algorítmicos con integración a MetaTrader 5.

## 📋 Características

- ✅ **Autenticación completa** con email y 2FA (Google Authenticator)
- ✅ **Dashboard de usuario** con visualización de capital y productos
- ✅ **Gestión de productos financieros** (M.P.T MarketProThief, GoldenRoad, MultiMarkets)
- ✅ **Resultados históricos** con gráficas interactivas (Chart.js)
- ✅ **Sistema de verificación** de email
- ✅ **Panel de administración** personalizado
- ✅ **Newsletter** de suscripción
- ✅ **Páginas informativas** (How We Work, Connect MT5)
- ✅ **Diseño responsive** con paleta azul profesional

## 🛠️ Tecnologías

- **Backend:** Django 4.2.26
- **Base de datos:** SQLite (desarrollo) / PostgreSQL (producción)
- **Frontend:** HTML5, CSS3, JavaScript
- **Gráficas:** Chart.js
- **Autenticación:** Django Auth + PyOTP (2FA)
- **Email:** Django Email Backend

## 📦 Instalación

### 1. Clonar el repositorio

```bash
git clone <url-del-repo>
cd djangoProject
```

### 2. Crear entorno virtual

```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

### 3. Instalar dependencias

pip install -r requirements.TXT

### o en su defecto:

```bash
pip install django==4.2.26
pip install pillow
pip install pyotp
pip install qrcode
```

### 4. Configurar base de datos

```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Cargar datos iniciales

```bash
python manage.py load_initial_data
```

### 6. Crear superusuario

```bash
python manage.py createsuperuser
```
### 7. Recuerda ejecutar python manage.py collectstatic 
si estás usando archivos estáticos en producción para que 
los cambios se reflejen.

### 8. Ejecutar servidor

```bash
python manage.py runserver
```

Accede a: `http://127.0.0.1:8000/`

## 📂 Estructura del Proyecto

```
djangoProject/
├── djangoProject/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── appKairos/
│   ├── management/
│   │   └── commands/
│   │       └── load_initial_data.py
│   ├── static/
│   │   └── css/
│   │       ├── styles.css
│   │       ├── dashboard.css
│   │       ├── connect.css
│   │       ├── howdowework.css
│   │       ├── auth.css
│   │       └── newsletter.css
│   ├── templates/
│   │   ├── index_en.html
│   │   ├── login_en.html
│   │   ├── register_en.html
│   │   ├── dashboard_en.html
│   │   ├── connect_en.html
│   │   ├── howdowework_en.html
│   │   ├── newsletter_en.html
│   │   └── verify-email_en.html
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── backends.py
│   ├── forms.py
│   ├── models.py
│   ├── urls.py
│   └── views.py
├── manage.py
└── README.md
```

## 🗄️ Modelos de Datos

### Usuario
- Email único (login)
- Autenticación 2FA
- Capital total
- Productos contratados

### Mercado
- XAUUSD (Oro)
- NASDAQ
- S&P 500

### Producto
- M.P.T MarketProThief
- GoldenRoad
- MultiMarkets

### ProductoContratado
- Relación Usuario-Producto
- Monto invertido
- Estado (active/inactive/pending)

### Resultado
- Historial mensual
- Capital por período
- Cambios y porcentajes

## 🔐 Autenticación

### Login con Email
Los usuarios inician sesión con su email en lugar de username.

### Verificación de Email
Al registrarse, se envía un token de verificación por email.

### 2FA (Google Authenticator)
Los usuarios pueden activar autenticación de dos factores escaneando un código QR.

## 🎨 Diseño

### Paleta de Colores
- `#0077b6` - Azul principal
- `#00b4d8` - Azul claro
- `#00ddff` - Cyan neón (hover)
- `whitesmoke` - Texto
- Transparencias: `rgba(0,0,0,0.4-0.7)`

### Fuentes
- Space Grotesk (principal)
- Outfit (botones)

## 📧 Configuración de Email

### Desarrollo (Consola)
```python
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

### Producción (SMTP)
```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'tu_email@gmail.com'
EMAIL_HOST_PASSWORD = 'tu_app_password'
```

## 🔧 Comandos Útiles

```bash
# Crear migraciones
python manage.py makemigrations

# Aplicar migraciones
python manage.py migrate

# Crear superusuario
python manage.py createsuperuser

# Cargar datos iniciales
python manage.py load_initial_data

# Ejecutar servidor
python manage.py runserver

# Acceder al shell
python manage.py shell

# Crear archivo de requisitos
pip freeze > requirements.txt
```

## 🚀 Despliegue en Producción

### 1. Actualizar settings.py
```python
DEBUG = False
ALLOWED_HOSTS = ['tu-dominio.com']
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'kairos_db',
        'USER': 'tu_usuario',
        'PASSWORD': 'tu_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

### 2. Recopilar archivos estáticos
```bash
python manage.py collectstatic
```

### 3. Configurar servidor web (Nginx + Gunicorn)
```bash
pip install gunicorn
gunicorn djangoProject.wsgi:application --bind 0.0.0.0:8000
```

## 📝 Tareas Pendientes

- [ ] Implementar recuperación de contraseña
- [ ] Añadir gráficas interactivas en dashboard
- [ ] Integración con API de MetaTrader 5
- [ ] Sistema de notificaciones en tiempo real
- [ ] Tests unitarios y de integración
- [ ] Documentación de API REST (si se implementa)

## 👤 Autor

**Igor Barredo Arroyo**  
Proyecto Kairos - Gestión de Capital 

## 📄 Licencia

Proyecto privado - Todos los derechos reservados © 2025