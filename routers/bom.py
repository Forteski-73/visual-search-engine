# routers/bom.py
from fastapi import APIRouter

from schemas.requests import ProductBomRequest
from services.product_service import inserir_bom as inserir_bom_service

router = APIRouter()


@router.post("/bom/inserir")
def inserir_bom(req: ProductBomRequest):
    return inserir_bom_service(req)
