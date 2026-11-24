# modelo.py - FOSJA funcional completo, sem torch, so Python puro
import re
import random
import json
import os
from collections import defaultdict, Counter

ARQ_DATASET = "dataset.txt"
ARQ_MEMORIA = "memoria.json"

def limpar(texto):
    texto = texto.lower().strip()
    texto = re.sub(r'\s+', ' ', texto)
    return texto

def tokenizar(texto):
    texto = limpar(texto)
    # separa palavra e pontuacao
    return re.findall(r"[a-zà-ú0-9]+|[?.!]", texto)

class ModeloFosja:
    def __init__(self):
        self.linhas = []
        self.vocab = Counter()
        self.bigram = defaultdict(Counter)
        self.trigram = defaultdict(Counter)
        self.respostas = []  # lista de (pergunta_tokens, resposta_original)
        self.memoria = {}
        self.carregar()

    def carregar(self):
        # 1. Carrega dataset
        if os.path.exists(ARQ_DATASET):
            with open(ARQ_DATASET, "r", encoding="utf-8", errors="ignore") as f:
                self.linhas = [l.strip() for l in f if l.strip()]
        else:
            self.linhas = ["ola fosja", "fosja online", "quem e voce"]

        # 2. Carrega memoria
        if os.path.exists(ARQ_MEMORIA):
            try:
                with open(ARQ_MEMORIA, "r", encoding="utf-8") as f:
                    self.memoria = json.load(f)
            except:
                self.memoria = {}

        self.treinar()

    def treinar(self):
        self.vocab.clear()
        self.bigram.clear()
        self.trigram.clear()
        self.respostas.clear()

        for linha in self.linhas:
            toks = tokenizar(linha)
            if not toks:
                continue
            self.respostas.append((toks, linha))
            for t in toks:
                self.vocab[t] += 1
            # bigram / trigram
            for i in range(len(toks)-1):
                self.bigram[toks[i]][toks[i+1]] += 1
            for i in range(len(toks)-2):
                chave = (toks[i], toks[i+1])
                self.trigram[chave][toks[i+2]] += 1

    def salvar_memoria(self):
        try:
            with open(ARQ_MEMORIA, "w", encoding="utf-8") as f:
                json.dump(self.memoria, f, ensure_ascii=False, indent=2)
        except:
            pass

    def aprender(self, texto):
        texto = texto.strip()
        if not texto or texto in self.linhas:
            return False
        self.linhas.append(texto)
        with open(ARQ_DATASET, "a", encoding="utf-8") as f:
            f.write("\n" + texto)
        self.treinar()
        return True

    def buscar_melhor(self, pergunta):
        ptoks = set(tokenizar(pergunta))
        if not ptoks:
            return None, 0
        melhor = None
        melhor_score = 0
        for toks, original in self.respostas:
            # score = palavras em comum + bonus por ordem
            comuns = len(ptoks & set(toks))
            score = comuns / (len(ptoks) + 0.5)
            # bonus se for pergunta parecida
            if comuns > 0:
                score += 0.1
            if score > melhor_score:
                melhor_score = score
                melhor = original
        return melhor, melhor_score

    def gerar_por_ngram(self, semente, max_palavras=18):
        toks = tokenizar(semente)
        if not toks:
            toks = [random.choice(list(self.vocab.keys()))] if self.vocab else ["fosja"]
        resultado = toks[:]
        for _ in range(max_palavras):
            prox = None
            if len(resultado) >= 2:
                chave = (resultado[-2], resultado[-1])
                if chave in self.trigram and self.trigram[chave]:
                    prox = self.trigram[chave].most_common(1)[0][0]
            if not prox and resultado[-1] in self.bigram and self.bigram[resultado[-1]]:
                prox = self.bigram[resultado[-1]].most_common(1)[0][0]
            if not prox or prox in ["?", "!", "."]:
                break
            resultado.append(prox)
        texto = " ".join(resultado)
        texto = texto.replace(" ?", "?").replace(" !", "!").replace(" .", ".")
        return texto.capitalize()

    def responder(self, pergunta, historico=None):
        p = limpar(pergunta)
        if not p:
            return "Pode falar, estou te ouvindo."

        # 1. Memoria: se ja falou nome etc
        if "meu nome e" in p or "me chamo" in p:
            nome = p.replace("meu nome e", "").replace("me chamo", "").strip()
            nome = nome.capitalize()
            self.memoria["nome"] = nome
            self.salvar_memoria()
            return f"Prazer, {nome}! Vou lembrar de você."

        if "qual meu nome" in p or "sabe meu nome" in p:
            if "nome" in self.memoria:
                return f"Seu nome é {self.memoria['nome']}, claro que lembro."
            return "Ainda não sei seu nome. Como você se chama?"

        # 2. Saudações e intents fixos
        if p in ["oi", "ola", "ola!", "oi!", "bom dia", "boa tarde", "boa noite", "eai", "fala"]:
            return random.choice([
                "Olá! Eu sou a FOSJA, como posso te ajudar?",
                "Oi! Bom te ver por aqui. O que você quer saber?",
                "Fala! Estou online e pronta."
            ])
        if "quem e voce" in p or "quem é você" in p or "o que e voce" in p:
            return "Eu sou a FOSJA, uma IA feita pelo Paulo Victor. Aprendo com o que você me ensina."
        if "tudo bem" in p or "como vai" in p or "como voce esta" in p:
            return "Estou bem, rodando leve sem travar! E você, como vai?"
        if "obrigado" in p or "valeu" in p:
            return "Por nada! Precisando, é só chamar."
        if "tchau" in p or "adeus" in p:
            return "Até mais! Vou ficar aqui te esperando."

        # 3. Busca no dataset - resposta mais parecida
        melhor, score = self.buscar_melhor(p)
        if melhor and score > 0.35:
            # Se achou algo muito parecido, responde com contexto
            return melhor

        # 4. Geração por n-gram - cria frase nova
        if len(self.vocab) > 5:
            gerada = self.gerar_por_ngram(p)
            if len(gerada) > 3:
                return f"Entendi sobre '{pergunta}'. Pensa assim: {gerada}"

        # 5. Fallback inteligente
        return f"Entendi: '{pergunta}'. Ainda estou aprendendo sobre isso. Me ensina mais uma frase sobre esse assunto que eu aprendo na hora."

# Instancia global - o app.py usa isso
_instancia = ModeloFosja()

def carregar_modelo():
    global _instancia
    _instancia = ModeloFosja()
    return _instancia

def gerar_resposta(pergunta, historico=None):
    return _instancia.responder(pergunta, historico)

def treinar_modelo():
    _instancia.treinar()
    return True
