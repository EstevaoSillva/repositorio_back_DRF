from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from django.conf import settings
from decimal import Decimal
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models import UniqueConstraint

import logging

# Configuração do Logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

class ModelBase(models.Model):
    """
    Modelo base para fornecer campos de ID, data de criação e modificação para outros modelos.
    """
    id = models.BigAutoField(primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at')
    modified_at = models.DateTimeField(auto_now=True, db_column='modified_at')
    activate = models.BooleanField(db_column='activate', default=True, null=False)

    class Meta:
        abstract = True
        managed = True

class Usuario(AbstractUser):
    """
    Modelo de usuário personalizado.
    """
    email = models.EmailField(unique=True)
    telefone = models.CharField(max_length=15, blank=True, null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'telefone']

    def __str__(self):
        return f"{self.username}"

class Veiculo(ModelBase):
    """
    Representa um veículo do sistema.
    """
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='veiculos', on_delete=models.CASCADE, db_column='usuario_id', verbose_name='Usuário')
    placa = models.CharField(max_length=7, db_column='placa', verbose_name='Placa', unique=True)
    marca = models.CharField(max_length=255, db_column='marca', verbose_name='Marca')
    modelo = models.CharField(max_length=255, db_column='modelo', verbose_name='Modelo')
    cor = models.CharField(max_length=255, db_column='cor', verbose_name='Cor')
    ano = models.IntegerField(db_column='ano', verbose_name='Ano')
    capacidade_tanque = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Capacidade do Tanque', db_column='capacidade_tanque')
    is_deleted = models.BooleanField(db_column='is_deleted', default=False, null=False)

    class Meta:
        db_table = 'veiculos'
        

    def __str__(self):
        return f"ID:{self.id} - Modelo: {self.modelo} - Placa: {self.placa} - Usuário: {self.usuario}"

class Servico(ModelBase):
    """
    Representa um serviço associado a um veículo.
    """

    veiculo = models.ForeignKey(Veiculo, on_delete=models.CASCADE, related_name='servicos', verbose_name='Veículo', db_column='veiculo_id')
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='servicos', verbose_name='Usuário', db_column='usuario_id')
    nome = models.CharField(max_length=255, verbose_name='Nome do Serviço', db_column='nome')
    descricao = models.TextField(verbose_name='Descrição', db_column='descricao', blank=True, null=True)
    data_agendamento = models.DateTimeField(verbose_name='Data de Agendamento', db_column='data_agendamento', null=True, blank=True)
    concluido = models.BooleanField(default=False, verbose_name='Concluído', db_column='concluido')
    custo = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Custo', db_column='custo', null=True, blank=True)

    class Meta:
        db_table = 'servicos'
        verbose_name = 'Serviço'
        verbose_name_plural = 'Serviços'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        # Lógica de agendamento do próximo serviço
        proxima_data = ServicoBehavior.agendar_proximo_servico(self)
        if proxima_data:
            # Crie um novo objeto Servico para o próximo agendamento
            proximo_servico = Servico(
                veiculo=self.veiculo,
                usuario=self.usuario,
                nome=self.nome,
                descricao=self.descricao,
                data_agendamento=proxima_data,
                concluido=False,
                custo=self.custo
            )
            proximo_servico.save()

        # Lógica de notificação de agendamento
        ServicoBehavior.enviar_notificacao_agendamento(self)

        # Lógica de registro de histórico
        ServicoBehavior.registrar_historico_servico(self)

    @property
    def custo_total(self):
        return ServicoBehavior.calcular_custo_total(self)

    def __str__(self):
        return f"{self.nome} - {self.veiculo.placa}"

