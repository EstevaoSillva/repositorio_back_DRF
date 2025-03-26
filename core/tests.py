from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from .models import Veiculo, Hodometro, Usuario
from .serializers import HodometroSerializer
from django.contrib.auth.models import User

class HodometroTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = Usuario.objects.create_user(username='estevao', email='estevaovsilva@gmail.com', password='Abcd1234') 
        self.client.force_authenticate(user=self.user)
        self.veiculo = Veiculo.objects.create(
            usuario=self.user,
            placa="ABC1234",
            marca="Marca Teste",
            modelo="Modelo Teste",
            cor="Cor Teste",
            ano=2023
        )

    def test_criar_hodometro_sucesso(self):
        data = {'veiculo': self.veiculo.id, 'hodometro': 100}
        response = self.client.post('/hodometros/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED) #Verifica se o Status Code está correto.
        self.assertEqual(Hodometro.objects.count(), 1)
        self.assertEqual(Hodometro.objects.first().hodometro, 100)
        self.assertEqual(Hodometro.objects.first().usuario, self.user) #Verifica se o usuario foi salvo.

    def test_criar_hodometro_valor_invalido(self):
        Hodometro.objects.create(veiculo=self.veiculo, hodometro=100)
        data = {'veiculo': self.veiculo.id, 'hodometro': 50}
        response = self.client.post('/hodometros/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('hodometro', response.data)

    def test_atualizar_hodometro_sucesso(self):
        hodometro = Hodometro.objects.create(veiculo=self.veiculo, hodometro=100)
        data = {'veiculo': self.veiculo.id, 'hodometro': 200}
        response = self.client.put(f'/hodometros/{hodometro.id}/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Hodometro.objects.get(id=hodometro.id).hodometro, 200)

    def test_atualizar_hodometro_valor_invalido(self):
        hodometro = Hodometro.objects.create(veiculo=self.veiculo, hodometro=100)
        data = {'veiculo': self.veiculo.id, 'hodometro': 50}
        response = self.client.put(f'/hodometros/{hodometro.id}/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('hodometro', response.data)

    def test_serializer_validacao_hodometro(self):
        Hodometro.objects.create(veiculo=self.veiculo, hodometro=100)
        data = {'veiculo': self.veiculo.id, 'hodometro': 50}
        serializer = HodometroSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('hodometro', serializer.errors)