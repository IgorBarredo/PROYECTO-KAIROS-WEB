from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

Usuario = get_user_model()


class EmailBackend(ModelBackend):
    """
    Backend de autenticación personalizado que permite login con email o username
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            # Intentar buscar por email primero
            try:
                user = Usuario.objects.get(email=username)
            except Usuario.DoesNotExist:
                # Si no existe por email, intentar por username
                user = Usuario.objects.get(username=username)
        except Usuario.DoesNotExist:
            return None
        
        # Verificar contraseña
        if user.check_password(password):
            return user
        return None
    
    def get_user(self, user_id):
        try:
            return Usuario.objects.get(pk=user_id)
        except Usuario.DoesNotExist:
            return None