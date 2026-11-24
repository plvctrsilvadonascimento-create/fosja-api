import torch
import torch.nn as nn
import math
import os
from tokenizer import Tokenizer

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
MODELO = None
TOKENIZER = None

class PositionalEncoding(nn.Module):
    def __init__(self, d_model, max_len=256):
        super().__init__()
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model))
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        self.register_buffer("pe", pe.unsqueeze(0))
    def forward(self, x):
        return x + self.pe[:, :x.size(1), :]

class FosjaTransformer(nn.Module):
    def __init__(self, vocab_size, d_model=512, n_heads=8, num_layers=8, dropout=0.1, max_len=256):
        super().__init__()
        self.d_model = d_model
        self.embedding = nn.Embedding(vocab_size, d_model, padding_idx=1)
        self.pos = PositionalEncoding(d_model, max_len)
        self.dropout = nn.Dropout(dropout)
        encoder_layer = nn.TransformerEncoderLayer(d_model=d_model, nhead=n_heads, dim_feedforward=d_model * 4, dropout=dropout, activation="gelu", batch_first=True, norm_first=True)
        self.transformer_encoder = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        self.norm = nn.LayerNorm(d_model)
        self.fc = nn.Linear(d_model, vocab_size)
        self.fc.weight = self.embedding.weight
    def forward(self, x):
        seq_len = x.size(1)
        mask = torch.triu(torch.ones(seq_len, seq_len, device=x.device), diagonal=1).bool()
        pad_mask = (x == 1)
        x = self.embedding(x) * math.sqrt(self.d_model)
        x = self.pos(x)
        x = self.dropout(x)
        x = self.transformer_encoder(x, mask=mask, src_key_padding_mask=pad_mask)
        x = self.norm(x)
        output = self.fc(x)
        return output

def carregar_modelo():
    global MODELO, TOKENIZER
    TOKENIZER = Tokenizer()
    TOKENIZER.carregar("dataset.txt")
    MODELO = FosjaTransformer(len(TOKENIZER.vocab)).to(DEVICE)
    if os.path.exists("cerebro.pt"):
        MODELO.load_state_dict(torch.load("cerebro.pt", map_location=DEVICE))
    MODELO.eval()
    return MODELO

def gerar_resposta(pergunta, idioma="pt", modo="livre"):
    global MODELO, TOKENIZER
    if MODELO is None:
        carregar_modelo()
    max_tokens = 120 if modo == "avancado" else 90 if modo == "modelos" else 60
    temperatura = 0.85 if modo == "livre" else 0.7 if modo == "avancado" else 0.9
    ids = TOKENIZER.codificar(pergunta)
    gerado = ids[:]
    with torch.no_grad():
        for _ in range(max_tokens):
            contexto = gerado[-128:]
            x = torch.tensor([contexto], dtype=torch.long).to(DEVICE)
            saida = MODELO(x)
            logits = saida[0, -1] / temperatura
            probs = torch.softmax(logits, dim=-1)
            topk_probs, topk_ids = torch.topk(probs, k=40)
            topk_probs = topk_probs / topk_probs.sum()
            proximo = topk_ids[torch.multinomial(topk_probs, 1)].item()
            if proximo == TOKENIZER.fim_id:
                break
            gerado.append(proximo)
            palavra = TOKENIZER.decodificar([proximo])
            if palavra:
                yield palavra + " "
