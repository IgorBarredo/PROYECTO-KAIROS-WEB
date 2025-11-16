from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .models import Usuario, ProductoContratado
import re


class RegistroUsuarioForm(UserCreationForm):
    """
    Formulario de registro de usuario con email como identificador principal
    """
    email = forms.EmailField(
        label='Email',
        max_length=254,
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'tu_email@ejemplo.com',
            'autocomplete': 'email'
        }),
        help_text='Ingresa un email válido. Será tu nombre de usuario.'
    )
    
    username = forms.CharField(
        label='Nombre de usuario',
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nombre de usuario',
            'autocomplete': 'username'
        }),
        help_text='Requerido. 150 caracteres o menos. Letras, dígitos y @/./+/-/_ solamente.'
    )
    
    first_name = forms.CharField(
        label='Nombre',
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nombre',
            'autocomplete': 'given-name'
        })
    )
    
    last_name = forms.CharField(
        label='Apellidos',
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Apellidos',
            'autocomplete': 'family-name'
        })
    )
    
    telefono = forms.CharField(
        label='Teléfono',
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+34 600 000 000',
            'autocomplete': 'tel'
        })
    )
    
    password1 = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Contraseña',
            'autocomplete': 'new-password'
        }),
        help_text='''
        Tu contraseña debe contener:
        • Al menos 8 caracteres
        • Al menos una letra mayúscula
        • Al menos una letra minúscula
        • Al menos un número
        • Al menos un carácter especial (@$!%*?&)
        '''
    )
    
    password2 = forms.CharField(
        label='Confirmar contraseña',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirmar contraseña',
            'autocomplete': 'new-password'
        }),
        help_text='Ingresa la misma contraseña para verificación.'
    )
    
    acepto_terminos = forms.BooleanField(
        label='Acepto los términos y condiciones',
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    class Meta:
        model = Usuario
        fields = ['email', 'username', 'first_name', 'last_name', 'telefono', 'password1', 'password2']
    
    def clean_email(self):
        """Valida que el email no esté registrado"""
        email = self.cleaned_data.get('email')
        if Usuario.objects.filter(email=email).exists():
            raise ValidationError('Este email ya está registrado.')
        return email.lower()
    
    def clean_password1(self):
        """Valida que la contraseña cumpla con los requisitos de seguridad"""
        password = self.cleaned_data.get('password1')
        
        if len(password) < 8:
            raise ValidationError('La contraseña debe tener al menos 8 caracteres.')
        
        if not re.search(r'[A-Z]', password):
            raise ValidationError('La contraseña debe contener al menos una letra mayúscula.')
        
        if not re.search(r'[a-z]', password):
            raise ValidationError('La contraseña debe contener al menos una letra minúscula.')
        
        if not re.search(r'\d', password):
            raise ValidationError('La contraseña debe contener al menos un número.')
        
        if not re.search(r'[@$!%*?&]', password):
            raise ValidationError('La contraseña debe contener al menos un carácter especial (@$!%*?&).')
        
        return password
    
    def save(self, commit=True):
        """Guarda el usuario con el email como identificador"""
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.telefono = self.cleaned_data.get('telefono', '')
        if commit:
            user.save()
        return user


class LoginForm(AuthenticationForm):
    """
    Formulario de login con email como identificador
    """
    username = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'tu_email@ejemplo.com',
            'autocomplete': 'email',
            'autofocus': True
        })
    )
    
    password = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Contraseña',
            'autocomplete': 'current-password'
        })
    )
    
    recordarme = forms.BooleanField(
        label='Recordarme',
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    error_messages = {
        'invalid_login': _(
            "Por favor ingresa un email y contraseña correctos. "
            "Ten en cuenta que ambos campos pueden ser sensibles a mayúsculas."
        ),
        'inactive': _("Esta cuenta está inactiva."),
    }


class VerificarEmailForm(forms.Form):
    """
    Formulario para verificar el email del usuario mediante token
    """
    token = forms.CharField(
        label='Código de verificación',
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingresa el código recibido por email',
            'autocomplete': 'off'
        }),
        help_text='Revisa tu email e ingresa el código de verificación de 6 dígitos.'
    )
    
    def clean_token(self):
        """Valida el formato del token"""
        token = self.cleaned_data.get('token')
        if not token:
            raise ValidationError('Debes ingresar el código de verificación.')
        return token.strip()


