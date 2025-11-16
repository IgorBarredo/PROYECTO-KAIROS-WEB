"""
Tests para los modelos de la aplicación appKairos
"""
from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import timedelta
import secrets

from appKairos.models import (
    Usuario, Mercado, Producto, ProductoContratado,
    Resultado, TokenVerificacionEmail, TokenRecuperacionPassword,
    SesionSeguridad
)


class UsuarioModelTest(TestCase):
    """Tests para el modelo Usuario"""
    
    def setUp(self):
        """Configuración inicial para los tests"""
        self.usuario = Usuario.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!',
            first_name='Test',
            last_name='User'
        )
    
    def test_crear_usuario(self):
        """Test de creación de usuario"""
        self.assertEqual(self.usuario.email, 'test@example.com')
        self.assertEqual(self.usuario.username, 'testuser')
        self.assertTrue(self.usuario.check_password('TestPass123!'))
        self.assertFalse(self.usuario.email_verificado)
        self.assertFalse(self.usuario.tiene_2fa_activo)
    
    def test_email_unico(self):
        """Test que el email debe ser único"""
        with self.assertRaises(Exception):
            Usuario.objects.create_user(
                username='testuser2',
                email='test@example.com',  # Email duplicado
                password='TestPass123!'
            )
    
    def test_str_method(self):
        """Test del método __str__"""
        self.assertEqual(str(self.usuario), 'test@example.com')
    
    def test_calcular_capital_total(self):
        """Test de cálculo de capital total"""
        # Crear producto y contratación
        mercado = Mercado.objects.create(nombre='XAUUSD', codigo='XAUUSD')
        producto = Producto.objects.create(
            nombre='Producto Test',
            codigo='PROD001'
        )
        producto.mercados.add(mercado)
        
        ProductoContratado.objects.create(
            usuario=self.usuario,
            producto=producto,
            monto_invertido=Decimal('1000.00'),
            capital_actual=Decimal('1200.00'),
            estado='activo'
        )
        
        capital = self.usuario.calcular_capital_total()
        self.assertEqual(capital, Decimal('1200.00'))
        self.assertEqual(self.usuario.capital_total, Decimal('1200.00'))
    
    def test_generar_codigos_respaldo(self):
        """Test de generación de códigos de respaldo"""
        codigos = Usuario.generar_codigos_respaldo()
        self.assertEqual(len(codigos), 10)
        for codigo in codigos:
            self.assertEqual(len(codigo), 8)
            self.assertTrue(codigo.isupper())
    
    def test_activar_2fa(self):
        """Test de activación de 2FA"""
        import pyotp
        
        # Generar secreto
        self.usuario.secreto_2fa = pyotp.random_base32()
        self.usuario.tiene_2fa_activo = True
        self.usuario.fecha_activacion_2fa = timezone.now()
        self.usuario.save()
        
        self.assertTrue(self.usuario.tiene_2fa_activo)
        self.assertIsNotNone(self.usuario.secreto_2fa)
        self.assertIsNotNone(self.usuario.fecha_activacion_2fa)


class MercadoModelTest(TestCase):
    """Tests para el modelo Mercado"""
    
    def test_crear_mercado(self):
        """Test de creación de mercado"""
        mercado = Mercado.objects.create(
            nombre='XAUUSD',
            codigo='XAUUSD',
            descripcion='Oro vs Dólar',
            activo=True
        )
        self.assertEqual(mercado.nombre, 'XAUUSD')
        self.assertEqual(str(mercado), 'XAUUSD')
        self.assertTrue(mercado.activo)
    
    def test_codigo_unico(self):
        """Test que el código debe ser único"""
        Mercado.objects.create(nombre='XAUUSD', codigo='XAUUSD')
        with self.assertRaises(Exception):
            Mercado.objects.create(nombre='XAUUSD2', codigo='XAUUSD')


class ProductoModelTest(TestCase):
    """Tests para el modelo Producto"""
    
    def setUp(self):
        self.mercado = Mercado.objects.create(
            nombre='XAUUSD',
            codigo='XAUUSD'
        )
    
    def test_crear_producto(self):
        """Test de creación de producto"""
        producto = Producto.objects.create(
            nombre='Producto Premium',
            codigo='PREM001',
            descripcion='Producto de prueba',
            activo=True
        )
        producto.mercados.add(self.mercado)
        
        self.assertEqual(producto.nombre, 'Producto Premium')
        self.assertEqual(str(producto), 'Producto Premium')
        self.assertTrue(producto.activo)
        self.assertEqual(producto.mercados.count(), 1)


class ProductoContratadoModelTest(TestCase):
    """Tests para el modelo ProductoContratado"""
    
    def setUp(self):
        self.usuario = Usuario.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!'
        )
        self.mercado = Mercado.objects.create(nombre='XAUUSD', codigo='XAUUSD')
        self.producto = Producto.objects.create(
            nombre='Producto Test',
            codigo='PROD001'
        )
        self.producto.mercados.add(self.mercado)
    
    def test_crear_contratacion(self):
        """Test de creación de contratación"""
        contrato = ProductoContratado.objects.create(
            usuario=self.usuario,
            producto=self.producto,
            monto_invertido=Decimal('1000.00'),
            capital_actual=Decimal('1000.00'),
            estado='activo'
        )
        
        self.assertEqual(contrato.monto_invertido, Decimal('1000.00'))
        self.assertEqual(contrato.estado, 'activo')
        self.assertIn('test@example.com', str(contrato))
    
    def test_unique_together(self):
        """Test que un usuario no puede contratar el mismo producto dos veces"""
        ProductoContratado.objects.create(
            usuario=self.usuario,
            producto=self.producto,
            monto_invertido=Decimal('1000.00'),
            capital_actual=Decimal('1000.00')
        )
        
        with self.assertRaises(Exception):
            ProductoContratado.objects.create(
                usuario=self.usuario,
                producto=self.producto,
                monto_invertido=Decimal('2000.00'),
                capital_actual=Decimal('2000.00')
            )


