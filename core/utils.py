from django.core.mail import send_mail
from django.conf import settings
import os
import json

def enviar_email_ativacao(email, token):
    assunto = "Ativação da sua conta"
    mensagem = f"Olá! Clique no link abaixo para ativar sua conta:\n\n"
    mensagem += f"http://localhost:8000/api/ativar/{token}/"
    
    send_mail(assunto, mensagem, settings.EMAIL_HOST_USER, [email])


def carregar_veiculos():
    # Caminho para o arquivo veiculos.json
    caminho_arquivo = os.path.join(settings.BASE_DIR, 'core', 'data', 'veiculos_com_id.json')
    
    try:
        with open(caminho_arquivo, 'r', encoding='utf-8') as arquivo:
            veiculos = json.load(arquivo)
            return veiculos
    except FileNotFoundError:
        raise Exception("Arquivo veiculos.json não encontrado.")
    except json.JSONDecodeError:
        raise Exception("Erro ao decodificar o arquivo veiculos.json.")