class Hodometro(ModelBase):
    """
    Representa o controle de hodômetro de um veículo.
    """
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="hodometros", db_column='usuario_id')
    veiculo = models.ForeignKey(Veiculo, on_delete=models.CASCADE, related_name="hodometros", db_column='veiculo_id')
    
    hodometro = models.PositiveIntegerField(verbose_name="Hodômetro Inicial", db_column='hodometro_inicial', null=False)
    hodometro_diferenca = models.PositiveIntegerField(verbose_name="Diferenca", db_column='hodometro_diferenca', null=True, blank=True)
    
    
    # Auditoria
    last_modified_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="modified_hodometros")
    last_modified_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        db_table = 'hodometros'
        # Garantir que não existam duplicatas para (veiculo, usuario, hodometro_inicial)
        indexes = [
            models.Index(fields=['veiculo']),
            models.Index(fields=['usuario']),
            models.Index(fields=['hodometro']),
        ]

    @receiver(post_save, sender=hodometro)
    def atualizar_registros_relacionados(sender, instance, **kwargs):
        """
        Atualiza os registros de manutenção e abastecimento quando o hodômetro é atualizado.
        """
        veiculo = instance.veiculo
        novo_hodometro = instance.hodometro

        # Atualiza as previsões de próximas trocas de óleo
        trocas_de_oleo = TrocaDeOleo.objects.filter(veiculo=veiculo)
        for troca in trocas_de_oleo:
            proximo_hodometro, proxima_data = TrocaDeOleoBehavior.calcular_proxima_troca(troca)
            if proximo_hodometro:
                troca.proximo_hodometro = proximo_hodometro
                troca.proxima_data = proxima_data
                troca.save()

        # Atualiza os registros de abastecimento
        abastecimentos = Abastecimento.objects.filter(veiculo=veiculo)
        for abastecimento in abastecimentos:
            # Recalcula o consumo médio usando a função centralizada
            hodometro_diferenca = HodometroBehavior.calcular_diferenca(veiculo, abastecimento.hodometro)
            abastecimento.desempenho_veiculo = AbastecimentoBehavior.calcular_desempenho_veiculo(hodometro_diferenca, veiculo)
            abastecimento.save()

        # Atualiza outros registros de manutenção (Servico)
        servicos = Servico.objects.filter(veiculo=veiculo)
        for servico in servicos:
            # Lógica para atualizar registros de manutenção, se necessário
            # Exemplo: Atualizar custo total se depender da quilometragem
            custo_total = ServicoBehavior.calcular_custo_total(servico)
            servico.custo = custo_total
            servico.save()

    def __str__(self):
        return f"{self.veiculo} ({self.id})"

class Abastecimento(ModelBase):
    """
    Representa um abastecimento registrado no sistema.
    """

    veiculo = models.ForeignKey(Veiculo, on_delete=models.CASCADE, related_name='abastecimentos', verbose_name='Veículo', db_column='veiculo_id')
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='abastecimentos', verbose_name='Usuário', db_column='usuario_id')
    hodometro = models.PositiveIntegerField(verbose_name='Hodômetro', db_column='hodometro')
    hodometro_diferenca = models.PositiveIntegerField(verbose_name='Diferenca', db_column='hodometro_diferenca', null=True, blank=True)
    desempenho_veiculo = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Desempenho do Veículo', db_column='desempenho_veiculo', null=True, blank=True)
    preco_combustivel = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Preço do Combustível', db_column='preco_combustivel')
    total_litros = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Total de Litros', db_column='total_litros')
    preco_total = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Preço Total', db_column='preco_total')
    data_abastecimento = models.DateTimeField(verbose_name='Data do Abastecimento', db_column='data_abastecimento')
    total_gasto_abastecimento = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    litros_por_dia = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), verbose_name="Litros por Dia", db_column='litros_por_dia')

    class Meta:
        db_table = 'abastecimentos'
        verbose_name = 'Abastecimento'
        verbose_name_plural = 'Abastecimentos'
        ordering = ['data_abastecimento']
        constraints = [
            UniqueConstraint(fields=['veiculo', 'data_abastecimento'], name='abastecimento_por_veiculo_e_data')
        ]

    def __str__(self):
        return f"Abastecimento em {self.data_abastecimento} | Veículo {getattr(self.veiculo, 'placa', 'Sem placa')}"

    def save(self, *args, **kwargs):
        from core.behaviors import AbastecimentoBehavior

        logger = logging.getLogger(__name__)

        logger.debug(f"Salvando abastecimento - Veículo: {self.veiculo}")

        # Obter o último registro de hodômetro para o veículo
        ultimo_hodometro = Hodometro.objects.filter(veiculo=self.veiculo).order_by('-id').first()

        logger.debug(f"Último hodômetro: {ultimo_hodometro.hodometro if ultimo_hodometro else 'Nenhum'}")

        # Calcular a diferença do hodômetro corretamente
        if ultimo_hodometro:
            self.hodometro_diferenca = self.hodometro - ultimo_hodometro.hodometro
        else:
            self.hodometro_diferenca = 0

        logger.debug(f"Hodômetro diferença calculado: {self.hodometro_diferenca}")

        self.preco_total = AbastecimentoBehavior.calcular_preco_total(self.total_litros, self.preco_combustivel)
        logger.debug(f"Preço total calculado: {self.preco_total}")

        if self.preco_total >= Decimal("1000.00"):
            self.preco_total = Decimal("999.99")

        # Usar a função centralizada para calcular o desempenho
        self.desempenho_veiculo = AbastecimentoBehavior.calcular_consumo_medio(self.hodometro_diferenca, self.veiculo)
        logger.debug(f"Consumo médio calculado: {self.desempenho_veiculo}")

        self.total_gasto_abastecimento = AbastecimentoBehavior.calcular_total_gasto_abastecimento(
            self.preco_total,
            self.veiculo
        )

        super().save(*args, **kwargs)


