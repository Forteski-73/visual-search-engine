# routers/categorias.py
from fastapi import APIRouter, Body

from schemas.requests import RenameCategoryRequest
from services.category_service import excluir_categoria as excluir_categoria_service
from services.category_service import listar_categorias as listar_categorias_service
from services.category_service import renomear_categoria as renomear_categoria_service

router = APIRouter()


@router.get("/listarCategorias")
def listar_categorias():
    return listar_categorias_service()


@router.delete("/excluirCategoria")
def excluir_categoria(categoria: str = Body(..., embed=True)):
    return excluir_categoria_service(categoria)


@router.patch("/renomearCategoria")
def renomear_categoria(req: RenameCategoryRequest):
    return renomear_categoria_service(req.categoria_atual, req.categoria_nova)
