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
    Resultado, TokenVerificacionEmail, TokenRecuperacionPassword, SesionSeguridad
)
from .forms import (
    RegistroUsuarioForm, LoginForm, VerificarEmailForm,
    Activar2FAForm, Verificar2FAForm, ContactoForm,
    ContratarProductoForm, ActualizarPerfilForm, CambiarPasswordForm,
    SolicitarRecuperacionPasswordForm, ResetPasswordForm, Desactivar2FAForm
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
        return redirect('appKairos:dashboard')
    
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
                reverse('appKairos:verificar_email', kwargs={'token': token})
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
            return redirect('appKairos:verify_email_sent')
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
        return redirect('appKairos:dashboard')
    
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
                    request.session['pre_2fa_timestamp'] = timezone.now().timestamp()
                    request.session['intentos_2fa'] = 0
                    return redirect('appKairos:verificar_2fa')
                else:
                    # Login directo
                    login(request, user)
                    if not recordarme:
                        request.session.set_expiry(0)
                    messages.success(request, f'Bienvenido de vuelta, {user.first_name or user.username}!')
                    return redirect('appKairos:dashboard')
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
            # Si el formulario no es válido, mostrar mensaje de error
            messages.error(request, 'Email o contraseña incorrectos.')
    else:
        form = LoginForm()
    
    return render(request, 'login_en.html', {'form': form})


@login_required
def logout_view(request):
    """Vista de cierre de sesión"""
    logout(request)
    messages.success(request, 'Has cerrado sesión exitosamente.')
    return redirect('appKairos:index')


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
        usuario.fecha_verificacion_email = timezone.now()
        usuario.save()
        
        # Marcar token como usado
        token_obj.usado = True
        token_obj.save()
        
        messages.success(request, '¡Email verificado exitosamente! Ya puedes iniciar sesión.')
        return redirect('appKairos:login')
        
    except TokenVerificacionEmail.DoesNotExist:
        messages.error(request, 'Token de verificación inválido o expirado.')
        return redirect('appKairos:index')


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
                reverse('appKairos:verificar_email', kwargs={'token': token})
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
    
    return redirect('appKairos:verify_email_sent')


# ============================================================================
# VISTAS DE RECUPERACIÓN DE CONTRASEÑA
# ============================================================================

def solicitar_recuperacion_view(request):
    """Vista para solicitar recuperación de contraseña"""
    if request.user.is_authenticated:
        return redirect('appKairos:dashboard')
    
    if request.method == 'POST':
        form = SolicitarRecuperacionPasswordForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                usuario = Usuario.objects.get(email=email, is_active=True)
                
                # Invalidar tokens anteriores
                TokenRecuperacionPassword.objects.filter(
                    usuario=usuario, 
                    usado=False
                ).update(usado=True)
                
                # Crear nuevo token
                token = secrets.token_urlsafe(32)
                TokenRecuperacionPassword.objects.create(
                    usuario=usuario,
                    token=token,
                    expira_en=timezone.now() + timedelta(hours=1)
                )
                
                # Enviar email
                reset_url = request.build_absolute_uri(
                    reverse('appKairos:reset_password', kwargs={'token': token})
                )
                
                send_mail(
                    subject='Recuperación de Contraseña - Proyecto Kairos',
                    message=f'''
                    Hola {usuario.first_name or usuario.username},
                    
                    Has solicitado restablecer tu contraseña.
                    
                    Por favor haz clic en el siguiente enlace para crear una nueva contraseña:
                    {reset_url}
                    
                    Este enlace expirará en 1 hora.
                    
                    Si no solicitaste este cambio, ignora este email y tu contraseña permanecerá sin cambios.
                    
                    Saludos,
                    Equipo Proyecto Kairos
                    ''',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[usuario.email],
                    fail_silently=False,
                )
                
                messages.success(request, 'Se ha enviado un enlace de recuperación a tu email.')
                return redirect('appKairos:recuperacion_enviada')
                
            except Usuario.DoesNotExist:
                # Por seguridad, no revelar si el email existe o no
                messages.success(request, 'Si el email existe en nuestro sistema, recibirás un enlace de recuperación.')
                return redirect('appKairos:recuperacion_enviada')
    else:
        form = SolicitarRecuperacionPasswordForm()
    
    return render(request, 'solicitar_recuperacion.html', {'form': form})


def recuperacion_enviada_view(request):
    """Vista que confirma el envío del email de recuperación"""
    return render(request, 'recuperacion_enviada.html')


def reset_password_view(request, token):
    """Vista para restablecer la contraseña con token"""
    try:
        token_obj = TokenRecuperacionPassword.objects.get(
            token=token,
            usado=False,
            expira_en__gt=timezone.now()
        )
        usuario = token_obj.usuario
        
        if request.method == 'POST':
            form = ResetPasswordForm(request.POST)
            if form.is_valid():
                nueva_password = form.cleaned_data['password_nueva']
                
                # Cambiar contraseña
                usuario.set_password(nueva_password)
                usuario.save()
                
                # Marcar token como usado
                token_obj.usado = True
                token_obj.save()
                
                messages.success(request, 'Contraseña restablecida exitosamente. Ya puedes iniciar sesión.')
                return redirect('appKairos:login')
        else:
            form = ResetPasswordForm()
        
        return render(request, 'reset_password.html', {
            'form': form,
            'token': token
        })
        
    except TokenRecuperacionPassword.DoesNotExist:
        messages.error(request, 'El enlace de recuperación es inválido o ha expirado.')
        return redirect('appKairos:solicitar_recuperacion')


# ============================================================================
# VISTAS DE 2FA (AUTENTICACIÓN DE DOS FACTORES)
# ============================================================================

@login_required
def activar_2fa_view(request):
    """Vista para activar la autenticación de dos factores"""
    usuario = request.user
    
    if usuario.tiene_2fa_activo:
        messages.info(request, 'Ya tienes 2FA activado.')
        return redirect('appKairos:perfil')
    
    if request.method == 'POST':
        form = Activar2FAForm(request.POST)
        if form.is_valid():
            codigo = form.cleaned_data['codigo_verificacion']
            
            # Verificar código
            totp = pyotp.TOTP(usuario.secreto_2fa)
            if totp.verify(codigo, valid_window=1):
                # Generar códigos de respaldo
                codigos_respaldo = Usuario.generar_codigos_respaldo()
                
                # Guardar códigos encriptados (separados por comas)
                from django.contrib.auth.hashers import make_password
                codigos_encriptados = [make_password(codigo) for codigo in codigos_respaldo]
                usuario.codigos_respaldo_2fa = ','.join(codigos_encriptados)
                
                # Activar 2FA
                usuario.tiene_2fa_activo = True
                usuario.fecha_activacion_2fa = timezone.now()
                usuario.save()
                
                # Guardar códigos en sesión para mostrarlos
                request.session['codigos_respaldo_2fa'] = codigos_respaldo
                
                messages.success(request, '¡2FA activado exitosamente!')
                return redirect('appKairos:mostrar_codigos_respaldo')
            else:
                qr_code_base64 = None
                messages.error(request, 'Código incorrecto. Por favor intenta de nuevo.')
    else:
        qr_code_base64 = None
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


@login_required
def mostrar_codigos_respaldo_view(request):
    """Vista para mostrar los códigos de respaldo 2FA"""
    codigos = request.session.get('codigos_respaldo_2fa')
    
    if not codigos:
        messages.warning(request, 'No hay códigos de respaldo para mostrar.')
        return redirect('appKairos:dashboard')
    
    if request.method == 'POST':
        # Usuario confirmó que guardó los códigos
        del request.session['codigos_respaldo_2fa']
        messages.info(request, 'Recuerda guardar tus códigos de respaldo en un lugar seguro.')
        return redirect('appKairos:dashboard')
    
    return render(request, 'codigos_respaldo_2fa.html', {'codigos': codigos})


def verificar_2fa_view(request):
    """Vista mejorada para verificar código 2FA durante el login"""
    user_id = request.session.get('pre_2fa_user_id')
    timestamp = request.session.get('pre_2fa_timestamp')
    
    # Verificar timeout (5 minutos)
    if not user_id or not timestamp:
        messages.error(request, 'Sesión expirada. Por favor inicia sesión nuevamente.')
        return redirect('appKairos:login')
    
    if timezone.now().timestamp() - timestamp > 300:  # 5 minutos
        del request.session['pre_2fa_user_id']
        del request.session['pre_2fa_timestamp']
        messages.error(request, 'Tiempo de verificación expirado. Inicia sesión nuevamente.')
        return redirect('appKairos:login')
    
    try:
        usuario = Usuario.objects.get(id=user_id)
    except Usuario.DoesNotExist:
        return redirect('appKairos:login')
    
    # Verificar intentos fallidos
    intentos = request.session.get('intentos_2fa', 0)
    if intentos >= 3:
        del request.session['pre_2fa_user_id']
        messages.error(request, 'Demasiados intentos fallidos. Por favor inicia sesión nuevamente.')
        return redirect('appKairos:login')
    
    if request.method == 'POST':
        form = Verificar2FAForm(request.POST)
        if form.is_valid():
            codigo_2fa = form.cleaned_data.get('codigo_2fa')
            codigo_respaldo = form.cleaned_data.get('codigo_respaldo')
            
            verificacion_exitosa = False
            
            # Verificar código TOTP
            if codigo_2fa:
                totp = pyotp.TOTP(usuario.secreto_2fa)
                if totp.verify(codigo_2fa, valid_window=1):
                    verificacion_exitosa = True
            
            # Verificar código de respaldo
            elif codigo_respaldo and usuario.codigos_respaldo_2fa:
                from django.contrib.auth.hashers import check_password
                codigos_encriptados = usuario.codigos_respaldo_2fa.split(',')
                
                for idx, codigo_encriptado in enumerate(codigos_encriptados):
                    if check_password(codigo_respaldo, codigo_encriptado):
                        # Código de respaldo válido - eliminarlo
                        codigos_encriptados.pop(idx)
                        usuario.codigos_respaldo_2fa = ','.join(codigos_encriptados)
                        usuario.save()
                        verificacion_exitosa = True
                        messages.info(request, 'Has usado un código de respaldo. Te quedan {} códigos.'.format(len(codigos_encriptados)))
                        break
            
            if verificacion_exitosa:
                # Login exitoso - especificar backend explícitamente
                from django.contrib.auth import get_backends
                backend = get_backends()[0]
                usuario.backend = f'{backend.__module__}.{backend.__class__.__name__}'
                login(request, usuario, backend=usuario.backend)
                
                # Limpiar sesión temporal
                del request.session['pre_2fa_user_id']
                del request.session['pre_2fa_timestamp']
                if 'intentos_2fa' in request.session:
                    del request.session['intentos_2fa']
                
                # Registrar sesión exitosa
                SesionSeguridad.objects.create(
                    usuario=usuario,
                    ip_address=get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    exitoso=True,
                    requirio_2fa=True
                )
                
                messages.success(request, f'Bienvenido de vuelta, {usuario.first_name or usuario.username}!')
                return redirect('appKairos:dashboard')
            else:
                qr_code_base64 = None
                # Incrementar intentos fallidos
                request.session['intentos_2fa'] = intentos + 1
                
                # Registrar intento fallido
                SesionSeguridad.objects.create(
                    usuario=usuario,
                    ip_address=get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    exitoso=False,
                    requirio_2fa=True,
                    motivo_fallo='Código 2FA incorrecto'
                )
                
                messages.error(request, f'Código incorrecto. Intentos restantes: {3 - intentos - 1}')
    else:
        qr_code_base64 = None
        form = Verificar2FAForm()
    
    return render(request, 'verificar_2fa.html', {
        'form': form,
        'intentos_restantes': 3 - intentos
    })


@login_required
def desactivar_2fa_view(request):
    """Vista mejorada para desactivar 2FA con verificación de contraseña"""
    usuario = request.user
    
    if not usuario.tiene_2fa_activo:
        messages.info(request, 'No tienes 2FA activado.')
        return redirect('appKairos:perfil')
    
    if request.method == 'POST':
        form = Desactivar2FAForm(request.POST)
        if form.is_valid():
            password = form.cleaned_data['password']
            
            # Verificar contraseña
            if usuario.check_password(password):
                # Desactivar 2FA
                usuario.tiene_2fa_activo = False
                usuario.secreto_2fa = None
                usuario.codigos_respaldo_2fa = None
                usuario.fecha_activacion_2fa = None
                usuario.save()
                
                messages.success(request, '2FA desactivado exitosamente.')
                return redirect('appKairos:perfil')
            else:
                qr_code_base64 = None
                messages.error(request, 'Contraseña incorrecta.')
    else:
        qr_code_base64 = None
        form = Desactivar2FAForm()
    
    return render(request, 'desactivar_2fa.html', {'form': form})


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
    ).select_related('producto').prefetch_related('producto__mercados')
    
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
    productos_disponibles = Producto.objects.filter(activo=True).exclude(
        id__in=productos_contratados.values_list('producto_id', flat=True)
    )
    
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
            return redirect('appKairos:dashboard')
    else:
        qr_code_base64 = None
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
        return redirect('appKairos:dashboard')
    
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
            return redirect('appKairos:perfil')
    else:
        qr_code_base64 = None
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
                return redirect('appKairos:perfil')
            else:
                qr_code_base64 = None
                messages.error(request, 'Contraseña actual incorrecta.')
    else:
        qr_code_base64 = None
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
        return redirect('appKairos:index')
    else:
        qr_code_base64 = None
        messages.error(request, 'Por favor corrige los errores en el formulario.')
        return redirect('appKairos:index')


def questions_view(request):
    """
    Vista de preguntas frecuentes (FAQ)
    Conecta con: questions_en.html
    """
    return render(request, 'questions_en.html')


# ============================================================================
# FUNCIONES AUXILIARES
# ============================================================================

def get_client_ip(request):
    """Obtiene la IP del cliente"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        qr_code_base64 = None
        ip = request.META.get('REMOTE_ADDR')
    return ip