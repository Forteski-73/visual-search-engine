# tests/test_analisar_base64.py
import types

import numpy as np
from PIL import Image

from services import recognition_service


def _fake_point(categoria: str, score: float):
    return types.SimpleNamespace(payload={"categoria": categoria}, score=score)


def _fake_response(points):
    return types.SimpleNamespace(points=points)


def _prep_pipeline(monkeypatch, *, base64="ZmFrZQ==", detectado=True):
    fake_img = Image.new("RGB", (10, 10))
    monkeypatch.setattr(recognition_service, "load_image_from_base64", lambda b64: fake_img)
    monkeypatch.setattr(recognition_service, "detectar_prato", lambda img: (fake_img if detectado else None))
    monkeypatch.setattr(
        recognition_service, "gerar_embedding_dinov2", lambda img: np.zeros(768, dtype=np.float32)
    )
    monkeypatch.setattr(recognition_service, "converter_para_base64", lambda img: "BASE64FAKE")


def test_analisar_base64_vazio(client):
    resp = client.post("/analisarBase64", json={"image_base64": ""})

    assert resp.status_code == 200
    assert resp.json() == {"success": False, "message": "Base64 vazio."}


def test_analisar_base64_yolo_nao_detectou(client, monkeypatch):
    _prep_pipeline(monkeypatch, detectado=False)

    resp = client.post("/analisarBase64", json={"image_base64": "ZmFrZQ=="})

    assert resp.status_code == 200
    assert resp.json() == {"success": False, "message": "Nenhum prato/peça detectado pelo YOLO."}


def test_analisar_base64_reconhecido_na_busca_estrita(client, monkeypatch):
    _prep_pipeline(monkeypatch)

    resposta = _fake_response(
        [_fake_point("prato_azul", 0.9123), _fake_point("prato_verde", 0.85)]
    )
    query_points = lambda **kwargs: resposta
    monkeypatch.setattr(recognition_service.qdrant_client, "query_points", query_points)

    resp = client.post("/analisarBase64", json={"image_base64": "ZmFrZQ=="})

    assert resp.status_code == 200
    assert resp.json() == {
        "success": True,
        "reconhecido": True,
        "imagem_processada": "BASE64FAKE",
        "data": {
            "categoria_detectada": "prato_azul",
            "porcentagem_similaridade": "91.23%",
            "confianca": 91.23,
            "ranking_proximidade": [
                {"categoria": "prato_azul", "confianca": 91.23},
                {"categoria": "prato_verde", "confianca": 85.0},
            ],
        },
    }


def test_analisar_base64_fallback_busca_frouxa(client, monkeypatch):
    _prep_pipeline(monkeypatch)

    chamadas = {"n": 0}

    def query_points(**kwargs):
        chamadas["n"] += 1
        if kwargs.get("score_threshold") == 0.80:
            return _fake_response([])
        return _fake_response([_fake_point("prato_rosa", 0.70)])

    monkeypatch.setattr(recognition_service.qdrant_client, "query_points", query_points)

    resp = client.post("/analisarBase64", json={"image_base64": "ZmFrZQ=="})

    assert resp.status_code == 200
    assert resp.json() == {
        "success": True,
        "reconhecido": True,
        "imagem_processada": "BASE64FAKE",
        "data": {
            "categoria_detectada": "prato_rosa",
            "porcentagem_similaridade": "70.0%",
            "confianca": 70.0,
            "ranking_proximidade": [{"categoria": "prato_rosa", "confianca": 70.0}],
        },
    }
    assert chamadas["n"] == 2


def test_analisar_base64_nao_reconhecido(client, monkeypatch):
    _prep_pipeline(monkeypatch)

    monkeypatch.setattr(
        recognition_service.qdrant_client, "query_points", lambda **kwargs: _fake_response([])
    )

    resp = client.post("/analisarBase64", json={"image_base64": "ZmFrZQ=="})

    assert resp.status_code == 200
    assert resp.json() == {
        "success": True,
        "reconhecido": False,
        "imagem_processada": "BASE64FAKE",
        "message": "A imagem não pertence a nenhuma decoração catalogada.",
    }


def test_analisar_base64_erro_processamento(client, monkeypatch):
    fake_img = Image.new("RGB", (10, 10))
    monkeypatch.setattr(recognition_service, "load_image_from_base64", lambda b64: fake_img)

    def _boom(img):
        raise RuntimeError("falhou")

    monkeypatch.setattr(recognition_service, "detectar_prato", _boom)

    resp = client.post("/analisarBase64", json={"image_base64": "ZmFrZQ=="})

    assert resp.status_code == 200
    assert resp.json() == {
        "success": False,
        "error_code": "PROCESSING_ERROR",
        "message": "falhou",
    }
