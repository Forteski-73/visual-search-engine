# tests/test_treinar.py
import numpy as np
from PIL import Image

from services import training_service


def test_treinar_sucesso(client, monkeypatch):
    fake_img = Image.new("RGB", (10, 10))

    monkeypatch.setattr(training_service, "load_image_from_base64", lambda b64: fake_img)
    monkeypatch.setattr(training_service, "detectar_prato", lambda img: fake_img)
    monkeypatch.setattr(
        training_service, "gerar_embedding_dinov2", lambda img: np.zeros(768, dtype=np.float32)
    )
    monkeypatch.setattr(training_service.qdrant_client, "upsert", lambda **kwargs: None)

    resp = client.post(
        "/treinar",
        json={"image_base64": "ZmFrZQ==", "categoria": "prato_azul", "augmentations": 1},
    )

    assert resp.status_code == 200
    assert resp.json() == {
        "success": True,
        "message": "Treinamento concluído. 1 vetores indexados.",
        "categoria": "prato_azul",
    }


def test_treinar_imagem_invalida(client, monkeypatch):
    monkeypatch.setattr(training_service, "load_image_from_base64", lambda b64: None)

    resp = client.post(
        "/treinar",
        json={"image_base64": "ZmFrZQ==", "categoria": "prato_azul"},
    )

    assert resp.status_code == 200
    assert resp.json() == {"success": False, "message": "Imagem inválida."}


def test_treinar_yolo_nao_detectou(client, monkeypatch):
    fake_img = Image.new("RGB", (10, 10))

    monkeypatch.setattr(training_service, "load_image_from_base64", lambda b64: fake_img)
    monkeypatch.setattr(training_service, "detectar_prato", lambda img: None)

    resp = client.post(
        "/treinar",
        json={"image_base64": "ZmFrZQ==", "categoria": "prato_azul"},
    )

    assert resp.status_code == 200
    assert resp.json() == {"success": False, "message": "YOLO não detectou o objeto."}


def test_treinar_erro_interno(client, monkeypatch):
    fake_img = Image.new("RGB", (10, 10))

    def _boom(img):
        raise RuntimeError("boom")

    monkeypatch.setattr(training_service, "load_image_from_base64", lambda b64: fake_img)
    monkeypatch.setattr(training_service, "detectar_prato", lambda img: fake_img)
    monkeypatch.setattr(training_service, "gerar_embedding_dinov2", _boom)

    resp = client.post(
        "/treinar",
        json={"image_base64": "ZmFrZQ==", "categoria": "prato_azul", "augmentations": 1},
    )

    assert resp.status_code == 200
    assert resp.json() == {
        "success": False,
        "error_code": "TRAINING_ERROR",
        "message": "boom",
    }
