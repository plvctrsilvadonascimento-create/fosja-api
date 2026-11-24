# treinar.py - treino próprio, sem API

import torch
import torch.nn as nn
from tokenizer import TokenizerFOSJA
from modelo import CerebroFOSJA

tok = TokenizerFOSJA()
tok.treinar("dataset.txt")

# Prepara os dados do teu dataset
with open("dataset.txt", "r", encoding="utf-8") as f:
    linhas = [l.strip() for l in f if l.strip()]

dados = [tok.codificar(l) for l in linhas]
max_len = max(len(d) for d in dados)
dados = [d + [0]*(max_len - len(d)) for d in dados]
dados = torch.tensor(dados)

modelo = CerebroFOSJA(len(tok.palavra_para_id))
otimizador = torch.optim.Adam(modelo.parameters(), lr=0.001)
perda_fn = nn.CrossEntropyLoss(ignore_index=0)

print("Começando treino da FOSJA...")
for epoca in range(500):
    modelo.train()
    otimizador.zero_grad()
    entrada = dados[:, :-1]
    alvo = dados[:, 1:]
    saida = modelo(entrada)
    perda = perda_fn(saida.reshape(-1, saida.shape[-1]), alvo.reshape(-1))
    perda.backward()
    otimizador.step()
    if epoca % 50 == 0:
        print(f"Epoca {epoca} - Perda: {perda.item():.4f}")

torch.save({"modelo": modelo.state_dict(), "vocab": tok.palavra_para_id}, "cerebro.pt")
print("Pronto! Cérebro salvo em cerebro.pt")
