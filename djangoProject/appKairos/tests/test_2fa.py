"""
Tests específicos para la funcionalidad de autenticación de dos factores (2FA)
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth.hashers import make_password, check_password
import pyotp

from appKairos.models import Usuario


class Activar2FAViewTest(TestCase):
    """Tests para la vista de activación de 2FA"""
    
    def setUp(self):
        self.client = Client()
        self.usuario = Usuario.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!',
            is_active=True
        )
        self.url = reverse('appKairos:activar_2fa')
        self.client.login(username='testuser', password='TestPass123!')
    
    def test_get_activar_2fa(self):
        """Test GET a la vista de activación"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'activar_2fa.html')
        
        # Verificar que se generó un secreto
        self.usuario.refresh_from_db()
        self.assertIsNotNone(self.usuario.secreto_2fa)
        
        # Verificar que se muestra el QR code
        self.assertIn('qr_code', response.context)
        self.assertIn('secret_key', response.context)
    
    def test_activar_2fa_con_codigo_correcto(self):
        """Test de activación con código correcto"""
        # Generar secreto
        self.usuario.secreto_2fa = pyotp.random_base32()
        self.usuario.save()
        
        # Generar código válido
        totp = pyotp.TOTP(self.usuario.secreto_2fa)
        codigo_valido = totp.now()
        
        data = {'codigo_verificacion': codigo_valido}
        response = self.client.post(self.url, data)
        
        # Verificar que 2FA fue activado
        self.usuario.refresh_from_db()
        self.assertTrue(self.usuario.tiene_2fa_activo)
        self.assertIsNotNone(self.usuario.fecha_activacion_2fa)
        
        # Verificar que se generaron códigos de respaldo
        self.assertIsNotNone(self.usuario.codigos_respaldo_2fa)
    
    def test_activar_2fa_con_codigo_incorrecto(self):
        """Test de activación con código incorrecto"""
        self.usuario.secreto_2fa = pyotp.random_base32()
        self.usuario.save()
        
        data = {'codigo_verificacion': '000000'}  # Código incorrecto
        response = self.client.post(self.url, data)
        
        # Verificar que 2FA NO fue activado
        self.usuario.refresh_from_db()
        self.assertFalse(self.usuario.tiene_2fa_activo)
    
    def test_redireccion_si_2fa_ya_activo(self):
        """Test de redirección si 2FA ya está activo"""
        self.usuario.tiene_2fa_activo = True
        self.usuario.save()
        
        response = self.client.get(self.url)
        
        # Debe redirigir al dashboard
        self.assertEqual(response.status_code, 302)


class Verificar2FAViewTest(TestCase):
    """Tests para la vista de verificación 2FA durante login"""
    
    def setUp(self):
        self.client = Client()
        self.usuario = Usuario.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!',
            is_active=True,
            tiene_2fa_activo=True
        )
        self.usuario.secreto_2fa = pyotp.random_base32()
        
        # Generar códigos de respaldo
        codigos_respaldo = Usuario.generar_codigos_respaldo()
        codigos_encriptados = [make_password(codigo) for codigo in codigos_respaldo]
        self.usuario.codigos_respaldo_2fa = ','.join(codigos_encriptados)
        self.usuario.save()
        
        self.codigo_respaldo_valido = codigos_respaldo[0]
        self.url = reverse('appKairos:verificar_2fa')
    
    def test_verificacion_con_codigo_totp_correcto(self):
        """Test de verificación con código TOTP correcto"""
        # Simular login previo
        session = self.client.session
        session['pre_2fa_user_id'] = self.usuario.id
        session['pre_2fa_timestamp'] = timezone.now().timestamp()
        session['intentos_2fa'] = 0
        session.save()
        
        # Generar código válido
        totp = pyotp.TOTP(self.usuario.secreto_2fa)
        codigo_valido = totp.now()
        
        data = {'codigo_2fa': codigo_valido, 'codigo_respaldo': ''}
        response = self.client.post(self.url, data)
        
        # Verificar redirección al dashboard
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.endswith('/dashboard/'))
        
        # Verificar que el usuario está autenticado
        self.assertTrue('_auth_user_id' in self.client.session)
    
    def test_verificacion_con_codigo_respaldo(self):
        """Test de verificación con código de respaldo"""
        # Simular login previo
        session = self.client.session
        session['pre_2fa_user_id'] = self.usuario.id
        session['pre_2fa_timestamp'] = timezone.now().timestamp()
        session['intentos_2fa'] = 0
        session.save()
        
        data = {'codigo_2fa': '', 'codigo_respaldo': self.codigo_respaldo_valido}
        response = self.client.post(self.url, data)
        
        # Verificar redirección al dashboard
        self.assertEqual(response.status_code, 302)
        
        # Verificar que el código de respaldo fue eliminado
        self.usuario.refresh_from_db()
        codigos_restantes = self.usuario.codigos_respaldo_2fa.split(',')
        self.assertEqual(len(codigos_restantes), 9)  # Debe quedar uno menos
    
    def test_verificacion_con_codigo_incorrecto(self):
        """Test de verificación con código incorrecto"""
        session = self.client.session
        session['pre_2fa_user_id'] = self.usuario.id
        session['pre_2fa_timestamp'] = timezone.now().timestamp()
        session['intentos_2fa'] = 0
        session.save()
        
        data = {'codigo_2fa': '000000', 'codigo_respaldo': ''}
        response = self.client.post(self.url, data)
        
        # Verificar que no se autenticó
        self.assertFalse('_auth_user_id' in self.client.session)
        
        # Verificar que se incrementaron los intentos
        self.assertEqual(self.client.session['intentos_2fa'], 1)
    
    def test_limite_intentos_fallidos(self):
        """Test del límite de intentos fallidos"""
        session = self.client.session
        session['pre_2fa_user_id'] = self.usuario.id
        session['pre_2fa_timestamp'] = timezone.now().timestamp()
        session['intentos_2fa'] = 3  # Ya alcanzó el límite
        session.save()
        
        response = self.client.get(self.url)
        
        # Debe redirigir al login
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.endswith('/login/'))


