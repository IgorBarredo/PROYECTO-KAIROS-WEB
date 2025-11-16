from django.urls import path
from . import views

app_name = 'appKairos'

urlpatterns = [
    # Páginas públicas
    path('', views.index_view, name='index'),
    path('how-we-work/', views.how_we_work_view, name='how_we_work'),
    path('connect-mt5/', views.connect_mt5_view, name='connect_mt5'),
    path('newsletter/', views.newsletter_view, name='newsletter'),
    path('contacto/', views.contacto_view, name='contacto'),
    
    # Autenticación
    path('register/', views.registro_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Verificación de email
    path('verify-email-sent/', views.verify_email_sent_view, name='verify_email_sent'),
    path('verify-email/<str:token>/', views.verificar_email_view, name='verificar_email'),
    path('resend-verification/', views.reenviar_verificacion_view, name='reenviar_verificacion'),
    
    # Recuperación de contraseña
    path('solicitar-recuperacion/', views.solicitar_recuperacion_view, name='solicitar_recuperacion'),
    path('recuperacion-enviada/', views.recuperacion_enviada_view, name='recuperacion_enviada'),
    path('reset-password/<str:token>/', views.reset_password_view, name='reset_password'),
    
    # 2FA
    path('activar-2fa/', views.activar_2fa_view, name='activar_2fa'),
    path('mostrar-codigos-respaldo/', views.mostrar_codigos_respaldo_view, name='mostrar_codigos_respaldo'),
    path('verificar-2fa/', views.verificar_2fa_view, name='verificar_2fa'),
    path('desactivar-2fa/', views.desactivar_2fa_view, name='desactivar_2fa'),
    
    # Dashboard y perfil
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('perfil/', views.perfil_view, name='perfil'),
    path('cambiar-password/', views.cambiar_password_view, name='cambiar_password'),
    
    # Productos
    path('contratar-producto/<int:producto_id>/', views.contratar_producto_view, name='contratar_producto'),
    path('cancelar-producto/<int:contrato_id>/', views.cancelar_producto_view, name='cancelar_producto'),
]