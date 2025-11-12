from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from decimal import Decimal


class Usuario(AbstractUser):
    """
    Modelo de Usuario personalizado que extiende AbstractUser
    Usa email como identificador principal para login
    """
    # Sobrescribir email para hacerlo único y obligatorio
    email = models.EmailField(
        unique=True,
        verbose_name='Email',
        help_text='Email del usuario (usado para login)'
    )
    
    # Campos adicionales de perfil
    telefono = models.CharField(max_length=20, blank=True, null=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    capital_total = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0,
        help_text="Capital total del usuario en euros"
    )
    
    # Campos de seguridad
    email_verificado = models.BooleanField(
        default=False,
        help_text="Indica si el usuario ha verificado su email"
    )
    fecha_verificacion_email = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha en que se verificó el email"
    )
    
    # Campos de autenticación de dos factores (2FA)
    doble_autenticacion_activa = models.BooleanField(
        default=False,
        help_text="Indica si el usuario tiene activada la autenticación de dos factores"
    )
    fecha_activacion_2fa = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha en que se activó 2FA"
    )
    
    # Hacer que el email sea el campo de login
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']  # username será opcional pero requerido por AbstractUser
    
    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
    
    def __str__(self):
        return self.email
    
    def calcular_capital_total(self):
        """Calcula el capital total sumando todos los productos contratados"""
        total = self.productos_contratados.filter(activo=True).aggregate(
            total=models.Sum('monto_invertido')
        )['total'] or Decimal('0')
        self.capital_total = total
        self.save()
        return total


class Mercado(models.Model):
    """
    Modelo para los mercados financieros (XAAUSD, NasdaQ, SP500)
    """
    nombre = models.CharField(max_length=50, unique=True)
    codigo = models.CharField(max_length=20, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    activo = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'Mercado'
        verbose_name_plural = 'Mercados'
    
    def __str__(self):
        return self.nombre


class Producto(models.Model):
    """
    Modelo de Producto financiero
    """
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True, null=True)
    codigo = models.CharField(max_length=50, unique=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(default=True)
    
    # Mercados en los que opera este producto
    mercados = models.ManyToManyField(
        Mercado,
        related_name='productos',
        help_text="Mercados en los que opera este producto"
    )
    
    class Meta:
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
        ordering = ['nombre']
    
    def __str__(self):
        return self.nombre


class ProductoContratado(models.Model):
    """
    Modelo para productos contratados por usuarios
    Representa la relación entre Usuario y Producto con datos específicos de la contratación
    """
    ESTADO_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('pending', 'Pending'),
    ]
    
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='productos_contratados'
    )
    producto = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE,
        related_name='contrataciones'
    )
    monto_invertido = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        help_text="Monto invertido en euros"
    )
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='active'
    )
    fecha_contratacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    activo = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'Producto Contratado'
        verbose_name_plural = 'Productos Contratados'
        unique_together = ('usuario', 'producto')
    
    def __str__(self):
        return f"{self.usuario.email} - {self.producto.nombre} (€{self.monto_invertido})"


class Resultado(models.Model):
    """
    Modelo de Resultado mensual del usuario
    Almacena el historial de capital para generar gráficas
    """
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='resultados'
    )
    producto_contratado = models.ForeignKey(
        ProductoContratado,
        on_delete=models.CASCADE,
        related_name='resultados',
        null=True,
        blank=True,
        help_text="Producto específico al que corresponde este resultado"
    )
    mes = models.CharField(max_length=20, help_text="Ej: Enero, Febrero, etc.")
    anio = models.IntegerField()
    capital = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        help_text="Capital en ese mes en euros"
    )
    cambio_mensual = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        default=0,
        help_text="Cambio respecto al mes anterior en euros"
    )
    porcentaje_cambio = models.DecimalField(
        max_digits=6, 
        decimal_places=2,
        default=0,
        help_text="Porcentaje de cambio respecto al mes anterior"
    )
    fecha_registro = models.DateTimeField(auto_now_add=True)
    observaciones = models.TextField(blank=True, null=True)
    
    class Meta:
        verbose_name = 'Resultado'
        verbose_name_plural = 'Resultados'
        ordering = ['anio', 'mes']
        unique_together = ('usuario', 'producto_contratado', 'mes', 'anio')
    
    def __str__(self):
        if self.producto_contratado:
            return f"{self.usuario.email} - {self.producto_contratado.producto.nombre} - {self.mes} {self.anio}"
        return f"{self.usuario.email} - Total - {self.mes} {self.anio}"
    
    def calcular_cambios(self, capital_anterior):
        """Calcula el cambio mensual y porcentaje"""
        if capital_anterior and capital_anterior > 0:
            self.cambio_mensual = self.capital - capital_anterior
            self.porcentaje_cambio = (self.cambio_mensual / capital_anterior) * 100
        else:
            self.cambio_mensual = 0
            self.porcentaje_cambio = 0


class TokenVerificacionEmail(models.Model):
    """
    Modelo para tokens de verificación de email
    """
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='tokens_verificacion'
    )
    token = models.CharField(max_length=100, unique=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_expiracion = models.DateTimeField()
    usado = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = 'Token de Verificación'
        verbose_name_plural = 'Tokens de Verificación'
    
    def __str__(self):
        return f"Token para {self.usuario.email}"
    
    def esta_expirado(self):
        """Verifica si el token ha expirado"""
        return timezone.now() > self.fecha_expiracion


class SesionSeguridad(models.Model):
    """
    Modelo para registrar intentos de login y actividad de seguridad
    """
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='sesiones_seguridad',
        null=True,
        blank=True
    )
    email_intento = models.EmailField(help_text="Email usado en el intento de login")
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True, null=True)
    exitoso = models.BooleanField(default=False)
    requirio_2fa = models.BooleanField(default=False)
    fecha_intento = models.DateTimeField(auto_now_add=True)
    motivo_fallo = models.CharField(max_length=200, blank=True, null=True)
    
    class Meta:
        verbose_name = 'Sesión de Seguridad'
        verbose_name_plural = 'Sesiones de Seguridad'
        ordering = ['-fecha_intento']
    
    def __str__(self):
        estado = "Exitoso" if self.exitoso else "Fallido"
        return f"{self.email_intento} - {estado} - {self.fecha_intento}"