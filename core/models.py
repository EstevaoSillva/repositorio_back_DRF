from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from django.conf import settings
from decimal import Decimal
from django.utils import timezone

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
    is_deleted = models.BooleanField(db_column='is_deleted', default=False, null=False)

    class Meta:
        db_table = 'veiculos'
        

    def __str__(self):
        return f"ID:{self.id} - Modelo: {self.modelo} - Placa: {self.placa} - Usuário: {self.usuario}"

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

    class Meta:
        db_table = 'abastecimentos'
        verbose_name = 'Abastecimento'
        verbose_name_plural = 'Abastecimentos'
        ordering = ['data_abastecimento']
        constraints = [
            models.UniqueConstraint(fields=['veiculo', 'data_abastecimento'], name='abastecimento_por_veiculo_e_data')
        ]

    def __str__(self):
        return f"Abastecimento em {self.data_abastecimento} | Veículo {getattr(self.veiculo, 'placa', 'Sem placa')}"

    def save(self, *args, **kwargs):
        from core.behaviors import AbastecimentoBehavior
        import logging

        logger = logging.getLogger(__name__)

        logger.debug(f"Salvando abastecimento - Veículo: {self.veiculo}")

        # Calcular a diferença do hodômetro com o Behavior
        if self.veiculo:
            ultimo_abastecimento = Hodometro.objects.filter(veiculo=self.veiculo).order_by('-id').first()
            logger.debug(f"Último hodômetro: {ultimo_abastecimento.hodometro if ultimo_abastecimento else 'Nenhum'}")

            if ultimo_abastecimento:
                self.hodometro_diferenca = AbastecimentoBehavior.calcular_diferenca(
                    self.hodometro, ultimo_abastecimento.hodometro
                )
            else:
                self.hodometro_diferenca = 0

        logger.debug(f"Hodômetro diferença calculado: {self.hodometro_diferenca}")

        self.preco_total = AbastecimentoBehavior.calcular_preco_total(self.total_litros, self.preco_combustivel)
        logger.debug(f"Preço total calculado: {self.preco_total}")

        if self.preco_total >= Decimal("1000.00"):
            self.preco_total = Decimal("999.99")

        # Corrigido: Passando self.veiculo em vez de self.total_litros
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

