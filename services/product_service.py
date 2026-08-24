# services/product_service.py
import logging
from datetime import datetime, timedelta

from core.database import get_conn
from schemas.requests import ProductBomRequest

logger = logging.getLogger(__name__)


def parse_br_date(date_str: str) -> datetime:
    """Converte string no formato dd/mm/yyyy para objeto datetime."""
    return datetime.strptime(date_str, "%d/%m/%Y")


# =====================================================
# 📦 LISTAGEM DE IMAGENS RECENTES
# =====================================================
def listar_imagens_recentes(start_date: str = None, end_date: str = None):
    conn = None
    cursor = None
    try:
        conn = get_conn()
        cursor = conn.cursor()

        # =================================================
        # DEFAULT: últimas 24h
        # =================================================
        if end_date:
            end_dt = parse_br_date(end_date)
        else:
            end_dt = datetime.now()

        if start_date:
            start_dt = parse_br_date(start_date)
        else:
            start_dt = end_dt - timedelta(days=1)

        # =================================================
        # Garante o range completo do dia para o SQL
        # =================================================
        start_dt = start_dt.replace(hour=0, minute=0, second=0, microsecond=0)
        end_dt = end_dt.replace(hour=23, minute=59, second=59, microsecond=999999)

        sql = """
        SELECT
            product_id,
            CONCAT('https://oxfordtec.com.br/Imagens/', image_path) AS full_image_url
        FROM product_image
        WHERE updated_at BETWEEN %s AND %s
          AND finalidade = 'PRODUTO'
          AND image_main = 1;
        """

        cursor.execute(sql, (start_dt, end_dt))
        rows = cursor.fetchall()

        lista_produtos = []

        for row in rows:
            lista_produtos.append(
                {
                    "product_id": row[0],
                    "full_image_url": row[1],
                }
            )

        return {
            "success": True,
            "total_items": len(lista_produtos),
            "data": lista_produtos,
        }

    except Exception as e:
        logger.exception("Falha ao listar imagens recentes")
        return {
            "success": False,
            "error_code": "DATABASE_ERROR",
            "message": str(e),
        }

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# =====================================================
# ➕ INSERIR REGISTRO NA PRODUCT_BOM
# =====================================================
def inserir_bom(req: ProductBomRequest):
    conn = None
    cursor = None
    try:
        conn = get_conn()
        cursor = conn.cursor()

        sql = """
            INSERT INTO product_bom (product_id, product_bom_id, product_name, product_qty)
            VALUES (%s, %s, %s, %s)
        """

        cursor.execute(sql, (req.product_id, req.product_bom_id, req.product_name, req.product_qty))
        conn.commit()

        novo_id = cursor.lastrowid

        return {
            "success": True,
            "message": "Registro inserido com sucesso.",
            "data": {
                "id": novo_id,
                "product_id": req.product_id,
                "product_bom_id": req.product_bom_id,
                "product_name": req.product_name,
                "product_qty": req.product_qty,
            },
        }

    except Exception as e:
        logger.exception("Falha ao inserir registro na product_bom")
        return {
            "success": False,
            "error_code": "INSERT_ERROR",
            "message": str(e),
        }

    finally:
        # ISSO AQUI SALVA O SEU BANCO: garante o fechamento ocorrendo erro ou não
        if cursor:
            cursor.close()
        if conn:
            conn.close()
