# routers/reconhecimento.py
from fastapi import APIRouter

from schemas.requests import ImageRequest
from services.recognition_service import analisar_base64 as analisar_base64_service

router = APIRouter()


@router.post("/analisarBase64")
def analisar_base64(req: ImageRequest):
    return analisar_base64_service(req)
