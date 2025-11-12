from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.utils import timezone
from .models import (
    Usuario, Mercado, Producto, ProductoContratado, 
    Resultado, TokenVerificacionEmail, SesionSeguridad
)


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    """
    Administración personalizada para el modelo Usuario
    """
    list_display = [
        'email', 'username', 'capital_total', 'email_verificado', 
        'doble_autenticacion_activa', 'is_active', 'fecha_registro'
    ]
    list_filter = [
        'email_verificado', 'doble_autenticacion_activa', 
        'is_active', 'is_staff', 'fecha_registro'
    ]
    search_fields = ['email', 'username', 'telefono']
    ordering = ['-fecha_registro']
    
    fieldsets = (
        ('Información de Acceso', {
            'fields': ('email', 'username', 'password')
        }),
        ('Información Personal', {
            'fields': ('first_name', 'last_name', 'telefono')
        }),
        ('Información Financiera', {
            'fields': ('capital_total',)
        }),
        ('Seguridad', {
            'fields': (
                'email_verificado', 'fecha_verificacion_email',
                'doble_autenticacion_activa', 'fecha_activacion_2fa'
            )
        }),
        ('Permisos', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Fechas Importantes', {
            'fields': ('last_login', 'fecha_registro')
        }),
    )
    
    readonly_fields = ['fecha_registro', 'last_login', 'fecha_verificacion_email', 'fecha_activacion_2fa']
    
    actions = ['recalcular_capital_total', 'verificar_email', 'activar_usuarios', 'desactivar_usuarios']
    
    def recalcular_capital_total(self, request, queryset):
        """Acción para recalcular el capital total de usuarios seleccionados"""
        count = 0
        for usuario in queryset:
            usuario.calcular_capital_total()
            count += 1
        self.message_user(request, f'Capital recalculado para {count} usuario(s).')
    recalcular_capital_total.short_description = "Recalcular capital total"
    
    def verificar_email(self, request, queryset):
        """Acción para marcar emails como verificados"""
        count = queryset.update(
            email_verificado=True,
            fecha_verificacion_email=timezone.now()
        )
        self.message_user(request, f'{count} email(s) verificado(s).')
    verificar_email.short_description = "Marcar email como verificado"
    
    def activar_usuarios(self, request, queryset):
        """Acción para activar usuarios"""
        count = queryset.update(is_active=True)
        self.message_user(request, f'{count} usuario(s) activado(s).')
    activar_usuarios.short_description = "Activar usuarios seleccionados"
    
    def desactivar_usuarios(self, request, queryset):
        """Acción para desactivar usuarios"""
        count = queryset.update(is_active=False)
        self.message_user(request, f'{count} usuario(s) desactivado(s).')
    desactivar_usuarios.short_description = "Desactivar usuarios seleccionados"


@admin.register(Mercado)
class MercadoAdmin(admin.ModelAdmin):
    """
    Administración para el modelo Mercado
    """
    list_display = ['nombre', 'codigo', 'activo', 'cantidad_productos']
    list_filter = ['activo']
    search_fields = ['nombre', 'codigo']
    ordering = ['nombre']
    
    def cantidad_productos(self, obj):
        """Muestra la cantidad de productos que operan en este mercado"""
        count = obj.productos.count()
        return format_html('<strong>{}</strong> producto(s)', count)
    cantidad_productos.short_description = 'Productos'


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    """
    Administración para el modelo Producto
    """
    list_display = ['nombre', 'codigo', 'mostrar_mercados', 'activo', 'fecha_creacion', 'cantidad_contrataciones']
    list_filter = ['activo', 'mercados', 'fecha_creacion']
    search_fields = ['nombre', 'codigo', 'descripcion']
    filter_horizontal = ['mercados']
    ordering = ['nombre']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', 'codigo', 'descripcion', 'activo')
        }),
        ('Mercados', {
            'fields': ('mercados',)
        }),
        ('Información Adicional', {
            'fields': ('fecha_creacion',)
        }),
    )
    
    readonly_fields = ['fecha_creacion']
    
    def mostrar_mercados(self, obj):
        """Muestra los mercados en los que opera el producto"""
        mercados = obj.mercados.all()
        if mercados:
            return ', '.join([m.codigo for m in mercados])
        return '-'
    mostrar_mercados.short_description = 'Mercados'
    
    def cantidad_contrataciones(self, obj):
        """Muestra cuántos usuarios han contratado este producto"""
        count = obj.contrataciones.filter(activo=True).count()
        return format_html('<strong>{}</strong> contratación(es)', count)
    cantidad_contrataciones.short_description = 'Contrataciones Activas'


