# routers/imagens.py
from fastapi import APIRouter, Query

from services.product_service import listar_imagens_recentes as listar_imagens_recentes_service

router = APIRouter()


@router.get("/imagensRecentes")
def imagens_recentes(
    start_date: str = Query(None),
    end_date: str = Query(None),
):
    return listar_imagens_recentes_service(start_date, end_date)
