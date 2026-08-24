# main.py
from core.logging_config import configure_logging

configure_logging()

from fastapi import FastAPI

from core.vector_db import inicializar_banco_vetorial
from routers import bom, categorias, imagens, reconhecimento, treinamento

app = FastAPI(root_path="/AI")


@app.on_event("startup")
def startup_event():
    # Garante que o banco vetorial está pronto ao iniciar a API
    inicializar_banco_vetorial()


app.include_router(treinamento.router)
app.include_router(reconhecimento.router)
app.include_router(categorias.router)
app.include_router(imagens.router)
app.include_router(bom.router)