class Desactivar2FAViewTest(TestCase):
    """Tests para la vista de desactivación de 2FA"""
    
    def setUp(self):
        self.client = Client()
        self.usuario = Usuario.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!',
            is_active=True,
            tiene_2fa_activo=True
        )
        self.usuario.secreto_2fa = pyotp.random_base32()
        self.usuario.save()
        
        self.url = reverse('appKairos:desactivar_2fa')
        self.client.login(username='testuser', password='TestPass123!')
    
    def test_get_desactivar_2fa(self):
        """Test GET a la vista de desactivación"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'desactivar_2fa.html')
    
    def test_desactivar_2fa_con_password_correcto(self):
        """Test de desactivación con contraseña correcta"""
        data = {'password': 'TestPass123!'}
        response = self.client.post(self.url, data)
        
        # Verificar redirección
        self.assertEqual(response.status_code, 302)
        
        # Verificar que 2FA fue desactivado
        self.usuario.refresh_from_db()
        self.assertFalse(self.usuario.tiene_2fa_activo)
        self.assertIsNone(self.usuario.secreto_2fa)
        self.assertIsNone(self.usuario.codigos_respaldo_2fa)
    
    def test_desactivar_2fa_con_password_incorrecto(self):
        """Test de desactivación con contraseña incorrecta"""
        data = {'password': 'WrongPassword123!'}
        response = self.client.post(self.url, data)
        
        # Verificar que 2FA NO fue desactivado
        self.usuario.refresh_from_db()
        self.assertTrue(self.usuario.tiene_2fa_activo)
    
    def test_redireccion_si_2fa_no_activo(self):
        """Test de redirección si 2FA no está activo"""
        self.usuario.tiene_2fa_activo = False
        self.usuario.save()
        
        response = self.client.get(self.url)
        
        # Debe redirigir al dashboard
        self.assertEqual(response.status_code, 302)


class CodigosRespaldo2FATest(TestCase):
    """Tests para la funcionalidad de códigos de respaldo"""
    
    def test_generar_codigos_respaldo(self):
        """Test de generación de códigos de respaldo"""
        codigos = Usuario.generar_codigos_respaldo()
        
        # Verificar cantidad
        self.assertEqual(len(codigos), 10)
        
        # Verificar formato
        for codigo in codigos:
            self.assertEqual(len(codigo), 8)
            self.assertTrue(codigo.isupper())
            self.assertTrue(all(c in '0123456789ABCDEF' for c in codigo))
        
        # Verificar que son únicos
        self.assertEqual(len(codigos), len(set(codigos)))
    
    def test_encriptar_codigos_respaldo(self):
        """Test de encriptación de códigos de respaldo"""
        codigos = Usuario.generar_codigos_respaldo()
        codigos_encriptados = [make_password(codigo) for codigo in codigos]
        
        # Verificar que están encriptados
        for i, codigo_encriptado in enumerate(codigos_encriptados):
            self.assertNotEqual(codigos[i], codigo_encriptado)
            self.assertTrue(check_password(codigos[i], codigo_encriptado))
    
    def test_usar_codigo_respaldo(self):
        """Test de uso de código de respaldo"""
        usuario = Usuario.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!',
            tiene_2fa_activo=True
        )
        
        # Generar y guardar códigos
        codigos = Usuario.generar_codigos_respaldo()
        codigos_encriptados = [make_password(codigo) for codigo in codigos]
        usuario.codigos_respaldo_2fa = ','.join(codigos_encriptados)
        usuario.save()
        
        # Usar un código
        codigo_usado = codigos[0]
        codigos_actuales = usuario.codigos_respaldo_2fa.split(',')
        
        # Buscar y eliminar el código usado
        for idx, codigo_enc in enumerate(codigos_actuales):
            if check_password(codigo_usado, codigo_enc):
                codigos_actuales.pop(idx)
                break
        
        # Verificar que se eliminó
        self.assertEqual(len(codigos_actuales), 9)