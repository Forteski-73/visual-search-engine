# tests/test_categorias.py
import types

from services import category_service


def _point(categoria: str):
    return types.SimpleNamespace(payload={"categoria": categoria})


def test_listar_categorias_paginado(client, monkeypatch):
    paginas = [
        ([_point("prato_azul"), _point("prato_verde")], "offset_2"),
        ([_point("prato_azul"), _point("caneca_branca")], None),
    ]

    def scroll(**kwargs):
        return paginas.pop(0)

    monkeypatch.setattr(category_service.qdrant_client, "scroll", scroll)

    resp = client.get("/listarCategorias")

    assert resp.status_code == 200
    assert resp.json() == {
        "success": True,
        "total_categorias": 3,
        "data": ["caneca_branca", "prato_azul", "prato_verde"],
    }


def test_listar_categorias_erro(client, monkeypatch):
    def scroll(**kwargs):
        raise RuntimeError("qdrant indisponível")

    monkeypatch.setattr(category_service.qdrant_client, "scroll", scroll)

    resp = client.get("/listarCategorias")

    assert resp.status_code == 200
    assert resp.json() == {
        "success": False,
        "error_code": "FETCH_CATEGORIES_ERROR",
        "message": "Erro ao listar categorias: qdrant indisponível",
    }


def test_excluir_categoria_sucesso(client, monkeypatch):
    monkeypatch.setattr(
        category_service.qdrant_client,
        "delete",
        lambda **kwargs: "OperationResult(status=completed)",
    )

    resp = client.request("DELETE", "/excluirCategoria", json={"categoria": "prato_azul"})

    assert resp.status_code == 200
    assert resp.json() == {
        "success": True,
        "message": "Todos os vetores da categoria 'prato_azul' foram removidos com sucesso.",
        "details": "OperationResult(status=completed)",
    }


def test_excluir_categoria_erro(client, monkeypatch):
    def delete(**kwargs):
        raise RuntimeError("falha ao deletar")

    monkeypatch.setattr(category_service.qdrant_client, "delete", delete)

    resp = client.request("DELETE", "/excluirCategoria", json={"categoria": "prato_azul"})

    assert resp.status_code == 200
    assert resp.json() == {
        "success": False,
        "error_code": "DELETE_ERROR",
        "message": "Erro ao excluir a categoria: falha ao deletar",
    }
