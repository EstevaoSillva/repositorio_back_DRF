from django.core.exceptions import ValidationError
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth.models import AnonymousUser
from django.db.models import Sum
from django.utils import timezone
from django.db import models
from django.conf import settings

from rest_framework.response import Response
from rest_framework import status

from decimal import Decimal, ROUND_DOWN
from datetime import timedelta, datetime

from core.models import Hodometro, Abastecimento, Veiculo, TrocaDeOleo, TipoOleo, Servico

import logging

# Configuração do Logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

class HodometroBehavior:

    @staticmethod
    def calcular_diferenca(veiculo, hodometro_atual):

        # Obtendo o primeiro registro de hodômetro do veículo
        registro_inicial = Hodometro.objects.filter(veiculo=veiculo).order_by('id').first()
        hodometro_inicial = registro_inicial.hodometro if registro_inicial else 0
        print(f"Registro inicial: {registro_inicial}")
        print(f"Hodômetro inicial: {hodometro_inicial}")

        # Convertendo os valores para Decimal antes de realizar a subtração
        hodometro_atual = Decimal(str(hodometro_atual)) if not isinstance(hodometro_atual, (int, float, Decimal)) else hodometro_atual
        hodometro_inicial = Decimal(str(hodometro_inicial)) if not isinstance(hodometro_inicial, (int, float, Decimal)) else hodometro_inicial
        print(f"Valores convertidos para Decimal: hodometro_atual={hodometro_atual}, hodometro_inicial={hodometro_inicial}")

        # Garantindo que os valores sejam do tipo correto
        if not isinstance(hodometro_atual, (int, float, Decimal)):
            raise ValueError("O hodômetro deve ser um número válido.")

        # Calculando e retornando a diferença
        return hodometro_atual - hodometro_inicial

    @staticmethod
    def obter_valor_ultimo_hodometro(veiculo):
        """
        Obtém o valor do último hodômetro registrado para o veículo.
        Retorna o valor do hodômetro ou None se não houver registros.
        """
        ultimo_registro = Hodometro.objects.filter(veiculo=veiculo).order_by('-id').first()
        return ultimo_registro.hodometro if ultimo_registro else None

    @staticmethod
    def inicializar_hodometro(usuario, veiculo, hodometro, hodometro_diferenca=None):
        return Hodometro.objects.create(
            usuario=usuario,
            veiculo=veiculo,
            hodometro=hodometro,
            hodometro_diferenca=hodometro_diferenca
        )

    @staticmethod
    def atualizar_hodometro(veiculo, novo_hodometro, usuario):
        """
        Atualiza o hodômetro de um veículo e sincroniza automaticamente os registros de abastecimento e troca de óleo.
        """
        with transaction.atomic():  # Garantir atomicidade da transação
            ultimo_hodometro = Hodometro.objects.filter(veiculo=veiculo).order_by('-id').first()
            ultimo_valor_hodometro = ultimo_hodometro.hodometro if ultimo_hodometro else 0

            if novo_hodometro < ultimo_valor_hodometro:
                raise ValueError(f"O hodômetro ({novo_hodometro}) não pode ser menor que o último registrado ({ultimo_valor_hodometro}).")

            hodometro_diferenca = novo_hodometro - ultimo_valor_hodometro

            # Criar novo registro de Hodômetro
            novo_registro = Hodometro.objects.create(
                veiculo=veiculo,
                hodometro=novo_hodometro,
                hodometro_diferenca=hodometro_diferenca,
                usuario=usuario
            )

            # Atualizando a última troca de óleo
            TrocaDeOleo.objects.filter(veiculo=veiculo, hodometro__lt=novo_hodometro).order_by('-data_troca').update(hodometro=novo_hodometro)

            # Atualizando o último abastecimento
            Abastecimento.objects.filter(veiculo=veiculo, hodometro__lt=novo_hodometro).order_by('-data_abastecimento').update(hodometro=novo_hodometro)

        return novo_registro

    @staticmethod
    def validar_hodometro(hodometro_atual, veiculo):
        """
        Valida o valor do hodômetro atual em relação ao último registro.
        """
        if not isinstance(hodometro_atual, int):
            raise ValueError("O hodômetro atual deve ser um valor inteiro.")

        hodometro_inicial = HodometroBehavior.obter_valor_ultimo_hodometro(veiculo)
        if hodometro_inicial and hodometro_atual < hodometro_inicial:
            raise ValueError("O hodômetro atual não pode ser menor que o último registro.")

