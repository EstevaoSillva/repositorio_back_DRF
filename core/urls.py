from django.urls import path, include
from rest_framework.routers import DefaultRouter
from core.views import UserInfoView, RegisterView, LoginView, AtivarContaView, VeiculoViewSet, HodometroViewSet, AbastecimentoViewSet, TrocaDeOleoViewSet

# Criação do roteador padrão
router = DefaultRouter()

# Registro de rotas para os ViewSets (apenas para ViewSets)
router.register(r'veiculos', VeiculoViewSet, basename='veiculos')
router.register(r'hodometros', HodometroViewSet, basename='hodometros')
router.register(r'abastecimentos', AbastecimentoViewSet, basename='abastecimentos')
router.register(r'trocas_de_oleo', TrocaDeOleoViewSet, basename='trocas_de_oleo')

# Definição das URLs
urlpatterns = [
    path('api/', include(router.urls)),  
    path('api/register/', RegisterView.as_view(), name='register'),  
    path('api/login/', LoginView.as_view(), name='login'),
    path('api/user/', UserInfoView.as_view(), name='user-info'),
    path('ativar/<str:token>/', AtivarContaView.as_view(), name='ativar-conta'),
]
