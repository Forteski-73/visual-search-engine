# services/recognition_service.py
import logging

from core.detector import detectar_prato
from core.embedding_model import gerar_embedding_dinov2
from core.image_utils import converter_para_base64, load_image_from_base64
from core.vector_db import COLLECTION_NAME, qdrant_client
from schemas.requests import ImageRequest

logger = logging.getLogger(__name__)


# =====================================================
# 🔍 RECONHECIMENTO COM ALTA PRECISÃO
# =====================================================
def analisar_base64(req: ImageRequest):
    if not req.image_base64:
        return {"success": False, "message": "Base64 vazio."}

    try:
        img_original = load_image_from_base64(req.image_base64)
        img_processada = detectar_prato(img_original)

        if img_processada is None:
            return {"success": False, "message": "Nenhum prato/peça detectado pelo YOLO."}

        # 🔄 CONVERSÃO: Transforma o recorte do YOLO de volta para string Base64
        base64_processada = converter_para_base64(img_original)

        # 1. Gera o embedding da imagem enviada pelo cliente
        embedding_teste = gerar_embedding_dinov2(img_processada)

        # 1ª Tentativa: Busca estrita (Padrão Ouro)
        resposta_qdrant = qdrant_client.query_points(
            collection_name=COLLECTION_NAME,
            query=embedding_teste.tolist(),
            limit=3,  # Mantém os 3 melhores
            score_threshold=0.80,  # Rígido
        )

        # Se não retornou nada (lista vazia), entra o plano B: busca mais frouxa
        if not resposta_qdrant.points:
            logger.info("Nenhum resultado com score >= 0.80. Tentando busca frouxa... >= 0.65")

            resposta_qdrant = qdrant_client.query_points(
                collection_name=COLLECTION_NAME,
                query=embedding_teste.tolist(),
                limit=3,  # Mantém os 3 melhores
                score_threshold=0.65,  # Relaxa o limiar (pega decorações parecidas, mas não idênticas)
            )

        # Extrai a lista de pontos de dentro do objeto de resposta do Qdrant
        resultados_busca = resposta_qdrant.points

        if not resultados_busca:
            return {
                "success": True,
                "reconhecido": False,
                "imagem_processada": base64_processada,
                "message": "A imagem não pertence a nenhuma decoração catalogada.",
            }

        # O primeiro elemento é o de maior score (similaridade mais próxima de 1.0)
        melhor_match = resultados_busca[0]

        return {
            "success": True,
            "reconhecido": True,
            "imagem_processada": base64_processada,
            "data": {
                "categoria_detectada": melhor_match.payload["categoria"],
                "porcentagem_similaridade": f"{round(melhor_match.score * 100, 2)}%",  # Ex: "96.42%"
                "confianca": round(melhor_match.score * 100, 2),  # Ex: 94.55%
                "ranking_proximidade": [
                    {"categoria": r.payload["categoria"], "confianca": round(r.score * 100, 2)}
                    for r in resultados_busca
                ],
            },
        }

    except Exception as e:
        logger.exception("Falha ao analisar imagem em /analisarBase64")
        return {"success": False, "error_code": "PROCESSING_ERROR", "message": str(e)}
