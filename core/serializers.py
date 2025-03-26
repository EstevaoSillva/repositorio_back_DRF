from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from rest_framework.exceptions import ValidationError
from rest_framework.fields import ChoiceField
from rest_framework_simplejwt.tokens import RefreshToken

from django.utils import timezone
from django.utils.timezone import now
from django.db import transaction
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.hashers import make_password
from django.core.validators import EmailValidator
from django.core.exceptions import ValidationError

from core.models import (Usuario, Veiculo, Hodometro, 
Abastecimento, TrocaDeOleo, Servico)
from core.behaviors import (HodometroBehavior, AbastecimentoBehavior, 
TrocaDeOleoBehavior, ServicoBehavior)
from core.utils import carregar_veiculos

from decimal import Decimal, InvalidOperation, ROUND_DOWN
import re


Usuario = get_user_model()

class UsuarioCadastroSerializer(serializers.ModelSerializer):
    """
    Serializer para registro de usuário com confirmação de senha.

    Campos:
        username (str): Nome de usuário do novo usuário.
        email (str): Email do novo usuário.
        password (str): Senha do novo usuário.
        confirmacao_senha (str): Confirmação da senha do novo usuário.
    """

    confirmacao_senha = serializers.CharField(write_only=True, required=True)

    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        error_messages={"required": "A senha é obrigatória."}
    )

    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=Usuario.objects.all(), message="Este email já está cadastrado.")],
        error_messages={
            'required': 'O email é obrigatório.',
            'invalid': 'Informe um endereço de email válido.',
        }
    )

    class Meta:
        model = Usuario
        fields = ['username', 'email', 'password', 'confirmacao_senha']

    def validate(self, data):
        """
        Valida se as senhas coincidem.
        """
        senha = data.get('password')
        confirmacao_senha = data.get('confirmacao_senha')

        if senha != confirmacao_senha:
            raise serializers.ValidationError({"confirmacao_senha": "As senhas não coincidem."})
        
        return data

    def create(self, validated_data):
        """
        Cria o usuário corretamente, removendo a confirmação de senha.
        """
        validated_data.pop('confirmacao_senha')  
        return Usuario.objects.create_user(**validated_data)

class VeiculoChoiceField(ChoiceField):
    def __init__(self, **kwargs):
        super().__init__(choices=self.get_veiculo_choices(), **kwargs)

    def get_veiculo_choices(self):
        veiculos = carregar_veiculos()
        # Formata os veículos para o formato de choices do ChoiceField
        return [(self.veiculo_to_string(veiculo), f"{veiculo['marca']} {veiculo['modelo']}") for veiculo in veiculos]

    def veiculo_to_string(self, veiculo):
        # Converte o veículo em uma string hashable
        return f"{veiculo['marca']}-{veiculo['modelo']}"

    def to_internal_value(self, data):
        # Converte a string selecionada de volta para o objeto do veículo
        veiculos = carregar_veiculos()
        for veiculo in veiculos:
            if self.veiculo_to_string(veiculo) == data:
                return veiculo
        self.fail('invalid_choice', input=data)

