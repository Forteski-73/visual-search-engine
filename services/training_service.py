# services/training_service.py
import logging
import random
import uuid
from datetime import datetime

from PIL import Image, ImageEnhance
from qdrant_client.models import PointStruct

from core.detector import detectar_prato
from core.embedding_model import gerar_embedding_dinov2
from core.image_utils import load_image_from_base64, load_image_from_url
from core.vector_db import COLLECTION_NAME, qdrant_client
from schemas.requests import TrainRequest

logger = logging.getLogger(__name__)


# =====================================================
# 🎨 FUNÇÃO DE DATA AUGMENTATION
# =====================================================
def aplicar_augmentations(img: Image.Image, variacao_index: int) -> Image.Image:
    """
    Aplica rotações e variações de iluminação para simular fotos reais.
    O 'variacao_index 0' sempre retorna a imagem original intacta.
    """
    if variacao_index == 0:
        return img  # A primeira imagem salva é sempre a original perfeita

    # 1. Rotação aleatória (Crucial para pratos redondos)
    angulo = random.uniform(0, 360)
    img_aug = img.rotate(angulo, resample=Image.BICUBIC, expand=False, fillcolor="black")

    # 2. Variação leve de Brilho
    fator_brilho = random.uniform(0.8, 1.2)
    img_aug = ImageEnhance.Brightness(img_aug).enhance(fator_brilho)

    # 3. Variação leve de Contraste
    fator_contraste = random.uniform(0.85, 1.15)
    img_aug = ImageEnhance.Contrast(img_aug).enhance(fator_contraste)

    return img_aug


# =====================================================
# 🧠 TREINAMENTO (SALVAMENTO VETORIAL DIRETO)
# =====================================================
def treinar(req: TrainRequest):
    try:
        img_original = (
            load_image_from_base64(req.image_base64)
            if req.image_base64
            else load_image_from_url(req.image_url)
        )
        if img_original is None:
            return {"success": False, "message": "Imagem inválida."}

        img_recortada = detectar_prato(img_original)
        if img_recortada is None:
            return {"success": False, "message": "YOLO não detectou o objeto."}

        total_augmentations = req.augmentations or 10
        pontos_para_inserir = []

        # Loop de Data Augmentation (Mantendo suas rotações e filtros simulando ambiente real)
        for i in range(total_augmentations):
            nova_img = aplicar_augmentations(img_recortada, variacao_index=i)

            # Extração profissional com DINOv2
            embedding = gerar_embedding_dinov2(nova_img)

            # Prepara o "ponto" para o Qdrant
            pontos_para_inserir.append(
                PointStruct(
                    id=str(uuid.uuid4()),  # ID único para cada variação treinada
                    vector=embedding.tolist(),
                    payload={
                        "categoria": req.categoria,
                        "data_treino": datetime.utcnow().isoformat(),
                        "model_version": "dinov2_base_v1",
                    },
                )
            )

        # Inserção em lote (Bulk Upsert) -> Ultra rápido
        qdrant_client.upsert(
            collection_name=COLLECTION_NAME,
            points=pontos_para_inserir,
        )

        return {
            "success": True,
            "message": f"Treinamento concluído. {total_augmentations} vetores indexados.",
            "categoria": req.categoria,
        }

    except Exception as e:
        logger.exception("Falha ao treinar categoria '%s'", req.categoria)
        return {"success": False, "error_code": "TRAINING_ERROR", "message": str(e)}