class AbastecimentoBehavior:
    """
    Classe para encapsular lógica de negócio relacionada aos abastecimentos.
    """

    @staticmethod
    def calcular_diferenca_hodometro(veiculo, novo_hodometro):
        """
        Calcula a diferença do hodômetro com base no último registro.
        """

        print("inicio calcular diferenca em abastecimentobeahavior")
        print(f"Veículo consultado: {veiculo}")
        ultimo_hodometro = Hodometro.objects.filter(veiculo=veiculo).order_by('-id').first()
        if ultimo_hodometro:
            ultimo_valor_hodometro = ultimo_hodometro.hodometro
            print(f"Último registro encontrado: {ultimo_hodometro.id}") 
        else:
            ultimo_valor_hodometro = 0
        print(f"Último hodômetro : {ultimo_valor_hodometro}")
        print(f"Novo hodômetro: {novo_hodometro}")
        print(f"Diferença: {novo_hodometro - ultimo_valor_hodometro}")
        print("fim calcular diferenca em abastecimentobeahavior")

        return novo_hodometro - ultimo_valor_hodometro

    @staticmethod
    def calcular_preco_total(total_litros, preco_combustivel):
        """
        Calcula o preço total do abastecimento.
        """
        if total_litros and preco_combustivel:
            preco_total = total_litros * preco_combustivel
            preco_total = Decimal(preco_total).quantize(Decimal('0.01'), rounding=ROUND_DOWN)

            # Limitar a 999.99
            if preco_total >= Decimal('1000.00'):
                return Decimal('999.99')

            return preco_total

        return Decimal('0.00')

    @staticmethod
    def calcular_consumo_medio(hodometro_diferenca, veiculo):
        """Calcula o desempenho do veículo (km/l)."""
        ultimo_abastecimento = AbastecimentoBehavior.obter_ultimo_abastecimento(veiculo)
        if not ultimo_abastecimento or not ultimo_abastecimento.total_litros:
            return None

        try:
            consumo_medio = hodometro_diferenca / ultimo_abastecimento.total_litros
            return Decimal(consumo_medio).quantize(Decimal('0.01'))
        except Exception as e:
            logging.error(f"Erro ao calcular o consumo médio: {e}")
            return None

    @staticmethod
    def calcular_total_gasto_abastecimento(total_pago, veiculo):
        """
        Calcula o total gasto com abastecimento.
        """
        if not isinstance(veiculo, Veiculo):
            raise ValueError(f"Erro: veiculo não é um objeto Veiculo. Tipo recebido: {type(veiculo)} - Valor: {veiculo}")

        if not isinstance(total_pago, (Decimal, float, int)):
            raise ValueError(f"Erro: total_pago deve ser um número. Tipo recebido: {type(total_pago)} - Valor: {total_pago}")

        ultimo_abastecimento = AbastecimentoBehavior.obter_ultimo_abastecimento(veiculo)
        total_anterior = ultimo_abastecimento.total_gasto_abastecimento if ultimo_abastecimento else Decimal('0.00')
        return total_anterior + Decimal(str(total_pago))

    @staticmethod
    def obter_ultimo_abastecimento(veiculo):
        if not isinstance(veiculo, Veiculo):
            raise ValueError(f"Erro: veiculo não é um objeto Veiculo. Tipo recebido: {type(veiculo)} - Valor: {veiculo}")

        return Abastecimento.objects.filter(veiculo=veiculo).order_by('-id').first()

    @staticmethod
    def calcular_diferenca_dias(data_atual, data_anterior):
        """
        Calcula a diferença em dias entre duas datas.
        """
        if not data_atual or not data_anterior:
            raise ValueError("Ambas as datas devem ser fornecidas para calcular a diferença.")

        return (data_atual - data_anterior).days

    @staticmethod
    def calcular_litros_por_dia(total_litros, dias_entre_abastecimentos):
        """
        Calcula os litros consumidos por dia, dado o total de litros abastecidos
        e os dias entre abastecimentos.
        """
        if dias_entre_abastecimentos and dias_entre_abastecimentos > 0:
            litros_por_dia = total_litros / dias_entre_abastecimentos
            litros_por_dia = Decimal(litros_por_dia).quantize(Decimal('0.01'), rounding=ROUND_DOWN)
            return litros_por_dia
        return None

    @staticmethod
    def km_dias(diferenca_km, dias_percorridos):
        """
        Calcula a quilometragem por dia, dado a quilometragem total e o número de dias.
        """
        if diferenca_km is not None and dias_percorridos is not None and diferenca_km > 0 and dias_percorridos > 0:
            km_dias = diferenca_km / dias_percorridos
            km_dias = Decimal(km_dias).quantize(Decimal('0'), rounding=ROUND_DOWN)
            return km_dias
        return None  # Retorna None caso qualquer valor seja inválido

    @staticmethod
    def sugerir_novo_abastecimento(veiculo):
        """
        Sugere um novo abastecimento com base no consumo diário e na capacidade do tanque.
        """
        ultimo_abastecimento = AbastecimentoBehavior.obter_ultimo_abastecimento(veiculo)
        if not ultimo_abastecimento or not ultimo_abastecimento.litros_por_dia:
            return None

        capacidade_tanque = veiculo.capacidade_tanque
        dias_restantes = capacidade_tanque / ultimo_abastecimento.litros_por_dia
        proximo_abastecimento = ultimo_abastecimento.data_abastecimento + timedelta(days=int(dias_restantes))
        return proximo_abastecimento

