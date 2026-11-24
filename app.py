from fastapi import FastAPI, Query, Request
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import json
import os
import time
import traceback
from modelo import gerar_resposta, carregar_modelo

app = FastAPI(title="FOSJA")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MODELO_CARREGADO = False

@app.on_event("startup")
async def startup():
    global MODELO_CARREGADO
    try:
        carregar_modelo()
        MODELO_CARREGADO = True
    except Exception:
        MODELO_CARREGADO = False

@app.get("/", response_class=HTMLResponse)
async def index():
    caminho = os.path.join(os.path.dirname(__file__), "index.html")
    with open(caminho, encoding="utf-8") as f:
        return f.read()

@app.get("/health")
async def health():
    return {"status": "ok", "modelo_carregado": MODELO_CARREGADO, "tempo": time.time()}

@app.get("/chat")
async def chat(
    request: Request,
    pergunta: str = Query(default="", max_length=2000),
    idioma: str = Query(default="pt"),
    modo: str = Query(default="livre"),
):
    pergunta_limpa = (pergunta or "").strip()
    idioma_norm = (idioma or "pt").lower().strip()
    modo_norm = (modo or "livre").lower().strip()
    if idioma_norm not in ("pt", "es"):
        idioma_norm = "pt"
    if modo_norm not in ("livre", "avancado", "modelos"):
        modo_norm = "livre"
    if not pergunta_limpa:
        async def vazio():
            yield f"data: {json.dumps({'texto': ''}, ensure_ascii=False)}\n\n"
            yield "data: [FIM]\n\n"
        return StreamingResponse(vazio(), media_type="text/event-stream")

    async def stream():
        try:
            async for pedaço in gerar_resposta(pergunta_limpa, idioma_norm, modo_norm):
                if pedaço:
                    yield f"data: {json.dumps({'texto': pedaço}, ensure_ascii=False)}\n\n"
            yield "data: [FIM]\n\n"
        except Exception:
            traceback.print_exc()
            yield f"data: {json.dumps({'texto': 'Não consegui responder agora. Tenta de novo.'}, ensure_ascii=False)}\n\n"
            yield "data: [FIM]\n\n"

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )

@app.exception_handler(Exception)
async def erro_global(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"erro": str(exc)})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
