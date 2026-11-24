# app.py - streaming com o modelo PRÓPRIO, sem Gemini

import json, torch
from fastapi import FastAPI
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from tokenizer import TokenizerFOSJA
from modelo import CerebroFOSJA

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Carrega o cérebro que TU treinou
tok = TokenizerFOSJA()
tok.treinar("dataset.txt")
checkpoint = torch.load("cerebro.pt", map_location="cpu")
tok.palavra_para_id = checkpoint["vocab"]
tok.id_para_palavra = {v:k for k,v in tok.palavra_para_id.items()}

modelo = CerebroFOSJA(len(tok.palavra_para_id))
modelo.load_state_dict(checkpoint["modelo"])
modelo.eval()

memoria = []

@app.get("/")
def home():
    return FileResponse("index.html")

@app.get("/chat")
async def chat(pergunta: str):
    memoria.append(pergunta)
    ids = tok.codificar(pergunta)

    def gerar_ao_vivo():
        # Gera palavra por palavra, ao vivo, igual no vídeo
        resposta_ids = []
        entrada = torch.tensor([ids])
        with torch.no_grad():
            for _ in range(20):
                saida = modelo(entrada)
                proxima = saida[0, -1].argmax().item()
                if proxima == 2:
                    break
                resposta_ids.append(proxima)
                palavra = tok.id_para_palavra.get(proxima, "")
                yield f"data: {json.dumps({'texto': palavra + ' '}, ensure_ascii=False)}\n\n"
                entrada = torch.cat([entrada, torch.tensor([[proxima]])], dim=1)
        yield "data: [FIM]\n\n"

    return StreamingResponse(gerar_ao_vivo(), media_type="text/event-stream")
