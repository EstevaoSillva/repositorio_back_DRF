from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth import login, authenticate
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ValidationError
from django.conf import settings  
import os
import json

from rest_framework.exceptions import ValidationError
from rest_framework import viewsets, permissions, status
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView

from rest_framework import generics
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth import get_user_model
from core.utils import enviar_email_ativacao

from django.shortcuts import get_object_or_404
from rest_framework.response import Response

from core import pagination
from core.models import Usuario, Veiculo, Hodometro, Abastecimento, TrocaDeOleo, Servico
from core.serializers import (
    UsuarioCadastroSerializer,VeiculoSerializer, HodometroSerializer, 
    AbastecimentoSerializer, TrocaDeOleoSerializer, ServicoSerializer
)
from core.filters import UsuarioFilter, VeiculoFilter, HodometroFilter, AbastecimentoFilter,TrocaDeOleoFilter
from core.behaviors import HodometroBehavior, AbastecimentoBehavior
from core.utils import carregar_veiculos

import logging

logger = logging.getLogger(__name__)

Usuario = get_user_model()

class UserInfoView(APIView):
    permission_classes = [IsAuthenticated]  # Somente usuários autenticados podem acessar

    def get(self, request):
        user = request.user  # Obtém o usuário autenticado
        user_data = {
            'id': user.id,
            'email': user.email,
            'nome': user.username,  
        }
        return Response(user_data)