class VeiculoSerializer(serializers.ModelSerializer):

    usuario = serializers.PrimaryKeyRelatedField(queryset=Usuario.objects.all(), required=True)
    usuario_nome = serializers.SerializerMethodField()
    veiculo_selecionado = VeiculoChoiceField(required=False, write_only=True) 

    class Meta:
        model = Veiculo
        fields = [
            'id', 
            'usuario_id',
            'usuario_nome', 
            'usuario', 
            'marca',
            'modelo',
            'capacidade_tanque',
            'veiculo_selecionado',
            'placa',
            'cor', 
            'ano', 
        ]

    def get_usuario_nome(self, obj):
        return obj.usuario.username  

    def validate_ano(self, value):
        """Valida o ano do veículo."""
        ano_atual = now().year
        if not (1886 <= value <= ano_atual):
            raise serializers.ValidationError(f"O ano deve estar entre 1886 e {ano_atual}.")
        return value

    def validate_placa(self, value):
        """Valida o formato da placa."""
        padrao_antigo = r'(?i)^[a-z]{3}\d{4}$'  # ABC1234
        padrao_mercosul = r'(?i)^[a-z]{3}\d[a-z]\d{2}$'  # ABC1D23
        if not (re.match(padrao_antigo, value) or re.match(padrao_mercosul, value)):
            raise serializers.ValidationError("A placa deve estar no formato ABC1234 ou ABC1D23.")
        return value.upper()

    def validate_cor(self, value):
        """Valida a cor do veículo."""
        cores_validas = ['Preto', 'Branco', 'Prata', 'Vermelho', 'Azul', 'Cinza', 'Amarelo', 'Verde']
        if value.capitalize() not in cores_validas:
            raise serializers.ValidationError(f"A cor deve ser uma das seguintes: {', '.join(cores_validas)}.")
        return value.title()

    def validate_veiculo_selecionado(self, value):
        """Valida se o veículo selecionado está na lista disponível."""
        try:
            veiculos_disponiveis = carregar_veiculos()
            if value not in veiculos_disponiveis:
                raise serializers.ValidationError("Veículo selecionado não está na lista disponível.")
            return value
        except Exception as e:
            raise serializers.ValidationError(f"Erro ao carregar veículos: {str(e)}")

    def validate_litros(self, litros):
            """Valida se o total de litros não excede a capacidade do tanque."""
            veiculo = self.initial_data.get('veiculo')
            if veiculo:
                try:
                    veiculo_obj = Veiculo.objects.get(pk=veiculo)
                    capacidade_tanque = veiculo_obj.capacidade_tanque
                    if litros > capacidade_tanque:
                        raise serializers.ValidationError(
                            f"O total de litros ({litros}) excede a capacidade do tanque ({capacidade_tanque})."
                        )
                except Veiculo.DoesNotExist:
                    raise serializers.ValidationError("Veículo não encontrado.")
            return litros

    def validate(self, data):
        """Valida dados gerais do veículo."""
        placa = data.get('placa')

        # Verifica unicidade, excluindo o veículo atual em caso de atualização
        if self.instance:  # Atualização de veículo
            if Veiculo.objects.exclude(id=self.instance.id).filter(placa=placa, is_deleted=False).exists():
                raise serializers.ValidationError({"placa": "Já existe um veículo registrado com esta placa."})
        else:  # Novo registro
            if Veiculo.objects.filter(placa=placa, is_deleted=False).exists():
                raise serializers.ValidationError({"placa": "Já existe um veículo registrado com esta placa."})

        return data


    def create(self, validated_data):
        if self.instance:
            # Lógica para atualização (ignora veiculo_selecionado)
            # Remove veiculo_selecionado dos validated_data se existir
            validated_data.pop('veiculo_selecionado', None) 
            # Atualiza o veículo existente com os dados validados
            for attr, value in validated_data.items(): # Para cada atributo e valor no validated_data
                setattr(self.instance, attr, value) # Atualiza o atributo do veículo
            self.instance.save()
            return self.instance
        else:
            # Lógica para criação com veiculo_selecionado
            usuario = self.context['request'].user
            veiculo_selecionado = validated_data.pop('veiculo_selecionado')
            cor = validated_data.pop('cor')
            placa = validated_data.pop('placa')
            ano = validated_data.pop('ano')
            veiculo = Veiculo.objects.create(
                usuario=usuario,
                marca=veiculo_selecionado['marca'],
                modelo=veiculo_selecionado['modelo'],
                ano=ano,
                capacidade_tanque=veiculo_selecionado['capacidade_tanque'],
                cor=cor,
                placa=placa
            )
            return veiculo

    def update_is_deleted(self, veiculo, is_deleted):
        """Desativa o veículo (soft delete)"""
        veiculo.is_deleted = is_deleted
        veiculo.save()
        return veiculo

    def update_activate_status(self, veiculo, status):
        """Ativa ou desativa o veículo alterando o status de exclusão lógica."""
        veiculo.is_deleted = not status  # Se status for False, marca como excluído
        veiculo.save()
        return veiculo


        """Ativa o veículo"""
        veiculo.activate = status
        veiculo.save()
        return veiculo

