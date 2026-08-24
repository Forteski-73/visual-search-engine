# tests/test_imagens_recentes.py
from unittest.mock import MagicMock

from services import product_service


def _fake_conn(rows):
    cursor = MagicMock()
    cursor.fetchall.return_value = rows
    conn = MagicMock()
    conn.cursor.return_value = cursor
    return conn, cursor


def test_imagens_recentes_sucesso(client, monkeypatch):
    rows = [
        (101, "https://oxfordtec.com.br/Imagens/a.jpg"),
        (102, "https://oxfordtec.com.br/Imagens/b.jpg"),
    ]
    conn, cursor = _fake_conn(rows)
    monkeypatch.setattr(product_service, "get_conn", lambda: conn)

    resp = client.get("/imagensRecentes", params={"start_date": "01/01/2026", "end_date": "02/01/2026"})

    assert resp.status_code == 200
    assert resp.json() == {
        "success": True,
        "total_items": 2,
        "data": [
            {"product_id": 101, "full_image_url": "https://oxfordtec.com.br/Imagens/a.jpg"},
            {"product_id": 102, "full_image_url": "https://oxfordtec.com.br/Imagens/b.jpg"},
        ],
    }
    cursor.close.assert_called_once()
    conn.close.assert_called_once()


def test_imagens_recentes_default_ultimas_24h(client, monkeypatch):
    conn, cursor = _fake_conn([])
    monkeypatch.setattr(product_service, "get_conn", lambda: conn)

    resp = client.get("/imagensRecentes")

    assert resp.status_code == 200
    assert resp.json() == {"success": True, "total_items": 0, "data": []}


def test_imagens_recentes_erro_banco(client, monkeypatch):
    def _get_conn():
        raise RuntimeError("conexão recusada")

    monkeypatch.setattr(product_service, "get_conn", _get_conn)

    resp = client.get("/imagensRecentes", params={"start_date": "01/01/2026"})

    assert resp.status_code == 200
    assert resp.json() == {
        "success": False,
        "error_code": "DATABASE_ERROR",
        "message": "conexão recusada",
    }
