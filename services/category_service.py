# services/category_service.py
import logging

from qdrant_client.models import FieldCondition, Filter, MatchValue

from core.vector_db import COLLECTION_NAME, qdrant_client

logger = logging.getLogger(__name__)


# =====================================================
# 📋 LISTAR TODAS AS CATEGORIAS CADASTRADAS (QDRANT)
# =====================================================
def listar_categorias():
    try:
        categorias_unicas = set()
        offset = None

        # Faz um loop usando paginação (scroll) para garantir que lerá
        # todos os pontos, mesmo se a base crescer muito
        while True:
            valores_scroll, proximo_offset = qdrant_client.scroll(
                collection_name=COLLECTION_NAME,
                with_payload=True,  # Precisamos ler o payload para pegar o nome da categoria
                with_vectors=False,  # IMPORTANTE: False ignora os vetores (deixa a busca ultra rápida)
                limit=100,  # Lê de 100 em 100 pontos por lote
                offset=offset,
            )

            # Extrai o nome da categoria do payload de cada ponto encontrado
            for ponto in valores_scroll:
                if ponto.payload and "categoria" in ponto.payload:
                    categorias_unicas.add(ponto.payload["categoria"])

            # Se não houver mais páginas (offset), encerra o loop
            if proximo_offset is None:
                break

            offset = proximo_offset

        # Converte o 'set' (que remove duplicados automaticamente) em uma lista ordenada
        lista_final = sorted(list(categorias_unicas))

        return {
            "success": True,
            "total_categorias": len(lista_final),
            "data": lista_final,
        }

    except Exception as e:
        logger.exception("Falha ao listar categorias")
        return {
            "success": False,
            "error_code": "FETCH_CATEGORIES_ERROR",
            "message": f"Erro ao listar categorias: {str(e)}",
        }


# =====================================================
# 🗑️ APAGAR CATEGORIA DO BANCO VETORIAL
# =====================================================
def excluir_categoria(categoria: str):
    try:
        # Executa a deleção baseada em um filtro de payload
        resultado = qdrant_client.delete(
            collection_name=COLLECTION_NAME,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="categoria",
                        match=MatchValue(value=categoria),
                    )
                ]
            ),
        )

        return {
            "success": True,
            "message": f"Todos os vetores da categoria '{categoria}' foram removidos com sucesso.",
            "details": str(resultado),
        }

    except Exception as e:
        logger.exception("Falha ao excluir categoria '%s'", categoria)
        return {
            "success": False,
            "error_code": "DELETE_ERROR",
            "message": f"Erro ao excluir a categoria: {str(e)}",
        }


# =====================================================
# ✏️ RENOMEAR CATEGORIA (SÓ O PAYLOAD, VETOR INTACTO)
# =====================================================
def renomear_categoria(categoria_atual: str, categoria_nova: str):
    try:
        filtro_atual = Filter(
            must=[FieldCondition(key="categoria", match=MatchValue(value=categoria_atual))]
        )

        total_afetado = qdrant_client.count(
            collection_name=COLLECTION_NAME,
            count_filter=filtro_atual,
        ).count

        if total_afetado == 0:
            return {
                "success": False,
                "error_code": "CATEGORY_NOT_FOUND",
                "message": f"Nenhum vetor encontrado com a categoria '{categoria_atual}'.",
            }

        qdrant_client.set_payload(
            collection_name=COLLECTION_NAME,
            payload={"categoria": categoria_nova},
            points=filtro_atual,
        )

        return {
            "success": True,
            "message": (
                f"Categoria '{categoria_atual}' renomeada para '{categoria_nova}' "
                f"em {total_afetado} vetor(es)."
            ),
            "total_renomeado": total_afetado,
        }

    except Exception as e:
        logger.exception("Falha ao renomear categoria '%s' -> '%s'", categoria_atual, categoria_nova)
        return {
            "success": False,
            "error_code": "RENAME_ERROR",
            "message": f"Erro ao renomear a categoria: {str(e)}",
        }
