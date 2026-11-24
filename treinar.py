import torch
import torch.nn as nn
import random
from modelo import FosjaTransformer
from tokenizer import Tokenizer

random.seed(42)
torch.manual_seed(42)
tokenizer = Tokenizer()
tokenizer.carregar("dataset.txt")
with open("dataset.txt", encoding="utf-8") as f:
    linhas = [l.strip() for l in f if l.strip()]
pares = []
for i in range(len(linhas) - 1):
    pares.append((linhas[i], linhas[i + 1]))
    pares.append((linhas[i] + " " + linhas[i + 1], linhas[i + 1]))
todos_ids = []
for a, b in pares:
    ids_a = tokenizer.codificar(a)
    ids_b = tokenizer.codificar(b)
    todos_ids.append(ids_a + ids_b + [tokenizer.fim_id])
random.shuffle(todos_ids)
split = int(len(todos_ids) * 0.9)
treino = todos_ids[:split]
valid = todos_ids[split:]
modelo = FosjaTransformer(len(tokenizer.vocab))
otimizador = torch.optim.AdamW(modelo.parameters(), lr=0.0003, weight_decay=0.01, betas=(0.9, 0.98), eps=1e-9)
scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(otimizador, T_max=500)
perda_fn = nn.CrossEntropyLoss(ignore_index=tokenizer.pad_id, label_smoothing=0.05)
modelo.train()
melhor = float("inf")
paciente = 0
for epoca in range(500):
    random.shuffle(treino)
    total = 0
    total_n = 0
    for seq in treino:
        for i in range(0, max(1, len(seq) - 128), 64):
            x = torch.tensor([seq[i:i + 128]], dtype=torch.long)
            y = torch.tensor([seq[i + 1:i + 129]], dtype=torch.long)
            if y.size(1) < 2:
                continue
            if x.size(1) != y.size(1):
                n = min(x.size(1), y.size(1))
                x = x[:, :n]
                y = y[:, :n]
            saida = modelo(x)
            perda = perda_fn(saida.view(-1, len(tokenizer.vocab)), y.view(-1))
            otimizador.zero_grad()
            perda.backward()
            torch.nn.utils.clip_grad_norm_(modelo.parameters(), 1.0)
            otimizador.step()
            total += perda.item()
            total_n += 1
    scheduler.step()
    modelo.eval()
    v_total = 0
    v_n = 0
    with torch.no_grad():
        for seq in valid[:200]:
            x = torch.tensor([seq[:-1]], dtype=torch.long)
            y = torch.tensor([seq[1:]], dtype=torch.long)
            if x.size(1) != y.size(1):
                n = min(x.size(1), y.size(1))
                x = x[:, :n]
                y = y[:, :n]
            saida = modelo(x)
            v_total += perda_fn(saida.view(-1, len(tokenizer.vocab)), y.view(-1)).item()
            v_n += 1
    v_media = v_total / max(1, v_n)
    print(epoca, total / max(1, total_n), v_media)
    if v_media < melhor:
        melhor = v_media
        paciente = 0
        torch.save(modelo.state_dict(), "cerebro.pt")
    else:
        paciente += 1
        if paciente >= 25:
            break
    modelo.train()
torch.save(modelo.state_dict(), "cerebro.pt")
