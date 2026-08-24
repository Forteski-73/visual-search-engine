# tests/test_bom_inserir.py
from unittest.mock import MagicMock

from services import product_service


def _fake_conn(lastrowid):
    cursor = MagicMock()
    cursor.lastrowid = lastrowid
    conn = MagicMock()
    conn.cursor.return_value = cursor
    return conn, cursor


def test_bom_inserir_sucesso(client, monkeypatch):
    conn, cursor = _fake_conn(lastrowid=55)
    monkeypatch.setattr(product_service, "get_conn", lambda: conn)

    payload = {
        "product_id": "P1",
        "product_bom_id": "B1",
        "product_name": "Prato Azul",
        "product_qty": 3,
    }
    resp = client.post("/bom/inserir", json=payload)

    assert resp.status_code == 200
    assert resp.json() == {
        "success": True,
        "message": "Registro inserido com sucesso.",
        "data": {
            "id": 55,
            "product_id": "P1",
            "product_bom_id": "B1",
            "product_name": "Prato Azul",
            "product_qty": 3,
        },
    }
    conn.commit.assert_called_once()
    cursor.close.assert_called_once()
    conn.close.assert_called_once()


def test_bom_inserir_defaults(client, monkeypatch):
    conn, cursor = _fake_conn(lastrowid=56)
    monkeypatch.setattr(product_service, "get_conn", lambda: conn)

    resp = client.post("/bom/inserir", json={"product_id": "P2"})

    assert resp.status_code == 200
    assert resp.json() == {
        "success": True,
        "message": "Registro inserido com sucesso.",
        "data": {
            "id": 56,
            "product_id": "P2",
            "product_bom_id": None,
            "product_name": None,
            "product_qty": 1,
        },
    }


def test_bom_inserir_erro(client, monkeypatch):
    def _get_conn():
        raise RuntimeError("insert falhou")

    monkeypatch.setattr(product_service, "get_conn", _get_conn)

    resp = client.post("/bom/inserir", json={"product_id": "P3"})

    assert resp.status_code == 200
    assert resp.json() == {
        "success": False,
        "error_code": "INSERT_ERROR",
        "message": "insert falhou",
    }
