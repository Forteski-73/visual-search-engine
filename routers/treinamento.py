# routers/treinamento.py
from fastapi import APIRouter

from schemas.requests import TrainRequest
from services.training_service import treinar as treinar_categoria

router = APIRouter()


@router.post("/treinar")
def treinar(req: TrainRequest):
    return treinar_categoria(req)