@admin.register(ProductoContratado)
class ProductoContratadoAdmin(admin.ModelAdmin):
    """
    Administración para el modelo ProductoContratado
    """
    list_display = [
        'usuario', 'producto', 'monto_invertido_formato', 
        'estado_badge', 'activo', 'fecha_contratacion'
    ]
    list_filter = ['estado', 'activo', 'fecha_contratacion', 'producto']
    search_fields = ['usuario__email', 'usuario__username', 'producto__nombre']
    ordering = ['-fecha_contratacion']
    
    fieldsets = (
        ('Información de Contratación', {
            'fields': ('usuario', 'producto', 'monto_invertido', 'estado', 'activo')
        }),
        ('Fechas', {
            'fields': ('fecha_contratacion', 'fecha_actualizacion')
        }),
    )
    
    readonly_fields = ['fecha_contratacion', 'fecha_actualizacion']
    
    actions = ['activar_productos', 'desactivar_productos', 'marcar_como_activo']
    
    def monto_invertido_formato(self, obj):
        """Formatea el monto invertido con símbolo de euro"""
        return format_html('€ <strong>{:,.2f}</strong>', obj.monto_invertido)
    monto_invertido_formato.short_description = 'Monto Invertido'
    
    def estado_badge(self, obj):
        """Muestra el estado con colores"""
        colors = {
            'active': 'green',
            'inactive': 'red',
            'pending': 'orange'
        }
        color = colors.get(obj.estado, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color, obj.get_estado_display()
        )
    estado_badge.short_description = 'Estado'
    
    def activar_productos(self, request, queryset):
        """Acción para activar productos contratados"""
        count = queryset.update(activo=True, estado='active')
        self.message_user(request, f'{count} producto(s) activado(s).')
    activar_productos.short_description = "Activar productos seleccionados"
    
    def desactivar_productos(self, request, queryset):
        """Acción para desactivar productos contratados"""
        count = queryset.update(activo=False, estado='inactive')
        self.message_user(request, f'{count} producto(s) desactivado(s).')
    desactivar_productos.short_description = "Desactivar productos seleccionados"
    
    def marcar_como_activo(self, request, queryset):
        """Acción para marcar estado como activo"""
        count = queryset.update(estado='active')
        self.message_user(request, f'{count} producto(s) marcado(s) como activo.')
    marcar_como_activo.short_description = "Marcar como Active"