class ResultadoModelTest(TestCase):
    """Tests para el modelo Resultado"""
    
    def setUp(self):
        self.usuario = Usuario.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!'
        )
        self.mercado = Mercado.objects.create(nombre='XAUUSD', codigo='XAUUSD')
        self.producto = Producto.objects.create(nombre='Producto Test', codigo='PROD001')
        self.producto.mercados.add(self.mercado)
        self.contrato = ProductoContratado.objects.create(
            usuario=self.usuario,
            producto=self.producto,
            monto_invertido=Decimal('1000.00'),
            capital_actual=Decimal('1000.00')
        )
    
    def test_crear_resultado(self):
        """Test de creación de resultado"""
        resultado = Resultado.objects.create(
            usuario=self.usuario,
            producto_contratado=self.contrato,
            fecha=timezone.now().date(),
            mes='Enero',
            anio=2024,
            capital_mes=Decimal('1200.00')
        )
        
        self.assertEqual(resultado.capital_mes, Decimal('1200.00'))
        self.assertEqual(resultado.mes, 'Enero')
        self.assertIn('test@example.com', str(resultado))
    
    def test_calcular_cambios(self):
        """Test de cálculo de cambios mensuales"""
        resultado = Resultado.objects.create(
            usuario=self.usuario,
            producto_contratado=self.contrato,
            fecha=timezone.now().date(),
            mes='Enero',
            anio=2024,
            capital_mes=Decimal('1200.00')
        )
        
        # Calcular cambios respecto a capital anterior
        resultado.calcular_cambios(Decimal('1000.00'))
        
        self.assertEqual(resultado.cambio_mensual, Decimal('200.00'))
        self.assertEqual(resultado.porcentaje_cambio, Decimal('20.00'))


class TokenVerificacionEmailModelTest(TestCase):
    """Tests para el modelo TokenVerificacionEmail"""
    
    def setUp(self):
        self.usuario = Usuario.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!',
            is_active=False
        )
    
    def test_crear_token(self):
        """Test de creación de token de verificación"""
        token = secrets.token_urlsafe(32)
        token_obj = TokenVerificacionEmail.objects.create(
            usuario=self.usuario,
            token=token,
            expira_en=timezone.now() + timedelta(hours=24)
        )
        
        self.assertEqual(token_obj.token, token)
        self.assertFalse(token_obj.usado)
        self.assertIn('test@example.com', str(token_obj))
    
    def test_token_expirado(self):
        """Test de verificación de expiración de token"""
        token_obj = TokenVerificacionEmail.objects.create(
            usuario=self.usuario,
            token=secrets.token_urlsafe(32),
            expira_en=timezone.now() - timedelta(hours=1)  # Expirado
        )
        
        self.assertTrue(token_obj.esta_expirado())
    
    def test_token_valido(self):
        """Test de token válido"""
        token_obj = TokenVerificacionEmail.objects.create(
            usuario=self.usuario,
            token=secrets.token_urlsafe(32),
            expira_en=timezone.now() + timedelta(hours=24)
        )
        
        self.assertFalse(token_obj.esta_expirado())


class TokenRecuperacionPasswordModelTest(TestCase):
    """Tests para el modelo TokenRecuperacionPassword"""
    
    def setUp(self):
        self.usuario = Usuario.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!'
        )
    
    def test_crear_token_recuperacion(self):
        """Test de creación de token de recuperación"""
        token = secrets.token_urlsafe(32)
        token_obj = TokenRecuperacionPassword.objects.create(
            usuario=self.usuario,
            token=token,
            expira_en=timezone.now() + timedelta(hours=1)
        )
        
        self.assertEqual(token_obj.token, token)
        self.assertFalse(token_obj.usado)
        self.assertIn('test@example.com', str(token_obj))
    
    def test_token_expirado(self):
        """Test de verificación de expiración"""
        token_obj = TokenRecuperacionPassword.objects.create(
            usuario=self.usuario,
            token=secrets.token_urlsafe(32),
            expira_en=timezone.now() - timedelta(minutes=30)
        )
        
        self.assertTrue(token_obj.esta_expirado())


class SesionSeguridadModelTest(TestCase):
    """Tests para el modelo SesionSeguridad"""
    
    def setUp(self):
        self.usuario = Usuario.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!'
        )
    
    def test_crear_sesion_exitosa(self):
        """Test de creación de sesión exitosa"""
        sesion = SesionSeguridad.objects.create(
            usuario=self.usuario,
            ip_address='192.168.1.1',
            user_agent='Mozilla/5.0',
            exitoso=True,
            requirio_2fa=False
        )
        
        self.assertTrue(sesion.exitoso)
        self.assertEqual(sesion.ip_address, '192.168.1.1')
        self.assertIn('Exitoso', str(sesion))
    
    def test_crear_sesion_fallida(self):
        """Test de creación de sesión fallida"""
        sesion = SesionSeguridad.objects.create(
            usuario=self.usuario,
            ip_address='192.168.1.1',
            user_agent='Mozilla/5.0',
            exitoso=False,
            motivo_fallo='Contraseña incorrecta'
        )
        
        self.assertFalse(sesion.exitoso)
        self.assertEqual(sesion.motivo_fallo, 'Contraseña incorrecta')
        self.assertIn('Fallido', str(sesion))