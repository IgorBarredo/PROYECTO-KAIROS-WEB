# 📦 Guía de Instalación - Proyecto Kairos

## 🔧 Requisitos Previos

- Python 3.8 o superior
- pip (gestor de paquetes de Python)
- Virtualenv (recomendado)

## 📋 Pasos de Instalación

### 1. Clonar el Repositorio

```bash
git clone <url-del-repositorio>
cd djangoProject
```

### 2. Crear Entorno Virtual

```bash
python -m venv venv

# En Windows:
venv\Scripts\activate

# En Linux/Mac:
source venv/bin/activate
```

### 3. Instalar Dependencias

```bash
pip install -r requirements.TXT
```

**Nota:** Si `python-decouple` no está instalado, ejecuta:
```bash
pip install python-decouple
```

### 4. Configurar Variables de Entorno

Copia el archivo `.env.example` a `.env`:

```bash
cp .env.example .env
```

Edita `.env` y configura las variables necesarias:

```env
SECRET_KEY=tu-secret-key-aqui-generada-con-secrets
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

**Generar SECRET_KEY segura:**
```python
import secrets
print(secrets.token_urlsafe(50))
```

### 5. Crear Base de Datos

```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Cargar Datos Iniciales

```bash
python manage.py load_initial_data
```

Este comando carga:
- Mercados financieros (XAUUSD, NASDAQ, S&P 500)
- Productos (M.P.T MarketProThief, GoldenRoad, MultiMarkets)

### 7. Crear Superusuario

```bash
python manage.py createsuperuser
```

Sigue las instrucciones para crear tu cuenta de administrador.

### 8. Ejecutar Servidor de Desarrollo

```bash
python manage.py runserver
```

Accede a: `http://127.0.0.1:8000/`

## 🔐 Configuración de Email (Opcional)

### Para Desarrollo (Por Defecto)
Los emails se muestran en la consola. No requiere configuración adicional.

### Para Producción (Gmail)

1. Habilita "Verificación en 2 pasos" en tu cuenta de Gmail
2. Genera una "Contraseña de aplicación" en: https://myaccount.google.com/apppasswords
3. Configura en `.env`:

```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=tu_email@gmail.com
EMAIL_HOST_PASSWORD=tu_app_password_generada
```

## 🗂️ Estructura del Proyecto

```
djangoProject/
├── appKairos/              # Aplicación principal
│   ├── management/         # Comandos personalizados
│   ├── migrations/         # Migraciones de base de datos
│   ├── static/            # Archivos estáticos (CSS, JS, imágenes)
│   ├── templates/         # Templates HTML
│   ├── admin.py           # Configuración del admin
│   ├── backends.py        # Backend de autenticación personalizado
│   ├── forms.py           # Formularios
│   ├── models.py          # Modelos de datos
│   ├── urls.py            # URLs de la app
│   └── views.py           # Vistas
├── djangoProject/         # Configuración del proyecto
│   ├── settings.py        # Configuración principal
│   ├── urls.py            # URLs principales
│   └── wsgi.py            # WSGI config
├── logs/                  # Logs del sistema
├── .env                   # Variables de entorno (NO subir a git)
├── .env.example           # Ejemplo de variables de entorno
├── .gitignore            # Archivos ignorados por git
├── db.sqlite3            # Base de datos SQLite
├── manage.py             # Script de gestión de Django
├── requirements.TXT      # Dependencias del proyecto
└── README.md             # Documentación principal
```

## ✅ Verificar Instalación

### 1. Acceder al Admin
- URL: `http://127.0.0.1:8000/admin/`
- Usuario: El que creaste con `createsuperuser`

### 2. Verificar Funcionalidades
- ✅ Registro de usuario
- ✅ Login con email
- ✅ Verificación de email (revisa la consola)
- ✅ Activación de 2FA
- ✅ Dashboard de usuario
- ✅ Contratación de productos

## 🐛 Solución de Problemas

### Error: "No module named 'decouple'"
```bash
pip install python-decouple
```

### Error: "No module named 'pyotp'"
```bash
pip install pyotp qrcode[pil]
```

### Error: "Table doesn't exist"
```bash
python manage.py migrate
```

### Error: "SECRET_KEY not found"
Asegúrate de tener el archivo `.env` con `SECRET_KEY` configurado.

### Los emails no se envían
- En desarrollo: Revisa la consola donde ejecutaste `runserver`
- En producción: Verifica la configuración SMTP en `.env`

## 📊 Comandos Útiles

```bash
# Ver migraciones pendientes
python manage.py showmigrations

# Crear nueva migración
python manage.py makemigrations

# Aplicar migraciones
python manage.py migrate

# Abrir shell de Django
python manage.py shell

# Recolectar archivos estáticos (producción)
python manage.py collectstatic

# Crear superusuario
python manage.py createsuperuser

# Cargar datos iniciales
python manage.py load_initial_data
```

## 🚀 Despliegue en Producción

Ver documentación en `README.md` sección "Despliegue en Producción".

## 📞 Soporte

Para problemas o dudas:
1. Revisa la documentación en `README.md`
2. Consulta los logs en `logs/django.log`
3. Revisa el código en GitHub

---

**Última actualización:** 2025-01-14
**Versión de Django:** 4.2.26