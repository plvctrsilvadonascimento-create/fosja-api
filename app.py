from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import json
import os
from modelo import gerar_resposta, carregar_modelo

app = FastAPI(title="FOSJA")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.on_event("startup")
async def startup():
    try:
        carregar_modelo()
    except Exception:
        pass

@app.get("/", response_class=HTMLResponse)
async def index():
    caminho = os.path.join(os.path.dirname(__file__), "index.html")
    with open(caminho, encoding="utf-8") as f:
        return f.read()

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/chat")
async def chat(pergunta: str = Query(default=""), idioma: str = Query(default="pt"), modo: str = Query(default="livre")):
    pergunta_limpa = (pergunta or "").strip()
    idioma_norm = idioma.lower() if idioma.lower() in ("pt", "es") else "pt"
    modo_norm = modo.lower() if modo.lower() in ("livre", "avancado", "modelos") else "livre"
    async def stream():
        try:
            for pedaco in gerar_resposta(pergunta_limpa, idioma_norm, modo_norm):
                if pedaco:
                    yield f"data: {json.dumps({'texto': pedaco}, ensure_ascii=False)}\n\n"
            yield "data: [FIM]\n\n"
        except Exception:
            yield f"data: {json.dumps({'texto': 'Não consegui responder agora. Tenta de novo.'}, ensure_ascii=False)}\n\n"
            yield "data: [FIM]\n\n"
    return StreamingResponse(stream(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