class TipoOleo(models.TextChoices):
    """
    Define os tipos de óleo disponíveis para troca.
    """
    OLEO_5K = '5K', 'Óleo para 5.000 km'
    OLEO_10K = '10K', 'Óleo para 10.000 km'


class TrocaDeOleo(ModelBase):
    """
    Representa uma troca de óleo registrada no sistema.
    """
    veiculo = models.ForeignKey(Veiculo, on_delete=models.CASCADE, related_name='trocas_de_oleo', verbose_name='Veículo', db_column='veiculo_id')
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='trocas_de_oleo', verbose_name='Usuário', db_column='usuario_id')
    hodometro = models.PositiveIntegerField(verbose_name='Hodômetro na Troca', db_column='hodometro')
    hodometro_diferenca = models.PositiveIntegerField(verbose_name='Diferença de Hodômetro', db_column='hodometro_diferenca', null=True, blank=True)
    tipo_oleo = models.CharField(max_length=3, choices=TipoOleo.choices, verbose_name='Tipo de Óleo', db_column='tipo_oleo')
    data_troca = models.DateTimeField(verbose_name='Data da Troca', db_column='data_troca')
    custo_total = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Custo Total', db_column='custo_total')

    class Meta:
        db_table = 'trocas_de_oleo'
        verbose_name = 'Troca de Óleo'
        verbose_name_plural = 'Trocas de Óleo'
        ordering = ['-data_troca']
        constraints = [
            models.UniqueConstraint(fields=['veiculo', 'data_troca'], name='troca_por_veiculo_e_data')
        ]

    def __str__(self):
        return f"Troca de óleo em {self.data_troca} | Veículo {getattr(self.veiculo, 'placa', 'Sem placa')}"

    def save(self, *args, **kwargs):
        from core.behaviors import TrocaDeOleoBehavior

        # Obtém o último hodômetro registrado para o veículo
        ultimo_hodometro = Hodometro.objects.filter(veiculo=self.veiculo).order_by('-id').first()

        if ultimo_hodometro:
            # Calcula a diferença de hodômetro
            self.hodometro_diferenca = self.hodometro - ultimo_hodometro.hodometro
        else:
            # Se for o primeiro registro, a diferença é a própria quilometragem
            self.hodometro_diferenca = self.hodometro

        # Verifica se a troca de óleo é necessária
        if not TrocaDeOleoBehavior.verificar_troca_necessaria(self.veiculo):
            raise ValidationError("Troca de óleo não necessária no momento.")

        # Salva a troca de óleo
        super().save(*args, **kwargs)

        # Atualiza o hodômetro do veículo
        if ultimo_hodometro:
            ultimo_hodometro.hodometro = self.hodometro
            ultimo_hodometro.save()


# class TipoCombustivel(models.TextChoices):
#     GASOLINA = 'GAS', 'Gasolina'
#     ETANOL = 'ETA', 'Etanol'
#     DIESEL = 'DIE', 'Diesel'
#     GNV = 'GNV', 'Gás Natural Veicular'

