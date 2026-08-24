# schemas/requests.py
from typing import Optional

from pydantic import BaseModel, Field


# =====================================================
# ANÁLISE BASE64
# =====================================================
class ImageRequest(BaseModel):

    image_base64: str = Field(
        ...,
        description="Imagem em Base64",
    )


# =====================================================
# ANÁLISE URL
# =====================================================
class UrlImageRequest(BaseModel):

    image_url: str = Field(
        ...,
        description="URL pública da imagem",
    )


# =====================================================
# TREINAMENTO
# =====================================================
class TrainRequest(BaseModel):

    # ================================================
    # URL OPCIONAL
    # ================================================
    image_url: Optional[str] = Field(
        default=None,
        description="URL pública da imagem",
    )

    # ================================================
    # BASE64 OPCIONAL
    # ================================================
    image_base64: Optional[str] = Field(
        default=None,
        description="Imagem em Base64",
    )

    # ================================================
    # CATEGORIA
    # ================================================
    categoria: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Categoria da decoração/produto",
    )

    # ================================================
    # MODELO DINOv2
    # ================================================
    embedding_model: str = Field(
        default="dinov2-base",
        description="Modelo de embedding utilizado",
    )

    # ================================================
    # AUGMENTATIONS
    # ================================================
    augmentations: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Quantidade de imagens augmentadas",
    )


# =====================================================
# MODEL - BOM
# =====================================================
class ProductBomRequest(BaseModel):

    # ================================================
    # ID DO PRODUTO
    # ================================================
    product_id: str = Field(
        ...,
        min_length=1,
        max_length=10,
        description="Código do produto embalado",
    )

    # ================================================
    # ID DO PRODUTO BOM
    # ================================================
    product_bom_id: Optional[str] = Field(
        default=None,
        max_length=10,
        description="Código do produto da BOM",
    )

    # ================================================
    # NOME DO PRODUTO
    # ================================================
    product_name: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Nome/descrição do produto",
    )

    # ================================================
    # QUANTIDADE
    # ================================================
    product_qty: int = Field(
        default=1,
        ge=1,
        description="Quantidade do item na BOM",
    )
