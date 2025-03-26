import json
import random

# Lista de veículos original
veiculos = [
    { "marca": "Chevrolet", "modelo": "Onix", "capacidade_tanque": 44 },
    { "marca": "Chevrolet", "modelo": "S10", "capacidade_tanque": 76 },
    { "marca": "Chevrolet", "modelo": "Cruze", "capacidade_tanque": 52 },
    { "marca": "Chevrolet", "modelo": "Tracker", "capacidade_tanque": 44 },
    { "marca": "Chevrolet", "modelo": "Spin", "capacidade_tanque": 53 },
    { "marca": "Chevrolet", "modelo": "Prisma", "capacidade_tanque": 54 },
    { "marca": "Chevrolet", "modelo": "Montana", "capacidade_tanque": 56 },
    { "marca": "Chevrolet", "modelo": "Equinox", "capacidade_tanque": 59 },
    { "marca": "Chevrolet", "modelo": "Trailblazer", "capacidade_tanque": 73 },
    { "marca": "Chevrolet", "modelo": "Cobalt", "capacidade_tanque": 54 },
    { "marca": "Chevrolet", "modelo": "Sonic", "capacidade_tanque": 46 },
    { "marca": "Chevrolet", "modelo": "Captiva", "capacidade_tanque": 65 },
    { "marca": "Chevrolet", "modelo": "Agile", "capacidade_tanque": 54 },
    { "marca": "Fiat", "modelo": "Toro", "capacidade_tanque": 60 },
    { "marca": "Fiat", "modelo": "Argo", "capacidade_tanque": 48 },
    { "marca": "Fiat", "modelo": "Strada", "capacidade_tanque": 55 },
    { "marca": "Fiat", "modelo": "Mobi", "capacidade_tanque": 47 },
    { "marca": "Fiat", "modelo": "Cronos", "capacidade_tanque": 48 },
    { "marca": "Fiat", "modelo": "Pulse", "capacidade_tanque": 47 },
    { "marca": "Fiat", "modelo": "Grand Siena", "capacidade_tanque": 52 },
    { "marca": "Fiat", "modelo": "Punto", "capacidade_tanque": 60 },
    { "marca": "Fiat", "modelo": "Bravo", "capacidade_tanque": 57 },
    { "marca": "Fiat", "modelo": "Linea", "capacidade_tanque": 60 },
    { "marca": "Fiat", "modelo": "Palio Weekend", "capacidade_tanque": 51 },
    { "marca": "Fiat", "modelo": "Idea", "capacidade_tanque": 48 },
    { "marca": "Fiat", "modelo": "Doblò", "capacidade_tanque": 60 },
    { "marca": "Fiat", "modelo": "Freemont", "capacidade_tanque": 77 },
    { "marca": "Fiat", "modelo": "500", "capacidade_tanque": 35 },
    { "marca": "Fiat", "modelo": "500X", "capacidade_tanque": 48 },
    { "marca": "Fiat", "modelo": "Tipo", "capacidade_tanque": 50 },
    { "marca": "Fiat", "modelo": "Palio", "capacidade_tanque": 48 },  
    { "marca": "Honda", "modelo": "Civic", "capacidade_tanque": 47 },
    { "marca": "Honda", "modelo": "HR-V", "capacidade_tanque": 50 },
    { "marca": "Honda", "modelo": "Fit", "capacidade_tanque": 46 },
    { "marca": "Honda", "modelo": "City", "capacidade_tanque": 48 },
    { "marca": "Honda", "modelo": "WR-V", "capacidade_tanque": 45 },
    { "marca": "Honda", "modelo": "CR-V", "capacidade_tanque": 57 },
    { "marca": "Honda", "modelo": "Accord", "capacidade_tanque": 56 },
    { "marca": "Honda", "modelo": "Pilot", "capacidade_tanque": 73 },
    { "marca": "Honda", "modelo": "Insight", "capacidade_tanque": 40 },
    { "marca": "Honda", "modelo": "Clarity", "capacidade_tanque": 48 },
    { "marca": "Honda", "modelo": "e", "capacidade_tanque": 35 },
    { "marca": "Volkswagen", "modelo": "Gol", "capacidade_tanque": 55 },
    { "marca": "Volkswagen", "modelo": "Amarok", "capacidade_tanque": 80 },
    { "marca": "Volkswagen", "modelo": "Polo", "capacidade_tanque": 52 },
    { "marca": "Volkswagen", "modelo": "T-Cross", "capacidade_tanque": 52 },
    { "marca": "Volkswagen", "modelo": "Virtus", "capacidade_tanque": 52 },
    { "marca": "Volkswagen", "modelo": "Nivus", "capacidade_tanque": 52 },
    { "marca": "Volkswagen", "modelo": "Taos", "capacidade_tanque": 50 },
    { "marca": "Volkswagen", "modelo": "Saveiro", "capacidade_tanque": 55 },
    { "marca": "Volkswagen", "modelo": "Voyage", "capacidade_tanque": 55 },
    { "marca": "Volkswagen", "modelo": "Jetta", "capacidade_tanque": 50 },
    { "marca": "Volkswagen", "modelo": "Golf", "capacidade_tanque": 51 },
    { "marca": "Volkswagen", "modelo": "Passat", "capacidade_tanque": 66 },
    { "marca": "Volkswagen", "modelo": "Tiguan", "capacidade_tanque": 60 },
    { "marca": "Volkswagen", "modelo": "Up!", "capacidade_tanque": 50 }
]

# Adicionando IDs sequenciais
for i, veiculo in enumerate(veiculos):
    veiculo['id'] = i + 1

# Salvando o JSON atualizado em um arquivo
with open('veiculos_com_id.json', 'w', encoding='utf-8') as f:
    json.dump(veiculos, f, ensure_ascii=False, indent=4)

print("IDs adicionados e arquivo 'veiculos_com_id.json' criado com sucesso!")