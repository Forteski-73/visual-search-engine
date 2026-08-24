# core/detector.py
import logging

import numpy as np
import torch
from PIL import Image, ImageFilter
from ultralytics import YOLO

from config import PROJECT_ROOT

logger = logging.getLogger(__name__)

# =====================================================
# DEVICE
# =====================================================
device = "cuda" if torch.cuda.is_available() else "cpu"

logger.info(f"[DEVICE]: {device}")

# =====================================================
# MODELO YOLO SEGMENTATION
# =====================================================
MODEL_PATH = PROJECT_ROOT / "yolo" / "model_oxford_seg.pt"

if not MODEL_PATH.exists():
    raise FileNotFoundError(f"Modelo não encontrado: {MODEL_PATH}")

# =====================================================
# CARREGA YOLO
# =====================================================
model = YOLO(str(MODEL_PATH))

logger.info("[YOLO]: Modelo carregado")

# =====================================================
# CLASSES VÁLIDAS
# =====================================================
CLASSES_VALIDAS = [
    "PRATO",
    "XICARA",
    "CANECA",
]


# =====================================================
# DETECTAR OBJETO
# =====================================================
def detectar_prato(img):

    # =================================================
    # PREDIÇÃO
    # =================================================
    # conf=0.40, confiabilidade, para não identificar qualquer coisa
    results = model.predict(
        img,
        conf=0.30,
        verbose=False,
        device=device,
    )

    # =================================================
    # SEM RESULTADO
    # =================================================
    if not results:

        logger.debug("[YOLO]: Nenhum resultado")

        return None

    r = results[0]

    # =================================================
    # SEM MÁSCARA
    # =================================================
    if r.masks is None:

        logger.debug("[YOLO]: Nenhuma máscara encontrada")
        logger.debug("TOTAL BOXES: %s", len(r.boxes))

        for i, box in enumerate(r.boxes):

            cls = int(box.cls[0])

            nome = model.names[cls]

            conf = float(box.conf[0])

            logger.debug(f"[DETECÇÃO {i}] {nome} (conf={conf:.3f})")

        logger.debug("MASKS: %s", r.masks)

        return None

    masks = r.masks.data.cpu().numpy()

    boxes = r.boxes

    # =================================================
    # SOMENTE OBJETOS VÁLIDOS
    # =================================================
    deteccoes_validas = []

    for i, box in enumerate(boxes):

        cls = int(box.cls[0])

        nome = model.names[cls]

        conf = float(box.conf[0])

        logger.debug(f"[YOLO ENXERGOU]: {nome} (conf={conf:.2f})")

        # =============================================
        # IGNORA QUALQUER OUTRA COISA
        # =============================================
        if nome not in CLASSES_VALIDAS:

            logger.debug(f"[IGNORADO]: {nome}")

            continue

        # =============================================
        # ÁREA DA MÁSCARA
        # =============================================
        area = masks[i].sum()

        deteccoes_validas.append(
            {
                "idx": i,
                "classe": nome,
                "conf": conf,
                "area": area,
            }
        )

    # =================================================
    # NENHUM OBJETO VÁLIDO
    # =================================================
    if len(deteccoes_validas) == 0:

        logger.debug("[YOLO]: Nenhum plate/bowl/cup/mug/vase encontrado")

        return None

    # =================================================
    # ESCOLHE MAIOR ÁREA
    # =================================================
    melhor = max(deteccoes_validas, key=lambda x: x["area"])

    melhor_idx = melhor["idx"]

    logger.info(f"[YOLO DETECTOU]: {melhor['classe']} (conf={melhor['conf']:.2f})")

    # =================================================
    # MÁSCARA
    # =================================================
    mask = masks[melhor_idx]

    # =================================================
    # IMG -> NUMPY
    # =================================================
    img_np = np.array(img.convert("RGB"))

    h, w = img_np.shape[:2]

    # =================================================
    # RESIZE MÁSCARA
    # =================================================
    mask_img = Image.fromarray((mask * 255).astype(np.uint8))

    mask_img = mask_img.resize((w, h), Image.Resampling.LANCZOS)

    # =================================================
    # BORDA SUAVE
    # =================================================
    mask_img = mask_img.filter(ImageFilter.GaussianBlur(radius=1))

    # =================================================
    # FLOAT
    # =================================================
    mask = np.array(mask_img).astype(np.float32) / 255.0

    # =================================================
    # 3 CANAIS
    # =================================================
    mask_3d = np.stack([mask, mask, mask], axis=-1)

    # =================================================
    # SEGMENTAÇÃO
    # =================================================
    seg = img_np.astype(np.float32) * mask_3d

    # =================================================
    # FUNDO PRETO // ( OBS: **BRANCO RETIRADO**)
    # =================================================
    final = seg.astype(np.uint8)

    final = np.clip(final, 0, 255).astype(np.uint8)

    # =================================================
    # PIL FINAL
    # =================================================
    img_final = Image.fromarray(final)

    logger.debug("[YOLO]: Segmentação concluída")

    return img_final