@admin.register(Resultado)
class ResultadoAdmin(admin.ModelAdmin):
    """
    Administración para el modelo Resultado
    """
    list_display = [
        'usuario', 'producto_info', 'mes', 'anio', 
        'capital_formato', 'cambio_formato', 'porcentaje_formato', 'fecha_registro'
    ]
    list_filter = ['anio', 'mes', 'fecha_registro', 'producto_contratado__producto']
    search_fields = ['usuario__email', 'usuario__username', 'producto_contratado__producto__nombre']
    ordering = ['-anio', '-fecha_registro']
    
    fieldsets = (
        ('Usuario y Producto', {
            'fields': ('usuario', 'producto_contratado')
        }),
        ('Período', {
            'fields': ('mes', 'anio')
        }),
        ('Resultados Financieros', {
            'fields': ('capital', 'cambio_mensual', 'porcentaje_cambio')
        }),
        ('Información Adicional', {
            'fields': ('observaciones', 'fecha_registro')
        }),
    )
    
    readonly_fields = ['fecha_registro']
    
    def producto_info(self, obj):
        """Muestra información del producto"""
        if obj.producto_contratado:
            return obj.producto_contratado.producto.nombre
        return 'Total General'
    producto_info.short_description = 'Producto'
    
    def capital_formato(self, obj):
        """Formatea el capital con símbolo de euro"""
        return format_html('€ <strong>{:,.2f}</strong>', obj.capital)
    capital_formato.short_description = 'Capital'
    
    def cambio_formato(self, obj):
        """Formatea el cambio mensual con color según sea positivo o negativo"""
        color = 'green' if obj.cambio_mensual >= 0 else 'red'
        signo = '+' if obj.cambio_mensual >= 0 else ''
        return format_html(
            '<span style="color: {};">{} € {:,.2f}</span>',
            color, signo, obj.cambio_mensual
        )
    cambio_formato.short_description = 'Cambio Mensual'
    
    def porcentaje_formato(self, obj):
        """Formatea el porcentaje con color según sea positivo o negativo"""
        color = 'green' if obj.porcentaje_cambio >= 0 else 'red'
        signo = '+' if obj.porcentaje_cambio >= 0 else ''
        return format_html(
            '<span style="color: {};">{} {:.2f}%</span>',
            color, signo, obj.porcentaje_cambio
        )
    porcentaje_formato.short_description = 'Porcentaje'


@admin.register(TokenVerificacionEmail)
class TokenVerificacionEmailAdmin(admin.ModelAdmin):
    """
    Administración para tokens de verificación de email
    """
    list_display = ['usuario', 'token_corto', 'fecha_creacion', 'fecha_expiracion', 'usado', 'estado_token']
    list_filter = ['usado', 'fecha_creacion', 'fecha_expiracion']
    search_fields = ['usuario__email', 'token']
    ordering = ['-fecha_creacion']
    readonly_fields = ['fecha_creacion']
    
    def token_corto(self, obj):
        """Muestra solo los primeros caracteres del token"""
        return f"{obj.token[:20]}..."
    token_corto.short_description = 'Token'
    
    def estado_token(self, obj):
        """Muestra el estado del token con colores"""
        if obj.usado:
            return format_html('<span style="color: gray;">Usado</span>')
        elif obj.esta_expirado():
            return format_html('<span style="color: red;">Expirado</span>')
        else:
            return format_html('<span style="color: green;">Válido</span>')
    estado_token.short_description = 'Estado'


@admin.register(SesionSeguridad)
class SesionSeguridadAdmin(admin.ModelAdmin):
    """
    Administración para sesiones de seguridad
    """
    list_display = [
        'email_intento', 'usuario', 'ip_address', 
        'estado_badge', 'requirio_2fa', 'fecha_intento'
    ]
    list_filter = ['exitoso', 'requirio_2fa', 'fecha_intento']
    search_fields = ['email_intento', 'usuario__email', 'ip_address']
    ordering = ['-fecha_intento']
    readonly_fields = ['fecha_intento']
    
    fieldsets = (
        ('Información del Intento', {
            'fields': ('usuario', 'email_intento', 'exitoso', 'motivo_fallo')
        }),
        ('Seguridad', {
            'fields': ('requirio_2fa', 'ip_address', 'user_agent')
        }),
        ('Fecha', {
            'fields': ('fecha_intento',)
        }),
    )
    
    def estado_badge(self, obj):
        """Muestra el estado del intento con colores"""
        if obj.exitoso:
            return format_html('<span style="background-color: green; color: white; padding: 3px 10px; border-radius: 3px;">Exitoso</span>')
        else:
            return format_html('<span style="background-color: red; color: white; padding: 3px 10px; border-radius: 3px;">Fallido</span>')
    estado_badge.short_description = 'Estado'
    
    def has_add_permission(self, request):
        """No permitir agregar sesiones manualmente"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """No permitir editar sesiones"""
        return False