"""
Tests para las vistas de la aplicación appKairos
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
import secrets

from appKairos.models import (
    Usuario, TokenVerificacionEmail, TokenRecuperacionPassword,
    Mercado, Producto
)


class RegistroViewTest(TestCase):
    """Tests para la vista de registro"""
    
    def setUp(self):
        self.client = Client()
        self.url = reverse('appKairos:register')
    
    def test_get_registro_view(self):
        """Test GET a la vista de registro"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'register_en.html')
    
    def test_registro_exitoso(self):
        """Test de registro exitoso"""
        data = {
            'email': 'nuevo@example.com',
            'username': 'nuevousuario',
            'first_name': 'Nuevo',
            'last_name': 'Usuario',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!',
            'acepto_terminos': True
        }
        response = self.client.post(self.url, data)
        
        # Verificar redirección
        self.assertEqual(response.status_code, 302)
        
        # Verificar que el usuario fue creado
        usuario = Usuario.objects.get(email='nuevo@example.com')
        self.assertFalse(usuario.is_active)  # Debe estar inactivo hasta verificar email
        
        # Verificar que se creó un token de verificación
        self.assertTrue(TokenVerificacionEmail.objects.filter(usuario=usuario).exists())


class LoginViewTest(TestCase):
    """Tests para la vista de login"""
    
    def setUp(self):
        self.client = Client()
        self.url = reverse('appKairos:login')
        self.usuario = Usuario.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!',
            is_active=True
        )
    
    def test_get_login_view(self):
        """Test GET a la vista de login"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'login_en.html')
    
    def test_login_exitoso(self):
        """Test de login exitoso"""
        data = {
            'username': 'test@example.com',
            'password': 'TestPass123!'
        }
        response = self.client.post(self.url, data)
        
        # Verificar redirección al dashboard
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.endswith('/dashboard/'))
    
    def test_login_fallido(self):
        """Test de login con credenciales incorrectas"""
        data = {
            'username': 'test@example.com',
            'password': 'WrongPassword123!'
        }
        response = self.client.post(self.url, data)
        
        # Debe mostrar error
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Email o contraseña incorrectos')


class VerificarEmailViewTest(TestCase):
    """Tests para la vista de verificación de email"""
    
    def setUp(self):
        self.client = Client()
        self.usuario = Usuario.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!',
            is_active=False
        )
        self.token = secrets.token_urlsafe(32)
        self.token_obj = TokenVerificacionEmail.objects.create(
            usuario=self.usuario,
            token=self.token,
            expira_en=timezone.now() + timedelta(hours=24)
        )
    
    def test_verificacion_exitosa(self):
        """Test de verificación exitosa"""
        url = reverse('appKairos:verificar_email', kwargs={'token': self.token})
        response = self.client.get(url)
        
        # Verificar redirección
        self.assertEqual(response.status_code, 302)
        
        # Verificar que el usuario fue activado
        self.usuario.refresh_from_db()
        self.assertTrue(self.usuario.is_active)
        self.assertTrue(self.usuario.email_verificado)
        
        # Verificar que el token fue marcado como usado
        self.token_obj.refresh_from_db()
        self.assertTrue(self.token_obj.usado)
    
    def test_token_invalido(self):
        """Test con token inválido"""
        url = reverse('appKairos:verificar_email', kwargs={'token': 'token_invalido'})
        response = self.client.get(url)
        
        # Debe redirigir con mensaje de error
        self.assertEqual(response.status_code, 302)


class SolicitarRecuperacionViewTest(TestCase):
    """Tests para la vista de solicitud de recuperación"""
    
    def setUp(self):
        self.client = Client()
        self.url = reverse('appKairos:solicitar_recuperacion')
        self.usuario = Usuario.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!',
            is_active=True
        )
    
    def test_get_solicitar_recuperacion(self):
        """Test GET a la vista"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'solicitar_recuperacion.html')
    
    def test_solicitar_recuperacion_exitoso(self):
        """Test de solicitud exitosa"""
        data = {'email': 'test@example.com'}
        response = self.client.post(self.url, data)
        
        # Verificar redirección
        self.assertEqual(response.status_code, 302)
        
        # Verificar que se creó un token de recuperación
        self.assertTrue(TokenRecuperacionPassword.objects.filter(usuario=self.usuario).exists())


class ResetPasswordViewTest(TestCase):
    """Tests para la vista de reset de contraseña"""
    
    def setUp(self):
        self.client = Client()
        self.usuario = Usuario.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='OldPass123!',
            is_active=True
        )
        self.token = secrets.token_urlsafe(32)
        self.token_obj = TokenRecuperacionPassword.objects.create(
            usuario=self.usuario,
            token=self.token,
            expira_en=timezone.now() + timedelta(hours=1)
        )
        self.url = reverse('appKairos:reset_password', kwargs={'token': self.token})
    
    def test_get_reset_password(self):
        """Test GET a la vista"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'reset_password.html')
    
    def test_reset_password_exitoso(self):
        """Test de cambio de contraseña exitoso"""
        data = {
            'password_nueva': 'NewPass123!',
            'password_confirmacion': 'NewPass123!'
        }
        response = self.client.post(self.url, data)
        
        # Verificar redirección
        self.assertEqual(response.status_code, 302)
        
        # Verificar que la contraseña cambió
        self.usuario.refresh_from_db()
        self.assertTrue(self.usuario.check_password('NewPass123!'))
        
        # Verificar que el token fue marcado como usado
        self.token_obj.refresh_from_db()
        self.assertTrue(self.token_obj.usado)


class DashboardViewTest(TestCase):
    """Tests para la vista del dashboard"""
    
    def setUp(self):
        self.client = Client()
        self.usuario = Usuario.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!',
            is_active=True
        )
        self.url = reverse('appKairos:dashboard')
    
    def test_dashboard_requiere_login(self):
        """Test que el dashboard requiere autenticación"""
        response = self.client.get(self.url)
        
        # Debe redirigir al login
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/login/'))
    
    def test_dashboard_con_usuario_autenticado(self):
        """Test del dashboard con usuario autenticado"""
        self.client.login(username='testuser', password='TestPass123!')
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard_en.html')
        self.assertIn('usuario', response.context)


class PerfilViewTest(TestCase):
    """Tests para la vista de perfil"""
    
    def setUp(self):
        self.client = Client()
        self.usuario = Usuario.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!',
            is_active=True
        )
        self.url = reverse('appKairos:perfil')
        self.client.login(username='testuser', password='TestPass123!')
    
    def test_get_perfil(self):
        """Test GET a la vista de perfil"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'perfil.html')
    
    def test_actualizar_perfil(self):
        """Test de actualización de perfil"""
        data = {
            'first_name': 'Nuevo',
            'last_name': 'Nombre',
            'telefono': '+34600000000'
        }
        response = self.client.post(self.url, data)
        
        # Verificar redirección
        self.assertEqual(response.status_code, 302)
        
        # Verificar que los datos se actualizaron
        self.usuario.refresh_from_db()
        self.assertEqual(self.usuario.first_name, 'Nuevo')
        self.assertEqual(self.usuario.last_name, 'Nombre')


class IndexViewTest(TestCase):
    """Tests para la vista principal"""
    
    def setUp(self):
        self.client = Client()
        self.url = reverse('appKairos:index')
    
    def test_index_view(self):
        """Test de la vista principal"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'index_en.html')