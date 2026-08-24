# tests/conftest.py
import sys
import types
from unittest.mock import MagicMock

import pytest


def _stub(name: str, **attrs):
    mod = types.ModuleType(name)
    for key, value in attrs.items():
        setattr(mod, key, value)
    sys.modules[name] = mod
    return mod


# =====================================================
# Stub de dependências pesadas/externas ANTES da coleta de testes.
#
# Os arquivos de teste importam services.* no nível de módulo, e services.*
# importa core.detector / core.embedding_model / core.vector_db / core.database.
# Sem isso, rodar a suíte carregaria o YOLO e o DINOv2 de verdade e tentaria
# abrir uma conexão MySQL real. Este arquivo é carregado pelo pytest antes de
# qualquer módulo de teste do diretório, então o stub já está em sys.modules
# no momento em que services.* é importado.
# =====================================================
_stub("core.detector", detectar_prato=MagicMock(name="detectar_prato"))
_stub("core.embedding_model", gerar_embedding_dinov2=MagicMock(name="gerar_embedding_dinov2"))
_stub(
    "core.vector_db",
    qdrant_client=MagicMock(name="qdrant_client"),
    COLLECTION_NAME="decoracoes_pratos",
    inicializar_banco_vetorial=MagicMock(name="inicializar_banco_vetorial"),
)
_stub("core.database", get_conn=MagicMock(name="get_conn", return_value=MagicMock(name="mysql_connection")))


@pytest.fixture(scope="session")
def client():
    import main
    from fastapi.testclient import TestClient

    with TestClient(main.app) as test_client:
        yield test_client