class Activar2FAForm(forms.Form):
    """
    Formulario para activar la autenticación de dos factores
    """
    codigo_verificacion = forms.CharField(
        label='Código de verificación',
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '000000',
            'autocomplete': 'off',
            'pattern': '[0-9]{6}',
            'inputmode': 'numeric'
        }),
        help_text='Ingresa el código de 6 dígitos generado por Google Authenticator.'
    )
    
    def clean_codigo_verificacion(self):
        """Valida que el código sea numérico de 6 dígitos"""
        codigo = self.cleaned_data.get('codigo_verificacion')
        if not codigo.isdigit():
            raise ValidationError('El código debe contener solo números.')
        if len(codigo) != 6:
            raise ValidationError('El código debe tener exactamente 6 dígitos.')
        return codigo


class Verificar2FAForm(forms.Form):
    """
    Formulario para verificar el código 2FA durante el login
    """
    codigo_2fa = forms.CharField(
        label='Código de autenticación',
        max_length=6,
        min_length=6,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '000000',
            'autocomplete': 'off',
            'pattern': '[0-9]{6}',
            'inputmode': 'numeric',
            'autofocus': True
        }),
        help_text='Ingresa el código de 6 dígitos de tu aplicación de autenticación.'
    )
    
    codigo_respaldo = forms.CharField(
        label='Código de respaldo',
        max_length=8,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'XXXXXXXX',
            'autocomplete': 'off'
        }),
        help_text='O ingresa un código de respaldo si no tienes acceso a tu aplicador.'
    )
    
    def clean(self):
        """Valida que al menos uno de los códigos esté presente"""
        cleaned_data = super().clean()
        codigo_2fa = cleaned_data.get('codigo_2fa')
        codigo_respaldo = cleaned_data.get('codigo_respaldo')
        
        if not codigo_2fa and not codigo_respaldo:
            raise ValidationError('Debes ingresar un código 2FA o un código de respaldo.')
        
        if codigo_2fa and not codigo_2fa.isdigit():
            raise ValidationError('El código 2FA debe contener solo números.')
        
        if codigo_2fa and len(codigo_2fa) != 6:
            raise ValidationError('El código 2FA debe tener exactamente 6 dígitos.')
        
        return cleaned_data


class Desactivar2FAForm(forms.Form):
    """
    Formulario para desactivar 2FA con verificación de contraseña
    """
    password = forms.CharField(
        label='Contraseña actual',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingresa tu contraseña para confirmar',
            'autocomplete': 'current-password'
        }),
        help_text='Por seguridad, debes ingresar tu contraseña para desactivar 2FA.'
    )


class SolicitarRecuperacionPasswordForm(forms.Form):
    """
    Formulario para solicitar recuperación de contraseña
    """
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'tu_email@ejemplo.com',
            'autocomplete': 'email',
            'autofocus': True
        }),
        help_text='Ingresa el email asociado a tu cuenta.'
    )


class ResetPasswordForm(forms.Form):
    """
    Formulario para establecer nueva contraseña
    """
    password_nueva = forms.CharField(
        label='Nueva contraseña',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nueva contraseña',
            'autocomplete': 'new-password'
        }),
        help_text='''
        Tu contraseña debe contener:
        • Al menos 8 caracteres
        • Al menos una letra mayúscula
        • Al menos una letra minúscula
        • Al menos un número
        • Al menos un carácter especial (@$!%*?&)
        '''
    )
    
    password_confirmacion = forms.CharField(
        label='Confirmar nueva contraseña',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirmar nueva contraseña',
            'autocomplete': 'new-password'
        })
    )
    
    def clean_password_nueva(self):
        """Valida que la nueva contraseña cumpla con los requisitos"""
        password = self.cleaned_data.get('password_nueva')
        
        if len(password) < 8:
            raise ValidationError('La contraseña debe tener al menos 8 caracteres.')
        
        if not re.search(r'[A-Z]', password):
            raise ValidationError('La contraseña debe contener al menos una letra mayúscula.')
        
        if not re.search(r'[a-z]', password):
            raise ValidationError('La contraseña debe contener al menos una letra minúscula.')
        
        if not re.search(r'\d', password):
            raise ValidationError('La contraseña debe contener al menos un número.')
        
        if not re.search(r'[@$!%*?&]', password):
            raise ValidationError('La contraseña debe contener al menos un carácter especial (@$!%*?&).')
        
        return password
    
    def clean(self):
        """Valida que las contraseñas coincidan"""
        cleaned_data = super().clean()
        password_nueva = cleaned_data.get('password_nueva')
        password_confirmacion = cleaned_data.get('password_confirmacion')
        
        if password_nueva and password_confirmacion:
            if password_nueva != password_confirmacion:
                raise ValidationError('Las contraseñas no coinciden.')
        
        return cleaned_data


