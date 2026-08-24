# core/image_utils.py
import base64
import io
import logging
from io import BytesIO

import cv2
import numpy as np
import requests
from PIL import Image, ImageFile

logger = logging.getLogger(__name__)

# =====================================================
# EVITA ERRO COM IMAGEM PARCIAL
# =====================================================
ImageFile.LOAD_TRUNCATED_IMAGES = True

# =====================================================
# CONFIG
# =====================================================
MAX_IMAGE_SIZE_MB = 15

ALLOWED_FORMATS = [
    "jpeg",
    "jpg",
    "png",
    "webp",
    "bmp",
]


# =====================================================
# VALIDAR IMAGEM
# =====================================================
def validar_imagem(image_data: bytes):

    # ================================================
    # VAZIO
    # ================================================
    if not image_data:

        logger.warning("❌ Conteúdo vazio")

        return False

    # ================================================
    # TAMANHO
    # ================================================
    tamanho_mb = len(image_data) / (1024 * 1024)

    if tamanho_mb > MAX_IMAGE_SIZE_MB:

        logger.warning(f"❌ Imagem muito grande: {tamanho_mb:.2f} MB")

        return False

    # ================================================
    # FORMATO
    # ================================================
    try:

        img_test = Image.open(BytesIO(image_data))

        formato = img_test.format.lower()

    except Exception:

        logger.warning("❌ Formato inválido")

        return False

    # ================================================
    # VALIDA FORMATO
    # ================================================
    if formato not in ALLOWED_FORMATS:

        logger.warning(f"❌ Formato inválido: {formato}")

        return False

    return True


# =====================================================
# NORMALIZA IMAGEM
# =====================================================
def normalizar_imagem(img: Image.Image):

    try:

        # ============================================
        # RGB
        # ============================================
        img = img.convert("RGB")

        # ============================================
        # REMOVE EXIF ORIENTATION
        # ============================================
        try:

            exif = img.getexif()

            orientation = exif.get(274)

            if orientation == 3:

                img = img.rotate(180, expand=True)

            elif orientation == 6:

                img = img.rotate(270, expand=True)

            elif orientation == 8:

                img = img.rotate(90, expand=True)

        except Exception:
            pass

        return img

    except Exception as e:

        logger.warning(f"❌ Erro ao normalizar imagem: {str(e)}")

        return None


# =====================================================
# URL (ROBUSTO / PRODUÇÃO)
# =====================================================
def load_image_from_url(url: str):

    try:

        # ============================================
        # URL VAZIA
        # ============================================
        if not url:

            logger.warning("❌ URL vazia")

            return None

        headers = {
            "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64)"),
            "Accept": ("image/webp,image/apng,image/*,*/*;q=0.8"),
        }

        # ============================================
        # DOWNLOAD
        # ============================================
        response = requests.get(
            url,
            headers=headers,
            timeout=15,
            stream=True,
        )

        # ============================================
        # STATUS
        # ============================================
        if response.status_code != 200:

            logger.warning(f"❌ HTTP inválido: {response.status_code}")

            return None

        # ============================================
        # CONTENT TYPE
        # ============================================
        content_type = response.headers.get("Content-Type", "")

        if "image" not in content_type.lower():

            logger.warning(f"❌ URL não retornou imagem: {content_type}")

            return None

        # ============================================
        # BYTES
        # ============================================
        image_data = response.content

        # ============================================
        # VALIDAÇÃO
        # ============================================
        if not validar_imagem(image_data):

            return None

        # ============================================
        # PIL
        # ============================================
        img = Image.open(BytesIO(image_data))

        img = normalizar_imagem(img)

        if img is None:

            return None

        logger.info(f"✅ Imagem carregada via URL ({img.width}x{img.height})")

        return img

    except requests.exceptions.Timeout:

        logger.warning("❌ Timeout ao baixar imagem")

        return None

    except requests.exceptions.ConnectionError:

        logger.warning("❌ Erro de conexão")

        return None

    except requests.exceptions.RequestException as e:

        logger.warning(f"❌ Falha na requisição: {str(e)}")

        return None

    except Exception as e:

        logger.warning(f"❌ Erro ao processar imagem: {str(e)}")

        return None


# =====================================================
# BASE64 (ROBUSTO / PRODUÇÃO)
# =====================================================
def load_image_from_base64(base64_string: str):

    try:

        # ============================================
        # VAZIO
        # ============================================
        if not base64_string:

            logger.warning("❌ Base64 vazio")

            return None

        # ============================================
        # REMOVE DATA URI
        # ============================================
        if "," in base64_string:

            base64_string = base64_string.split(",")[1]

        # ============================================
        # DECODE
        # ============================================
        image_data = base64.b64decode(base64_string, validate=True)

        # ============================================
        # VALIDAÇÃO
        # ============================================
        if not validar_imagem(image_data):

            return None

        # ============================================
        # PIL
        # ============================================
        img = Image.open(BytesIO(image_data))

        img = normalizar_imagem(img)

        if img is None:

            return None

        logger.info(f"✅ Imagem Base64 carregada ({img.width}x{img.height})")

        return img

    except base64.binascii.Error:

        logger.warning("❌ Base64 inválido")

        return None

    except Exception as e:

        logger.warning(f"❌ Erro ao processar Base64: {str(e)}")

        return None


# =====================================================
# PIL IMAGE -> BASE64
# =====================================================
def image_to_base64(img):

    buffer = io.BytesIO()

    img.save(buffer, format="PNG")

    img_bytes = buffer.getvalue()

    base64_str = base64.b64encode(img_bytes).decode("utf-8")

    return f"data:image/png;base64,{base64_str}"


# =====================================================
# IMAGEM PROCESSADA (OPENCV OU PIL) -> BASE64 JPEG
# =====================================================
def converter_para_base64(img_processada) -> str:
    # Se a imagem for do OpenCV (numpy array)
    if isinstance(img_processada, np.ndarray):
        _, buffer = cv2.imencode(".jpg", img_processada)
        return base64.b64encode(buffer).decode("utf-8")

    # Se a imagem for do PIL Image
    elif isinstance(img_processada, Image.Image):
        buffered = BytesIO()
        img_processada.save(buffered, format="JPEG", quality=85)
        return base64.b64encode(buffered.getvalue()).decode("utf-8")

    raise ValueError("Formato de imagem não suportado para conversão em Base64")
