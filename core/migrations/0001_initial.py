# Generated by Django 5.1.3 on 2025-03-24 22:32

import django.contrib.auth.models
import django.contrib.auth.validators
import django.db.models.deletion
import django.utils.timezone
from decimal import Decimal
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='Usuario',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('username', models.CharField(error_messages={'unique': 'A user with that username already exists.'}, help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.', max_length=150, unique=True, validators=[django.contrib.auth.validators.UnicodeUsernameValidator()], verbose_name='username')),
                ('first_name', models.CharField(blank=True, max_length=150, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=150, verbose_name='last name')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('telefone', models.CharField(blank=True, max_length=15, null=True)),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions')),
            ],
            options={
                'verbose_name': 'user',
                'verbose_name_plural': 'users',
                'abstract': False,
            },
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='Veiculo',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_column='created_at')),
                ('modified_at', models.DateTimeField(auto_now=True, db_column='modified_at')),
                ('activate', models.BooleanField(db_column='activate', default=True)),
                ('placa', models.CharField(db_column='placa', max_length=7, unique=True, verbose_name='Placa')),
                ('marca', models.CharField(db_column='marca', max_length=255, verbose_name='Marca')),
                ('modelo', models.CharField(db_column='modelo', max_length=255, verbose_name='Modelo')),
                ('cor', models.CharField(db_column='cor', max_length=255, verbose_name='Cor')),
                ('ano', models.IntegerField(db_column='ano', verbose_name='Ano')),
                ('capacidade_tanque', models.DecimalField(db_column='capacidade_tanque', decimal_places=2, max_digits=10, verbose_name='Capacidade do Tanque')),
                ('is_deleted', models.BooleanField(db_column='is_deleted', default=False)),
                ('usuario', models.ForeignKey(db_column='usuario_id', on_delete=django.db.models.deletion.CASCADE, related_name='veiculos', to=settings.AUTH_USER_MODEL, verbose_name='Usuário')),
            ],
            options={
                'db_table': 'veiculos',
            },
        ),
        migrations.CreateModel(
            name='Servico',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_column='created_at')),
                ('modified_at', models.DateTimeField(auto_now=True, db_column='modified_at')),
                ('activate', models.BooleanField(db_column='activate', default=True)),
                ('nome', models.CharField(db_column='nome', max_length=255, verbose_name='Nome do Serviço')),
                ('descricao', models.TextField(blank=True, db_column='descricao', null=True, verbose_name='Descrição')),
                ('data_agendamento', models.DateTimeField(blank=True, db_column='data_agendamento', null=True, verbose_name='Data de Agendamento')),
                ('concluido', models.BooleanField(db_column='concluido', default=False, verbose_name='Concluído')),
                ('custo', models.DecimalField(blank=True, db_column='custo', decimal_places=2, max_digits=10, null=True, verbose_name='Custo')),
                ('usuario', models.ForeignKey(db_column='usuario_id', on_delete=django.db.models.deletion.CASCADE, related_name='servicos', to=settings.AUTH_USER_MODEL, verbose_name='Usuário')),
                ('veiculo', models.ForeignKey(db_column='veiculo_id', on_delete=django.db.models.deletion.CASCADE, related_name='servicos', to='core.veiculo', verbose_name='Veículo')),
            ],
            options={
                'verbose_name': 'Serviço',
                'verbose_name_plural': 'Serviços',
                'db_table': 'servicos',
            },
        ),
        migrations.CreateModel(
            name='TrocaDeOleo',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_column='created_at')),
                ('modified_at', models.DateTimeField(auto_now=True, db_column='modified_at')),
                ('activate', models.BooleanField(db_column='activate', default=True)),
                ('hodometro', models.PositiveIntegerField(db_column='hodometro', verbose_name='Hodômetro na Troca')),
                ('hodometro_diferenca', models.PositiveIntegerField(blank=True, db_column='hodometro_diferenca', null=True, verbose_name='Diferença de Hodômetro')),
                ('tipo_oleo', models.CharField(choices=[('5K', 'Óleo para 5.000 km'), ('10K', 'Óleo para 10.000 km')], db_column='tipo_oleo', max_length=3, verbose_name='Tipo de Óleo')),
                ('data_troca', models.DateTimeField(db_column='data_troca', verbose_name='Data da Troca')),
                ('custo_total', models.DecimalField(db_column='custo_total', decimal_places=2, max_digits=10, verbose_name='Custo Total')),
                ('usuario', models.ForeignKey(db_column='usuario_id', on_delete=django.db.models.deletion.CASCADE, related_name='trocas_de_oleo', to=settings.AUTH_USER_MODEL, verbose_name='Usuário')),
                ('veiculo', models.ForeignKey(db_column='veiculo_id', on_delete=django.db.models.deletion.CASCADE, related_name='trocas_de_oleo', to='core.veiculo', verbose_name='Veículo')),
            ],
            options={
                'verbose_name': 'Troca de Óleo',
                'verbose_name_plural': 'Trocas de Óleo',
                'db_table': 'trocas_de_oleo',
                'ordering': ['-data_troca'],
                'constraints': [models.UniqueConstraint(fields=('veiculo', 'data_troca'), name='troca_por_veiculo_e_data')],
            },
        ),
        migrations.CreateModel(
            name='Hodometro',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_column='created_at')),
                ('modified_at', models.DateTimeField(auto_now=True, db_column='modified_at')),
                ('activate', models.BooleanField(db_column='activate', default=True)),
                ('hodometro', models.PositiveIntegerField(db_column='hodometro_inicial', verbose_name='Hodômetro Inicial')),
                ('hodometro_diferenca', models.PositiveIntegerField(blank=True, db_column='hodometro_diferenca', null=True, verbose_name='Diferenca')),
                ('last_modified_at', models.DateTimeField(auto_now=True, null=True)),
                ('last_modified_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='modified_hodometros', to=settings.AUTH_USER_MODEL)),
                ('usuario', models.ForeignKey(db_column='usuario_id', on_delete=django.db.models.deletion.CASCADE, related_name='hodometros', to=settings.AUTH_USER_MODEL)),
                ('veiculo', models.ForeignKey(db_column='veiculo_id', on_delete=django.db.models.deletion.CASCADE, related_name='hodometros', to='core.veiculo')),
            ],
            options={
                'db_table': 'hodometros',
                'indexes': [models.Index(fields=['veiculo'], name='hodometros_veiculo_a46080_idx'), models.Index(fields=['usuario'], name='hodometros_usuario_70dc62_idx'), models.Index(fields=['hodometro'], name='hodometros_hodomet_896b6d_idx')],
            },
        ),
        migrations.CreateModel(
            name='Abastecimento',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_column='created_at')),
                ('modified_at', models.DateTimeField(auto_now=True, db_column='modified_at')),
                ('activate', models.BooleanField(db_column='activate', default=True)),
                ('hodometro', models.PositiveIntegerField(db_column='hodometro', verbose_name='Hodômetro')),
                ('hodometro_diferenca', models.PositiveIntegerField(blank=True, db_column='hodometro_diferenca', null=True, verbose_name='Diferenca')),
                ('desempenho_veiculo', models.DecimalField(blank=True, db_column='desempenho_veiculo', decimal_places=2, max_digits=10, null=True, verbose_name='Desempenho do Veículo')),
                ('preco_combustivel', models.DecimalField(db_column='preco_combustivel', decimal_places=2, max_digits=10, verbose_name='Preço do Combustível')),
                ('total_litros', models.DecimalField(db_column='total_litros', decimal_places=2, max_digits=10, verbose_name='Total de Litros')),
                ('preco_total', models.DecimalField(db_column='preco_total', decimal_places=2, max_digits=10, verbose_name='Preço Total')),
                ('data_abastecimento', models.DateTimeField(db_column='data_abastecimento', verbose_name='Data do Abastecimento')),
                ('total_gasto_abastecimento', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=10)),
                ('litros_por_dia', models.DecimalField(db_column='litros_por_dia', decimal_places=2, default=Decimal('0.00'), max_digits=10, verbose_name='Litros por Dia')),
                ('usuario', models.ForeignKey(db_column='usuario_id', on_delete=django.db.models.deletion.CASCADE, related_name='abastecimentos', to=settings.AUTH_USER_MODEL, verbose_name='Usuário')),
                ('veiculo', models.ForeignKey(db_column='veiculo_id', on_delete=django.db.models.deletion.CASCADE, related_name='abastecimentos', to='core.veiculo', verbose_name='Veículo')),
            ],
            options={
                'verbose_name': 'Abastecimento',
                'verbose_name_plural': 'Abastecimentos',
                'db_table': 'abastecimentos',
                'ordering': ['data_abastecimento'],
                'constraints': [models.UniqueConstraint(fields=('veiculo', 'data_abastecimento'), name='abastecimento_por_veiculo_e_data')],
            },
        ),
    ]
