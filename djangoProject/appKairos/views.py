from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.db.models import Sum, Q
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.urls import reverse
import secrets
import pyotp
import qrcode
import io
import base64
from datetime import datetime, timedelta

from .models import (
    Usuario, Mercado, Producto, ProductoContratado, 
    Resultado, TokenVerificacionEmail, SesionSeguridad
)
from .forms import (
    RegistroUsuarioForm, LoginForm, VerificarEmailForm,
    Activar2FAForm, Verificar2FAForm, ContactoForm,
    ContratarProductoForm, ActualizarPerfilForm, CambiarPasswordForm
)


# ============================================================================
# VISTAS DE AUTENTICACIÓN
# ============================================================================

def registro_view(request):
    """
    Vista de registro de nuevos usuarios
    Conecta con: register_en.html
    """
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = RegistroUsuarioForm(request.POST)
        if form.is_valid():
            # Crear usuario pero no activarlo aún
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            
            # Generar token de verificación
            token = secrets.token_urlsafe(32)
            TokenVerificacionEmail.objects.create(
                usuario=user,
                token=token,
                expira_en=timezone.now() + timedelta(hours=24)
            )
            
            # Enviar email de verificación
            verification_url = request.build_absolute_uri(
                reverse('verificar_email', kwargs={'token': token})
            )
            
            send_mail(
                subject='Verifica tu cuenta - Proyecto Kairos',
                message=f'''
                Hola {user.first_name or user.username},
                
                Gracias por registrarte en Proyecto Kairos.
                
                Por favor verifica tu email haciendo clic en el siguiente enlace:
                {verification_url}
                
                Este enlace expirará en 24 horas.
                
                Si no creaste esta cuenta, ignora este email.
                
                Saludos,
                Equipo Proyecto Kairos
                ''',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
            
            messages.success(request, 'Cuenta creada exitosamente. Por favor verifica tu email.')
            return redirect('verify_email_sent')
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = RegistroUsuarioForm()
    
    return render(request, 'register_en.html', {'form': form})


def login_view(request):
    """
    Vista de inicio de sesión
    Conecta con: login_en.html
    """
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            recordarme = form.cleaned_data.get('recordarme', False)
            
            # Buscar usuario por email
            try:
                usuario = Usuario.objects.get(email=email)
                user = authenticate(request, username=usuario.username, password=password)
            except Usuario.DoesNotExist:
                user = None
            
            if user is not None:
                # Registrar intento de login exitoso
                SesionSeguridad.objects.create(
                    usuario=user,
                    ip_address=get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    exitoso=True
                )
                
                # Verificar si tiene 2FA activado
                if user.tiene_2fa_activo:
                    # Guardar user_id en sesión para verificación 2FA
                    request.session['pre_2fa_user_id'] = user.id
                    return redirect('verificar_2fa')
                else:
                    # Login directo
                    login(request, user)
                    if not recordarme:
                        request.session.set_expiry(0)
                    messages.success(request, f'Bienvenido de vuelta, {user.first_name or user.username}!')
                    return redirect('dashboard')
            else:
                # Registrar intento fallido
                try:
                    usuario = Usuario.objects.get(email=email)
                    SesionSeguridad.objects.create(
                        usuario=usuario,
                        ip_address=get_client_ip(request),
                        user_agent=request.META.get('HTTP_USER_AGENT', ''),
                        exitoso=False
                    )
                except Usuario.DoesNotExist:
                    pass
                
                messages.error(request, 'Email o contraseña incorrectos.')
    else:
        form = LoginForm()
    
    return render(request, 'login_en.html', {'form': form})


@login_required
def logout_view(request):
    """Vista de cierre de sesión"""
    logout(request)
    messages.success(request, 'Has cerrado sesión exitosamente.')
    return redirect('index')


def verify_email_sent_view(request):
    """
    Vista que muestra mensaje de verificación de email enviado
    Conecta con: verify-email_en.html
    """
    return render(request, 'verify-email_en.html')


def verificar_email_view(request, token):
    """
    Vista para verificar el email del usuario mediante token
    """
    try:
        token_obj = TokenVerificacionEmail.objects.get(
            token=token,
            usado=False,
            expira_en__gt=timezone.now()
        )
        
        # Activar usuario
        usuario = token_obj.usuario
        usuario.is_active = True
        usuario.email_verificado = True
        usuario.save()
        
        # Marcar token como usado
        token_obj.usado = True
        token_obj.save()
        
        messages.success(request, '¡Email verificado exitosamente! Ya puedes iniciar sesión.')
        return redirect('login')
        
    except TokenVerificacionEmail.DoesNotExist:
        messages.error(request, 'Token de verificación inválido o expirado.')
        return redirect('index')


def reenviar_verificacion_view(request):
    """Vista para reenviar email de verificación"""
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            usuario = Usuario.objects.get(email=email, is_active=False)
            
            # Invalidar tokens anteriores
            TokenVerificacionEmail.objects.filter(usuario=usuario, usado=False).update(usado=True)
            
            # Crear nuevo token
            token = secrets.token_urlsafe(32)
            TokenVerificacionEmail.objects.create(
                usuario=usuario,
                token=token,
                expira_en=timezone.now() + timedelta(hours=24)
            )
            
            # Enviar email
            verification_url = request.build_absolute_uri(
                reverse('verificar_email', kwargs={'token': token})
            )
            
            send_mail(
                subject='Verifica tu cuenta - Proyecto Kairos',
                message=f'''
                Hola {usuario.first_name or usuario.username},
                
                Has solicitado un nuevo enlace de verificación.
                
                Por favor verifica tu email haciendo clic en el siguiente enlace:
                {verification_url}
                
                Este enlace expirará en 24 horas.
                
                Saludos,
                Equipo Proyecto Kairos
                ''',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[usuario.email],
                fail_silently=False,
            )
            
            messages.success(request, 'Email de verificación reenviado. Por favor revisa tu bandeja de entrada.')
        except Usuario.DoesNotExist:
            messages.error(request, 'No se encontró una cuenta pendiente de verificación con ese email.')
    
    return redirect('verify_email_sent')


# ============================================================================
# VISTAS DE 2FA (AUTENTICACIÓN DE DOS FACTORES)
# ============================================================================

@login_required
def activar_2fa_view(request):
    """Vista para activar la autenticación de dos factores"""
    usuario = request.user
    
    if usuario.tiene_2fa_activo:
        messages.info(request, 'Ya tienes 2FA activado.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = Activar2FAForm(request.POST)
        if form.is_valid():
            codigo = form.cleaned_data['codigo_verificacion']
            
            # Verificar código
            totp = pyotp.TOTP(usuario.secreto_2fa)
            if totp.verify(codigo, valid_window=1):
                usuario.tiene_2fa_activo = True
                usuario.save()
                messages.success(request, '¡2FA activado exitosamente!')
                return redirect('dashboard')
            else:
                messages.error(request, 'Código incorrecto. Por favor intenta de nuevo.')
    else:
        # Generar secreto 2FA si no existe
        if not usuario.secreto_2fa:
            usuario.secreto_2fa = pyotp.random_base32()
            usuario.save()
        
        form = Activar2FAForm()
        
        # Generar código QR
        totp = pyotp.TOTP(usuario.secreto_2fa)
        provisioning_uri = totp.provisioning_uri(
            name=usuario.email,
            issuer_name='Proyecto Kairos'
        )
        
        # Crear imagen QR
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(provisioning_uri)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convertir a base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()
    
    context = {
        'form': form,
        'qr_code': qr_code_base64,
        'secret_key': usuario.secreto_2fa
    }
    return render(request, 'activar_2fa.html', context)


def verificar_2fa_view(request):
    """Vista para verificar código 2FA durante el login"""
    user_id = request.session.get('pre_2fa_user_id')
    if not user_id:
        return redirect('login')
    
    try:
        usuario = Usuario.objects.get(id=user_id)
    except Usuario.DoesNotExist:
        return redirect('login')
    
    if request.method == 'POST':
        form = Verificar2FAForm(request.POST)
        if form.is_valid():
            codigo = form.cleaned_data['codigo_2fa']
            
            # Verificar código
            totp = pyotp.TOTP(usuario.secreto_2fa)
            if totp.verify(codigo, valid_window=1):
                # Login exitoso
                login(request, usuario)
                del request.session['pre_2fa_user_id']
                messages.success(request, f'Bienvenido de vuelta, {usuario.first_name or usuario.username}!')
                return redirect('dashboard')
            else:
                messages.error(request, 'Código 2FA incorrecto.')
    else:
        form = Verificar2FAForm()
    
    return render(request, 'verificar_2fa.html', {'form': form})


@login_required
def desactivar_2fa_view(request):
    """Vista para desactivar 2FA"""
    if request.method == 'POST':
        usuario = request.user
        usuario.tiene_2fa_activo = False
        usuario.save()
        messages.success(request, '2FA desactivado exitosamente.')
    return redirect('dashboard')


# ============================================================================
# VISTA DEL DASHBOARD
# ============================================================================

@login_required
def dashboard_view(request):
    """
    Vista principal del dashboard del usuario
    Conecta con: dashboard_en.html
    """
    usuario = request.user
    
    # Obtener productos contratados
    productos_contratados = ProductoContratado.objects.filter(
        usuario=usuario
    ).select_related('producto', 'producto__mercado')
    
    # Calcular capital total
    capital_total = productos_contratados.filter(
        estado='activo'
    ).aggregate(
        total=Sum('capital_actual')
    )['total'] or 0
    
    # Actualizar capital total del usuario
    usuario.capital_total = capital_total
    usuario.save()
    
    # Obtener resultados mensuales para gráficas
    resultados = Resultado.objects.filter(
        usuario=usuario
    ).order_by('fecha')
    
    # Preparar datos para gráficas
    fechas = [r.fecha.strftime('%Y-%m') for r in resultados]
    capitales = [float(r.capital_mes) for r in resultados]
    porcentajes = [float(r.porcentaje_cambio) for r in resultados]
    
    # Obtener productos disponibles para contratar
    productos_disponibles = Producto.objects.filter(activo=True)
    
    # Estadísticas del usuario
    total_invertido = productos_contratados.aggregate(
        total=Sum('monto_invertido')
    )['total'] or 0
    
    ganancia_total = capital_total - total_invertido
    porcentaje_ganancia = (ganancia_total / total_invertido * 100) if total_invertido > 0 else 0
    
    context = {
        'usuario': usuario,
        'productos_contratados': productos_contratados,
        'capital_total': capital_total,
        'total_invertido': total_invertido,
        'ganancia_total': ganancia_total,
        'porcentaje_ganancia': porcentaje_ganancia,
        'fechas': fechas,
        'capitales': capitales,
        'porcentajes': porcentajes,
        'productos_disponibles': productos_disponibles,
    }
    
    return render(request, 'dashboard_en.html', context)


# ============================================================================
# VISTAS DE PRODUCTOS
# ============================================================================

@login_required
def contratar_producto_view(request, producto_id):
    """Vista para contratar un producto financiero"""
    producto = get_object_or_404(Producto, id=producto_id, activo=True)
    
    if request.method == 'POST':
        form = ContratarProductoForm(request.POST)
        if form.is_valid():
            contrato = form.save(commit=False)
            contrato.usuario = request.user
            contrato.producto = producto
            contrato.capital_actual = contrato.monto_invertido
            contrato.save()
            
            messages.success(request, f'Producto "{producto.nombre}" contratado exitosamente.')
            return redirect('dashboard')
    else:
        form = ContratarProductoForm(initial={'producto': producto})
    
    context = {
        'form': form,
        'producto': producto
    }
    return render(request, 'contratar_producto.html', context)


@login_required
def cancelar_producto_view(request, contrato_id):
    """Vista para cancelar un producto contratado"""
    contrato = get_object_or_404(ProductoContratado, id=contrato_id, usuario=request.user)
    
    if request.method == 'POST':
        contrato.estado = 'cancelado'
        contrato.fecha_fin = timezone.now()
        contrato.save()
        messages.success(request, 'Producto cancelado exitosamente.')
        return redirect('dashboard')
    
    return render(request, 'cancelar_producto.html', {'contrato': contrato})


# ============================================================================
# VISTAS DE PERFIL
# ============================================================================

@login_required
def perfil_view(request):
    """Vista del perfil del usuario"""
    if request.method == 'POST':
        form = ActualizarPerfilForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Perfil actualizado exitosamente.')
            return redirect('perfil')
    else:
        form = ActualizarPerfilForm(instance=request.user)
    
    return render(request, 'perfil.html', {'form': form})


@login_required
def cambiar_password_view(request):
    """Vista para cambiar la contraseña"""
    if request.method == 'POST':
        form = CambiarPasswordForm(request.POST)
        if form.is_valid():
            password_actual = form.cleaned_data['password_actual']
            password_nueva = form.cleaned_data['password_nueva']
            
            # Verificar contraseña actual
            if request.user.check_password(password_actual):
                request.user.set_password(password_nueva)
                request.user.save()
                
                # Actualizar sesión para no cerrar sesión
                from django.contrib.auth import update_session_auth_hash
                update_session_auth_hash(request, request.user)
                
                messages.success(request, 'Contraseña cambiada exitosamente.')
                return redirect('perfil')
            else:
                messages.error(request, 'Contraseña actual incorrecta.')
    else:
        form = CambiarPasswordForm()
    
    return render(request, 'cambiar_password.html', {'form': form})


# ============================================================================
# VISTAS PÚBLICAS
# ============================================================================

def index_view(request):
    """
    Vista de la página principal
    Conecta con: index_en.html
    """
    # Obtener productos destacados
    productos = Producto.objects.filter(activo=True)[:3]
    
    # Obtener últimos resultados para mostrar en gráfica
    resultados_recientes = Resultado.objects.all().order_by('-fecha')[:12]
    
    context = {
        'productos': productos,
        'resultados': resultados_recientes,
    }
    return render(request, 'index_en.html', context)


def how_we_work_view(request):
    """
    Vista de "Cómo trabajamos"
    Conecta con: howwework.html
    """
    return render(request, 'howwework.html')


def connect_mt5_view(request):
    """
    Vista de instrucciones para conectar MT5
    Conecta con: connect_en.html
    """
    return render(request, 'connect_en.html')


def newsletter_view(request):
    """
    Vista de suscripción al newsletter
    Conecta con: newsletter_en.html
    """
    if request.method == 'POST':
        email = request.POST.get('email')
        if email:
            # Aquí puedes integrar con un servicio de email marketing
            # Por ahora solo guardamos el email
            messages.success(request, '¡Gracias por suscribirte a nuestro newsletter!')
            
            # Enviar email de confirmación
            send_mail(
                subject='Bienvenido al Newsletter de Proyecto Kairos',
                message=f'''
                Hola,
                
                Gracias por suscribirte al newsletter de Igor Barredo Arroyo.
                
                Recibirás contenido exclusivo sobre capitalización de recursos, 
                crecimiento y estrategias de venta.
                
                Saludos,
                Equipo Proyecto Kairos
                ''',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=True,
            )
            
            return JsonResponse({'success': True})
        return JsonResponse({'success': False, 'error': 'Email inválido'})
    
    return render(request, 'newsletter_en.html')


@require_http_methods(["POST"])
def contacto_view(request):
    """Vista para procesar el formulario de contacto"""
    form = ContactoForm(request.POST)
    if form.is_valid():
        nombre = form.cleaned_data['nombre']
        email = form.cleaned_data['email']
        mensaje = form.cleaned_data['mensaje']
        
        # Enviar email al equipo
        send_mail(
            subject=f'Nuevo mensaje de contacto de {nombre}',
            message=f'''
            Nombre: {nombre}
            Email: {email}
            
            Mensaje:
            {mensaje}
            ''',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.CONTACT_EMAIL],
            fail_silently=False,
        )
        
        # Enviar confirmación al usuario
        send_mail(
            subject='Hemos recibido tu mensaje - Proyecto Kairos',
            message=f'''
            Hola {nombre},
            
            Gracias por contactarnos. Hemos recibido tu mensaje y te responderemos 
            lo antes posible.
            
            Saludos,
            Equipo Proyecto Kairos
            ''',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=True,
        )
        
        messages.success(request, 'Mensaje enviado exitosamente. Te responderemos pronto.')
        return redirect('index')
    else:
        messages.error(request, 'Por favor corrige los errores en el formulario.')
        return redirect('index')


# ============================================================================
# FUNCIONES AUXILIARES
# ============================================================================

def get_client_ip(request):
    """Obtiene la IP del cliente"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip