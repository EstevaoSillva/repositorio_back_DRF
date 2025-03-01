from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth import login, authenticate
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ValidationError
import json

from rest_framework.exceptions import ValidationError
from rest_framework import viewsets, permissions, status
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import action
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
from core.models import Usuario, Veiculo, Hodometro, Abastecimento, TrocaDeOleo
from core.serializers import UsuarioCadastroSerializer,VeiculoSerializer, HodometroSerializer, AbastecimentoSerializer, TrocaDeOleoSerializer
from core.filters import UsuarioFilter, VeiculoFilter, HodometroFilter, AbastecimentoFilter
from core.behaviors import HodometroBehavior, AbastecimentoBehavior

Usuario = get_user_model()

class UserInfoView(APIView):
    permission_classes = [IsAuthenticated]  # Somente usuários autenticados podem acessar

    def get(self, request):
        user = request.user  # Obtém o usuário autenticado
        user_data = {
            'id': user.id,
            'email': user.email,
            'Nome': user.username,  
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
                "refresh": str(refresh)
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

    queryset = TrocaDeOleo.objects.all()
    serializer_class = TrocaDeOleoSerializer
    permission_classes = (permissions.IsAuthenticated,)
    filter_backends = (DjangoFilterBackend,)
    # filterset_class = TrocaDeOleoFilter