class RegisterView(APIView):
    """
    View para registrar um novo usuário.
    """

    queryset = Usuario.objects.all()
    serializer_class = UsuarioCadastroSerializer
    permission_classes = [AllowAny]


    def post(self, request):

        serializer = UsuarioCadastroSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Usuário cadastrado com sucesso!"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    """
    View para autenticação do usuário e geração de tokens JWT.
    """
    permission_classes = [AllowAny]  # Permite acesso público

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        usuario = authenticate(email=email, password=password)
        if usuario is not None:
            refresh = RefreshToken.for_user(usuario)
            return Response({
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "usuario": {  
                    "id": usuario.id
                }
            }, status=status.HTTP_200_OK)
        
        return Response({"error": "Credenciais inválidas!"}, status=status.HTTP_401_UNAUTHORIZED)

class AtivarContaView(APIView):
    def get(self, request, token):
        user = get_object_or_404(Usuario, is_active=False)
        
        if default_token_generator.check_token(user, token):
            user.is_active = True
            user.save()
            return Response({"message": "Conta ativada com sucesso!"})
        
        return Response({"error": "Token inválido ou expirado."}, status=400)

class VeiculoViewSet(viewsets.ModelViewSet):

    queryset = Veiculo.objects.filter(is_deleted=False)
    serializer_class = VeiculoSerializer
    permission_classes = (permissions.IsAuthenticated,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = VeiculoFilter

    def create(self, request, *args, **kwargs):
        logger.info("Requisição POST recebida para cadastrar veículo")
        logger.info(f"Dados recebidos: {request.data}")

        usuario_id = request.data.get('usuario')
        marca = request.data.get('marca')
        modelo = request.data.get('modelo')
        capacidade_tanque = request.data.get('capacidade_tanque')
        placa = request.data.get('placa')
        cor = request.data.get('cor')
        ano = request.data.get('ano')

        print(f"Dados recebidos: {request.data}") 

        try:
            usuario = Usuario.objects.get(id=usuario_id)
        except User.DoesNotExist:
            return Response({'error': 'Usuário não encontrado.'}, status=status.HTTP_400_BAD_REQUEST)

        veiculo = Veiculo.objects.create(
            usuario=usuario,
            marca=marca,
            modelo=modelo,
            ano=ano,
            capacidade_tanque=capacidade_tanque,
            cor=cor,
            placa=placa
        )
        
        return Response({'message': 'Veículo cadastrado com sucesso.'}, status=status.HTTP_201_CREATED)


    def destroy(self, request, *args, **kwargs):
        veiculo = self.get_object()  # Obtém o veículo atual
        # Evita a exclusão permanente, marca o veículo como deletado (soft delete)
        if veiculo.is_deleted:
            return Response({"detail": "Veículo já está desativado."}, status=status.HTTP_400_BAD_REQUEST)
        
        veiculo.is_deleted = True
        veiculo.save()
        return Response({"detail": "Veículo desativado com sucesso."}, status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        veiculo = self.get_object()  # Obtém o veículo atual
        veiculo.is_deleted = False
        veiculo.save()
        return Response({"detail": "Veículo ativado com sucesso."}, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([AllowAny])
def veiculos_json(request):
    """Retorna os dados do arquivo veiculos.json."""
    try:
        # Construa o caminho completo para o arquivo veiculos.json
        file_path = os.path.join(settings.BASE_DIR, 'core', 'data', 'veiculos_com_id.json')

        with open(file_path, 'r') as f:
            veiculos = json.load(f)
        return Response(veiculos)
    except FileNotFoundError:
        return Response({"error": "Arquivo veiculos.json não encontrado."}, status=404)
    except json.JSONDecodeError:
        return Response({"error": "Erro ao decodificar arquivo veiculos.json."}, status=500)

@api_view(['PATCH'])
def reativar_veiculo(request, pk):
    try:
        veiculo = Veiculo.objects.get(pk=pk)
    except Veiculo.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    serializer = VeiculoSerializer(veiculo, data={'status': True}, partial=True)
    if serializer.is_valid():
        serializer.update_activate_status(veiculo, True) # Reativa o veículo
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class HodometroViewSet(viewsets.ModelViewSet):
    queryset = Hodometro.objects.all()
    serializer_class = HodometroSerializer
    permission_classes = (permissions.IsAuthenticated,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = HodometroFilter

    def get_queryset(self):
        """
        Filtra para mostrar apenas os hodômetros do usuário autenticado
        """
        return Hodometro.objects.filter(usuario=self.request.user)

class AbastecimentoViewSet(viewsets.ModelViewSet):

    queryset = Abastecimento.objects.all()
    serializer_class = AbastecimentoSerializer
    permission_classes = (permissions.IsAuthenticated,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = AbastecimentoFilter

    def get_queryset(self):
        
        """
        Retorna apenas os abastecimentos do usuário autenticado.
        """
        usuario = self.request.user
        return Abastecimento.objects.filter(veiculo__usuario=usuario)

    def perform_create(self, serializer):
        """
        Trata a criação de um abastecimento, garantindo que o usuário esteja associado.
        """
        # Obtém o usuário autenticado
        usuario = self.request.user

        # Cria o abastecimento associando o usuário ao registro
        serializer.save(usuario=usuario)

class TrocaDeOleoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para o modelo TrocaDeOleo.
    """
    queryset = TrocaDeOleo.objects.all()
    serializer_class = TrocaDeOleoSerializer
    permission_classes = (permissions.IsAuthenticated,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = TrocaDeOleoFilter

    def get_queryset(self):
        """
        Retorna as trocas de óleo do usuário autenticado.
        """
        return TrocaDeOleo.objects.filter(usuario=self.request.user)

    def perform_create(self, serializer):
        """
        Salva a troca de óleo com o usuário autenticado.
        """
        serializer.save(usuario=self.request.user)

    def create(self, request, *args, **kwargs):
        """
        Cria um novo registro de troca de óleo e lida com erros de validação.
        """
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        """
        Atualiza um registro de troca de óleo e lida com erros de validação.
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ServicoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para o modelo Servico.
    """
    queryset = Servico.objects.all()
    serializer_class = ServicoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Retorna os serviços do usuário autenticado.
        """
        return Servico.objects.filter(usuario=self.request.user)

    def perform_create(self, serializer):
        """
        Salva o serviço com o usuário autenticado.
        """
        serializer.save(usuario=self.request.user)