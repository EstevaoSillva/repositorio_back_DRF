from django.core.mail import send_mail
from django.conf import settings

def enviar_email_ativacao(email, token):
    assunto = "Ativação da sua conta"
    mensagem = f"Olá! Clique no link abaixo para ativar sua conta:\n\n"
    mensagem += f"http://localhost:8000/api/ativar/{token}/"
    
    send_mail(assunto, mensagem, settings.EMAIL_HOST_USER, [email])