class ContactoForm(forms.Form):
    """
    Formulario de contacto para la página principal
    """
    nombre = forms.CharField(
        label='Nombre',
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nombre',
            'autocomplete': 'name'
        })
    )
    
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email',
            'autocomplete': 'email'
        })
    )
    
    mensaje = forms.CharField(
        label='Mensaje',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Escribe tu mensaje aquí...',
            'rows': 5
        })
    )
    
    def clean_mensaje(self):
        """Valida que el mensaje tenga contenido suficiente"""
        mensaje = self.cleaned_data.get('mensaje')
        if len(mensaje) < 10:
            raise ValidationError('El mensaje debe tener al menos 10 caracteres.')
        return mensaje


class ContratarProductoForm(forms.ModelForm):
    """
    Formulario para contratar un producto financiero
    """
    monto_invertido = forms.DecimalField(
        label='Monto a invertir (€)',
        max_digits=12,
        decimal_places=2,
        min_value=100,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '1000.00',
            'step': '0.01'
        }),
        help_text='Monto mínimo: €100.00'
    )
    
    acepto_riesgos = forms.BooleanField(
        label='Entiendo y acepto los riesgos de inversión',
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    class Meta:
        model = ProductoContratado
        fields = ['producto', 'monto_invertido']
        widgets = {
            'producto': forms.Select(attrs={
                'class': 'form-control'
            })
        }
    
    def clean_monto_invertido(self):
        """Valida el monto mínimo de inversión"""
        monto = self.cleaned_data.get('monto_invertido')
        if monto < 100:
            raise ValidationError('El monto mínimo de inversión es €100.00')
        return monto


class ActualizarPerfilForm(forms.ModelForm):
    """
    Formulario para actualizar el perfil del usuario
    """
    class Meta:
        model = Usuario
        fields = ['first_name', 'last_name', 'telefono']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Apellidos'
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+34 600 000 000'
            })
        }


class CambiarPasswordForm(forms.Form):
    """
    Formulario para cambiar la contraseña del usuario
    """
    password_actual = forms.CharField(
        label='Contraseña actual',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Contraseña actual',
            'autocomplete': 'current-password'
        })
    )
    
    password_nueva = forms.CharField(
        label='Nueva contraseña',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nueva contraseña',
            'autocomplete': 'new-password'
        }),
        help_text='''
        Tu contraseña debe contener:
        • Al menos 8 caracteres
        • Al menos una letra mayúscula
        • Al menos una letra minúscula
        • Al menos un número
        • Al menos un carácter especial (@$!%*?&)
        '''
    )
    
    password_confirmacion = forms.CharField(
        label='Confirmar nueva contraseña',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirmar nueva contraseña',
            'autocomplete': 'new-password'
        })
    )
    
    def clean_password_nueva(self):
        """Valida que la nueva contraseña cumpla con los requisitos"""
        password = self.cleaned_data.get('password_nueva')
        
        if len(password) < 8:
            raise ValidationError('La contraseña debe tener al menos 8 caracteres.')
        
        if not re.search(r'[A-Z]', password):
            raise ValidationError('La contraseña debe contener al menos una letra mayúscula.')
        
        if not re.search(r'[a-z]', password):
            raise ValidationError('La contraseña debe contener al menos una letra minúscula.')
        
        if not re.search(r'\d', password):
            raise ValidationError('La contraseña debe contener al menos un número.')
        
        if not re.search(r'[@$!%*?&]', password):
            raise ValidationError('La contraseña debe contener al menos un carácter especial (@$!%*?&).')
        
        return password
    
    def clean(self):
        """Valida que las contraseñas coincidan"""
        cleaned_data = super().clean()
        password_nueva = cleaned_data.get('password_nueva')
        password_confirmacion = cleaned_data.get('password_confirmacion')
        
        if password_nueva and password_confirmacion:
            if password_nueva != password_confirmacion:
                raise ValidationError('Las contraseñas no coinciden.')
        
        return cleaned_data