# tokenizer.py - vocabulário próprio, sem copiar de ninguém

class TokenizerFOSJA:
    def __init__(self):
        self.palavra_para_id = {"<pad>": 0, "<inicio>": 1, "<fim>": 2}
        self.id_para_palavra = {0: "<pad>", 1: "<inicio>", 2: "<fim>"}

    def treinar(self, caminho="dataset.txt"):
        with open(caminho, "r", encoding="utf-8") as f:
            texto = f.read().lower()
        palavras = sorted(set(texto.split()))
        for p in palavras:
            if p not in self.palavra_para_id:
                novo_id = len(self.palavra_para_id)
                self.palavra_para_id[p] = novo_id
                self.id_para_palavra[novo_id] = p
        print(f"FOSJA aprendeu {len(self.palavra_para_id)} palavras")

    def codificar(self, texto):
        ids = [1]  # <inicio>
        for p in texto.lower().split():
            ids.append(self.palavra_para_id.get(p, 0))
        ids.append(2)  # <fim>
        return ids

    def decodificar(self, ids):
        palavras = []
        for i in ids:
            p = self.id_para_palavra.get(i, "")
            if p not in ["<pad>", "<inicio>", "<fim>"]:
                palavras.append(p)
        return " ".join(palavras)
