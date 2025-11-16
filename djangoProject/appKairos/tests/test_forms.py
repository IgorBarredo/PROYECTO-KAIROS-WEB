"""
Tests para los formularios de la aplicación appKairos
"""
from django.test import TestCase
from appKairos.forms import (
    RegistroUsuarioForm, LoginForm, Activar2FAForm,
    Verificar2FAForm, Desactivar2FAForm,
    SolicitarRecuperacionPasswordForm, ResetPasswordForm,
    CambiarPasswordForm, ContactoForm
)
from appKairos.models import Usuario


class RegistroUsuarioFormTest(TestCase):
    """Tests para el formulario de registro"""
    
    def test_formulario_valido(self):
        """Test con datos válidos"""
        form_data = {
            'email': 'nuevo@example.com',
            'username': 'nuevousuario',
            'first_name': 'Nuevo',
            'last_name': 'Usuario',
            'telefono': '+34600000000',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!',
            'acepto_terminos': True
        }
        form = RegistroUsuarioForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_email_duplicado(self):
        """Test con email duplicado"""
        Usuario.objects.create_user(
            username='existente',
            email='existente@example.com',
            password='TestPass123!'
        )
        
        form_data = {
            'email': 'existente@example.com',
            'username': 'nuevousuario',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!',
            'acepto_terminos': True
        }
        form = RegistroUsuarioForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
    
    def test_password_debil(self):
        """Test con contraseña débil"""
        form_data = {
            'email': 'nuevo@example.com',
            'username': 'nuevousuario',
            'password1': 'password',  # Sin mayúsculas, números ni caracteres especiales
            'password2': 'password',
            'acepto_terminos': True
        }
        form = RegistroUsuarioForm(data=form_data)
        self.assertFalse(form.is_valid())
    
    def test_passwords_no_coinciden(self):
        """Test cuando las contraseñas no coinciden"""
        form_data = {
            'email': 'nuevo@example.com',
            'username': 'nuevousuario',
            'password1': 'TestPass123!',
            'password2': 'TestPass456!',
            'acepto_terminos': True
        }
        form = RegistroUsuarioForm(data=form_data)
        self.assertFalse(form.is_valid())
    
    def test_terminos_no_aceptados(self):
        """Test sin aceptar términos"""
        form_data = {
            'email': 'nuevo@example.com',
            'username': 'nuevousuario',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!',
            'acepto_terminos': False
        }
        form = RegistroUsuarioForm(data=form_data)
        self.assertFalse(form.is_valid())


class Activar2FAFormTest(TestCase):
    """Tests para el formulario de activación 2FA"""
    
    def test_codigo_valido(self):
        """Test con código válido de 6 dígitos"""
        form_data = {'codigo_verificacion': '123456'}
        form = Activar2FAForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_codigo_invalido_longitud(self):
        """Test con código de longitud incorrecta"""
        form_data = {'codigo_verificacion': '12345'}  # Solo 5 dígitos
        form = Activar2FAForm(data=form_data)
        self.assertFalse(form.is_valid())
    
    def test_codigo_no_numerico(self):
        """Test con código no numérico"""
        form_data = {'codigo_verificacion': 'abc123'}
        form = Activar2FAForm(data=form_data)
        self.assertFalse(form.is_valid())


class Verificar2FAFormTest(TestCase):
    """Tests para el formulario de verificación 2FA"""
    
    def test_codigo_2fa_valido(self):
        """Test con código 2FA válido"""
        form_data = {'codigo_2fa': '123456', 'codigo_respaldo': ''}
        form = Verificar2FAForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_codigo_respaldo_valido(self):
        """Test con código de respaldo válido"""
        form_data = {'codigo_2fa': '', 'codigo_respaldo': 'ABCD1234'}
        form = Verificar2FAForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_sin_codigos(self):
        """Test sin ningún código"""
        form_data = {'codigo_2fa': '', 'codigo_respaldo': ''}
        form = Verificar2FAForm(data=form_data)
        self.assertFalse(form.is_valid())


class Desactivar2FAFormTest(TestCase):
    """Tests para el formulario de desactivación 2FA"""
    
    def test_password_valido(self):
        """Test con contraseña válida"""
        form_data = {'password': 'TestPass123!'}
        form = Desactivar2FAForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_password_vacio(self):
        """Test sin contraseña"""
        form_data = {'password': ''}
        form = Desactivar2FAForm(data=form_data)
        self.assertFalse(form.is_valid())


class SolicitarRecuperacionPasswordFormTest(TestCase):
    """Tests para el formulario de solicitud de recuperación"""
    
    def test_email_valido(self):
        """Test con email válido"""
        form_data = {'email': 'test@example.com'}
        form = SolicitarRecuperacionPasswordForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_email_invalido(self):
        """Test con email inválido"""
        form_data = {'email': 'email_invalido'}
        form = SolicitarRecuperacionPasswordForm(data=form_data)
        self.assertFalse(form.is_valid())


class ResetPasswordFormTest(TestCase):
    """Tests para el formulario de reset de contraseña"""
    
    def test_passwords_validos(self):
        """Test con contraseñas válidas y coincidentes"""
        form_data = {
            'password_nueva': 'NewPass123!',
            'password_confirmacion': 'NewPass123!'
        }
        form = ResetPasswordForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_passwords_no_coinciden(self):
        """Test con contraseñas que no coinciden"""
        form_data = {
            'password_nueva': 'NewPass123!',
            'password_confirmacion': 'DifferentPass123!'
        }
        form = ResetPasswordForm(data=form_data)
        self.assertFalse(form.is_valid())
    
    def test_password_debil(self):
        """Test con contraseña débil"""
        form_data = {
            'password_nueva': 'weak',
            'password_confirmacion': 'weak'
        }
        form = ResetPasswordForm(data=form_data)
        self.assertFalse(form.is_valid())


class CambiarPasswordFormTest(TestCase):
    """Tests para el formulario de cambio de contraseña"""
    
    def test_formulario_valido(self):
        """Test con datos válidos"""
        form_data = {
            'password_actual': 'OldPass123!',
            'password_nueva': 'NewPass123!',
            'password_confirmacion': 'NewPass123!'
        }
        form = CambiarPasswordForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_passwords_no_coinciden(self):
        """Test con contraseñas nuevas que no coinciden"""
        form_data = {
            'password_actual': 'OldPass123!',
            'password_nueva': 'NewPass123!',
            'password_confirmacion': 'DifferentPass123!'
        }
        form = CambiarPasswordForm(data=form_data)
        self.assertFalse(form.is_valid())


class ContactoFormTest(TestCase):
    """Tests para el formulario de contacto"""
    
    def test_formulario_valido(self):
        """Test con datos válidos"""
        form_data = {
            'nombre': 'Juan Pérez',
            'email': 'juan@example.com',
            'mensaje': 'Este es un mensaje de prueba con más de 10 caracteres'
        }
        form = ContactoForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_mensaje_muy_corto(self):
        """Test con mensaje demasiado corto"""
        form_data = {
            'nombre': 'Juan Pérez',
            'email': 'juan@example.com',
            'mensaje': 'Corto'
        }
        form = ContactoForm(data=form_data)
        self.assertFalse(form.is_valid())
    
    def test_email_invalido(self):
        """Test con email inválido"""
        form_data = {
            'nombre': 'Juan Pérez',
            'email': 'email_invalido',
            'mensaje': 'Este es un mensaje válido'
        }
        form = ContactoForm(data=form_data)
        self.assertFalse(form.is_valid())