class TrocaDeOleoBehavior:

    @staticmethod
    def calcular_proxima_troca(ultima_troca):
        """
        Calcula a próxima troca de óleo com base no tipo de óleo utilizado.
        """
        if not ultima_troca:
            return None, None  # Retorna None se não houver uma troca anterior

        km_intervalo = 5000 if ultima_troca.tipo_oleo == 'mineral' else 10000
        proximo_hodometro = ultima_troca.hodometro + km_intervalo
        proxima_data = ultima_troca.data_troca + timedelta(days=180)  # 6 meses

        return proximo_hodometro, proxima_data

    @staticmethod
    def verificar_alertas(veiculo, novo_hodometro):
        """
        Verifica se há alertas a serem emitidos com base na quilometragem e na data da última troca.
        """
        ultima_troca = TrocaDeOleo.objects.filter(veiculo=veiculo).order_by('-data_troca').first()
        if not ultima_troca:
            return None  # Sem alertas se não houver uma troca registrada

        proximo_hodometro, proxima_data = TrocaDeOleoBehavior.calcular_proxima_troca(ultima_troca)
        alertas = []

        if not proximo_hodometro:
            return None

        # Verificando alerta de quilometragem
        if novo_hodometro >= proximo_hodometro - 500:  # Alerta a partir de 500 km antes da troca
            if novo_hodometro < proximo_hodometro:
                alertas.append(f"Atenção! Falta menos de 500 km para a próxima troca de óleo ({proximo_hodometro} km).")
            else:
                km_excedente = novo_hodometro - proximo_hodometro
                alertas.append(f"Atenção! A troca de óleo está atrasada. Você ultrapassou {km_excedente} km.")

        # Verificando alerta de tempo
        data_atual = timezone.now().date()  # Garante que seja um objeto date
        if proxima_data and isinstance(proxima_data, datetime):
            proxima_data = proxima_data.date()  # Converte datetime para date

        # Formatando a data corretamente
        data_formatada = proxima_data.strftime("%d/%m/%Y - %H:%M")

        if data_atual >= proxima_data - timedelta(days=30):  # Alerta 1 mês antes
            if data_atual < proxima_data:
                alertas.append(f"Atenção! A troca de óleo está próxima da data prevista ({data_formatada}).")
            else:
                dias_atraso = (data_atual.date() - proxima_data.date()).days
                alertas.append(f"A troca de óleo está atrasada em {dias_atraso} dias ({data_formatada}).")

        return alertas

    @staticmethod
    def registrar_troca(usuario, veiculo, hodometro, tipo_oleo):
        """
        Registra uma nova troca de óleo e calcula a próxima troca.
        """
        troca = TrocaDeOleo.objects.create(
            usuario=usuario,
            veiculo=veiculo,
            hodometro=hodometro,
            tipo_oleo=tipo_oleo,
            data_troca=timezone.now()
        )
        return troca


class ServicoBehavior:
    @staticmethod
    def verificar_conclusao(servico):
        """
        Verifica se um serviço foi concluído.
        """
        return servico.concluido

    @staticmethod
    def agendar_proximo_servico(servico):
        """
        Agenda o próximo serviço com base no tipo de serviço e na data de conclusão.
        """
        if servico.concluido:
            if servico.nome == "Troca de Óleo":
                proxima_data = servico.data_agendamento + timedelta(days=180)  # 6 meses
                return proxima_data
            elif servico.nome == "Revisão Geral":
                proxima_data = servico.data_agendamento + timedelta(days=365)  # 1 ano
                return proxima_data
            # Adicione outras lógicas de agendamento conforme necessário
        return None

    @staticmethod
    def calcular_custo_total(servico):
        """
        Calcula o custo total do serviço, considerando possíveis taxas adicionais.
        """
        custo_base = servico.custo or 0  # Se o custo não estiver definido, use 0
        taxa_adicional = 0.1 * custo_base  # Exemplo: taxa adicional de 10%
        return custo_base + taxa_adicional

    @staticmethod
    def enviar_notificacao_agendamento(servico):
        """
        Envia uma notificação ao usuário sobre o agendamento do serviço.
        (Implementação fictícia, você precisará adaptar para o seu sistema de notificação)
        """
        usuario = servico.usuario
        mensagem = f"Seu serviço '{servico.nome}' foi agendado para {servico.data_agendamento}."
        print(f"Notificação para {usuario.username}: {mensagem}")
        # Aqui você implementaria a lógica para enviar a notificação (email, push, etc.)

    @staticmethod
    def registrar_historico_servico(servico):
        """
        Registra o histórico do serviço em um log ou tabela de histórico.
        (Implementação fictícia, você precisará adaptar para o seu sistema de log)
        """
        print(f"Histórico: Serviço '{servico.nome}' realizado em {servico.data_agendamento}.")
        # Aqui você implementaria a lógica para registrar o histórico do serviço