class HodometroSerializer(serializers.ModelSerializer):

    data_registro = serializers.DateTimeField(source='last_modified_at', read_only=True, format="%d/%m/%Y - %H:%M")
    usuario_nome = serializers.SerializerMethodField()
    placa_veiculo = serializers.SerializerMethodField()

    class Meta:
        model = Hodometro
        fields = [
            'id',
            'veiculo',
            'placa_veiculo',
            'hodometro',
            'hodometro_diferenca',
            'data_registro',
            'usuario_nome',
            'usuario'
        ]
        read_only_fields = ['hodometro_diferenca', 'usuario', 'data_registro']

    def get_placa_veiculo(self, obj):
        return obj.veiculo.placa

    def get_usuario_nome(self, obj):
        return obj.usuario.username

    def validate(self, data):

        veiculo = data.get('veiculo')
        hodometro = data.get('hodometro')

        if not veiculo:
            raise serializers.ValidationError({"veiculo": "Campo veículo é obrigatório."})

        if hodometro is None:
            raise serializers.ValidationError({"hodometro": "Campo hodômetro é obrigatório."})

        # Obtém o último registro de hodômetro para o veículo
        ultimo_registro = Hodometro.objects.filter(veiculo=veiculo).order_by('-hodometro').first()

        if ultimo_registro and hodometro < ultimo_registro.hodometro:
            raise serializers.ValidationError({"hodometro": "O valor do hodômetro não pode ser menor que o último registro."})

        return data

    def create(self, validated_data):
        veiculo = validated_data.get('veiculo')
        usuario = self.context['request'].user
        hodometro = validated_data.get('hodometro')

        ultimo_registro = Hodometro.objects.filter(veiculo=veiculo).order_by('-hodometro').first()

        hodometro_diferenca = None
        if ultimo_registro:
            hodometro_diferenca = HodometroBehavior.calcular_diferenca(veiculo, hodometro)


        return HodometroBehavior.inicializar_hodometro(
            usuario=usuario,
            veiculo=veiculo,
            hodometro=hodometro,
            hodometro_diferenca=hodometro_diferenca
        )

    def update(self, instance, validated_data):
        hodometro = validated_data.get('hodometro', instance.hodometro)

        if hodometro < instance.hodometro:
            raise serializers.ValidationError({"hodometro": "O valor do hodômetro não pode ser menor que o atual."})

        # Calcula a diferença de hodômetro
        instance.hodometro_diferenca = HodometroBehavior.calcular_diferenca(instance.hodometro, hodometro)
        instance.hodometro = hodometro
        instance.save()

        return instance

