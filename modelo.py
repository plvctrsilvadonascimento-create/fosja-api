import re

class Tokenizer:
    def __init__(self):
        self.vocab = {}
        self.inverso = {}
        self.fim_id = 0
        self.pad_id = 1
        self.unk_id = 2
    def normalizar(self, texto):
        texto = texto.lower().strip()
        texto = texto.replace("?", " ? ").replace(".", " . ").replace(",", " , ").replace("!", " ! ").replace(":", " : ")
        return texto.split()
    def carregar(self, caminho):
        with open(caminho, encoding="utf-8") as f:
            texto = f.read()
        tokens = self.normalizar(texto)
        unicos = sorted(set(tokens))
        self.vocab = {"<fim>": 0, "<pad>": 1, "<unk>": 2}
        for i, t in enumerate(unicos, start=3):
            self.vocab[t] = i
        self.inverso = {v: k for k, v in self.vocab.items()}
        self.fim_id = 0
        self.pad_id = 1
        self.unk_id = 2
    def codificar(self, texto):
        tokens = self.normalizar(texto)
        return [self.vocab.get(t, self.unk_id) for t in tokens]
    def decodificar(self, ids):
        palavras = []
        for i in ids:
            if i == self.fim_id or i == self.pad_id:
                continue
            palavras.append(self.inverso.get(i, ""))
        texto = " ".join(palavras)
        texto = texto.replace(" ?", "?").replace(" .", ".").replace(" ,", ",").replace(" !", "!").replace(" :", ":")
        return texto.strip()