class AbastecimentoSerializer(serializers.ModelSerializer):
    data_abastecimento = serializers.DateTimeField(required=False, allow_null=True, format="%d/%m/%Y - %H:%M", default=timezone.now)
    veiculo = serializers.PrimaryKeyRelatedField(queryset=Veiculo.objects.all(), required=True)
    hodometro = serializers.IntegerField(required=True)
    dias_entre_abastecimentos = serializers.SerializerMethodField()
    litros_por_dia = serializers.SerializerMethodField()
    km_dias = serializers.SerializerMethodField()
    total_gasto_abastecimento = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    sugestao_proximo_abastecimento = serializers.SerializerMethodField()

    class Meta:
        model = Abastecimento
        fields = [
            'id',
            'veiculo',
            'hodometro',
            'hodometro_diferenca',
            'total_litros',
            'preco_combustivel',
            'preco_total',
            'desempenho_veiculo',
            'data_abastecimento',
            'dias_entre_abastecimentos',
            'litros_por_dia',
            'km_dias',
            'total_gasto_abastecimento',
            'sugestao_proximo_abastecimento'
        ]
        read_only_fields = ['preco_total', 'desempenho_veiculo', 'hodometro_diferenca', 'dias_entre_abastecimentos',
                            'litros_por_dia', 'km_dias', 'total_gasto_abastecimento', 'sugestao_proximo_abastecimento']

    def get_total_gasto_abastecimento(self, obj):
        return AbastecimentoBehavior.calcular_total_gasto_abastecimento(obj.preco_total, obj.veiculo)

    def get_km_dias(self, obj):
        return AbastecimentoBehavior.km_dias(obj.hodometro_diferenca, self.get_dias_entre_abastecimentos(obj))

    def get_litros_por_dia(self, obj):
        return AbastecimentoBehavior.calcular_litros_por_dia(obj.total_litros, self.get_dias_entre_abastecimentos(obj))

    def get_dias_entre_abastecimentos(self, obj):
        ultimo_abastecimento = Abastecimento.objects.filter(veiculo=obj.veiculo, id__lt=obj.id).order_by(
            '-data_abastecimento').first()
        if ultimo_abastecimento and obj.data_abastecimento:
            return AbastecimentoBehavior.calcular_diferenca_dias(obj.data_abastecimento,
                                                                 ultimo_abastecimento.data_abastecimento)
        return None

    def get_sugestao_proximo_abastecimento(self, obj):
        return AbastecimentoBehavior.sugerir_novo_abastecimento(obj.veiculo)

    def validate(self, data):
        veiculo = data.get('veiculo')
        novo_hodometro = data.get('hodometro')
        data_abastecimento = data.get('data_abastecimento')
        # self.validate_litros(data.get('total_litros'))

        # Obter o último registro de hodômetro
        ultimo_hodometro = Hodometro.objects.filter(veiculo=veiculo).order_by('-id').first()
        ultimo_valor_hodometro = ultimo_hodometro.hodometro if ultimo_hodometro else 0

        # Validar o novo valor do hodômetro com base na diferença
        if novo_hodometro < ultimo_valor_hodometro:
            raise serializers.ValidationError({
                "hodometro": f"O valor do hodômetro ({novo_hodometro}) não pode ser menor que o último registrado ({ultimo_valor_hodometro})."
            })

        # Validação de data futura
        if data_abastecimento and data_abastecimento > timezone.now():
            raise serializers.ValidationError({
                "data_abastecimento": "Não é permitido registrar abastecimentos com datas futuras."
            })

        # Validação de data anterior ao último abastecimento
        if veiculo and data_abastecimento:
            if Abastecimento.objects.filter(veiculo=veiculo).exists():
                ultimo_abastecimento = Abastecimento.objects.filter(veiculo=veiculo).latest('data_abastecimento')
                if data_abastecimento < ultimo_abastecimento.data_abastecimento:
                    raise serializers.ValidationError({
                        "data_abastecimento": f"Não é permitido registrar abastecimentos com datas anteriores ao último abastecimento registrado. Último abastecimento: {ultimo_abastecimento.data_abastecimento.strftime('%d/%m/%Y %H:%M')}."
                    })

        return data

    def create(self, validated_data):
        veiculo = validated_data['veiculo']
        total_litros = validated_data['total_litros']
        preco_combustivel = validated_data['preco_combustivel']
        usuario = self.context['request'].user
        hodometro = validated_data['hodometro']
        print(f"Veículo: {veiculo}")
        print(f"Total de litros: {total_litros}")
        print(f"Preço do combustível: {preco_combustivel}")
        print(f"Usuário: {usuario}")
        print(f"Hodômetro: {hodometro}")

        # Calcular a diferença do hodômetro com o Behavior para o abastecimento
        abast_hodometro_diferenca = AbastecimentoBehavior.calcular_diferenca_hodometro(veiculo, hodometro)

        # Calcular a diferença de hodômetro com o Behavior de Hodometro
        new_hodometro_diferenca = HodometroBehavior.calcular_diferenca(veiculo, hodometro)

        # Calcular o preço total com o Behavior
        preco_total = AbastecimentoBehavior.calcular_preco_total(total_litros, preco_combustivel)

        # Criar o registro do abastecimento
        abastecimento = Abastecimento.objects.create(
            veiculo=veiculo,
            total_litros=total_litros,
            hodometro=hodometro,
            preco_combustivel=preco_combustivel,
            preco_total=preco_total,
            hodometro_diferenca=abast_hodometro_diferenca,
            data_abastecimento=validated_data.get('data_abastecimento', timezone.now()),
            usuario=usuario
        )

        # Criar o novo registro de Hodômetro
        Hodometro.objects.create(
            veiculo=veiculo,
            hodometro=hodometro,
            hodometro_diferenca=new_hodometro_diferenca,
            usuario=usuario
        )

        return abastecimento

    def update(self, instance, validated_data):
        veiculo = validated_data.get('veiculo', instance.veiculo)
        novo_hodometro = validated_data.pop('hodometro', instance.hodometro)
        total_litros = validated_data.get('total_litros', instance.total_litros)
        preco_combustivel = validated_data.get('preco_combustivel', instance.preco_combustivel)
        usuario = self.context['request'].user
        hodometro = self.context['request'].data.get('hodometro')

        # Obter o último valor de hodômetro registrado no veículo
        ultimo_hodometro = Hodometro.objects.filter(veiculo=veiculo).order_by('-id').first()
        ultimo_valor_hodometro = ultimo_hodometro.hodometro if ultimo_hodometro else 0

        if novo_hodometro != instance.hodometro:
            # Validar o novo hodômetro com o Behavior
            if not HodometroBehavior.validar_hodometro(ultimo_valor_hodometro, novo_hodometro):
                raise serializers.ValidationError({
                    "hodometro": f"O valor do hodômetro ({novo_hodometro}) não pode ser menor que o último registrado ({ultimo_valor_hodometro})."
                })

            # Calcular a diferença do hodômetro com o Behavior
            hodometro_diferenca = AbastecimentoBehavior.calcular_diferenca_hodometro(veiculo, novo_hodometro)

            # Calcular a diferença de hodômetro com o Behavior de Hodometro
            new_hodometro_diferenca = HodometroBehavior.calcular_diferenca(veiculo, hodometro)

            # Criar um novo registro de Hodômetro
            Hodometro.objects.create(
                veiculo=veiculo,
                hodometro=novo_hodometro,
                hodometro_diferenca=new_hodometro_diferenca,
                usuario=usuario
            )

            # Atualizar o campo de diferença no abastecimento
            instance.hodometro_diferenca = hodometro_diferenca
            instance.save()

        return instance 

class TrocaDeOleoSerializer(serializers.ModelSerializer):
    """
    Serializer para o modelo TrocaDeOleo.
    """

    proximo_hodometro = serializers.SerializerMethodField()
    proxima_data = serializers.SerializerMethodField()

    class Meta:
        model = TrocaDeOleo
        fields = [
            'id',
            'veiculo',
            'usuario',
            'hodometro',
            'tipo_oleo',
            'data_troca',
            'proximo_hodometro',
            'proxima_data',
        ]
        read_only_fields = ['proximo_hodometro', 'proxima_data']

    def get_proximo_hodometro(self, obj):
        proximo_hodometro, _ = TrocaDeOleoBehavior.calcular_proxima_troca(obj)
        return proximo_hodometro

    def get_proxima_data(self, obj):
        _, proxima_data = TrocaDeOleoBehavior.calcular_proxima_troca(obj)
        return proxima_data

    def create(self, validated_data):
        """Cria um novo registro de troca de óleo."""
        troca = TrocaDeOleo.objects.create(**validated_data)
        return troca

    def update(self, instance, validated_data):
        """Atualiza um registro de troca de óleo existente."""
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

class ServicoSerializer(serializers.ModelSerializer):
    """
    Serializer para o modelo Servico.
    """

    usuario_nome = serializers.SerializerMethodField()
    veiculo_placa = serializers.SerializerMethodField()
    custo_total = serializers.SerializerMethodField()

    class Meta:
        model = Servico
        fields = [
            'id',
            'veiculo',
            'veiculo_placa',
            'usuario',
            'usuario_nome',
            'nome',
            'descricao',
            'data_agendamento',
            'concluido',
            'custo',
            'custo_total',
        ]
        read_only_fields = ['custo_total']

    def get_usuario_nome(self, obj):
        return obj.usuario.username

    def get_veiculo_placa(self, obj):
        return obj.veiculo.placa

    def get_custo_total(self, obj):
        return ServicoBehavior.calcular_custo_total(obj)

    def validate_nome(self, value):
        """Valida o nome do serviço."""
        return value.title()

    def validate(self, data):
        """Valida dados gerais do serviço."""
        # Adicione validações adicionais conforme necessário
        return data

    def create(self, validated_data):
        """Cria um novo serviço."""
        servico = Servico.objects.create(**validated_data)
        ServicoBehavior.enviar_notificacao_agendamento(servico)
        ServicoBehavior.registrar_historico_servico(servico)
        return servico

    def update(self, instance, validated_data):
        """Atualiza um serviço existente."""
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance