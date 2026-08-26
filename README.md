# Oxford Visual Search Engine

API de reconhecimento visual de produtos para a Oxford Porcelanas. Recebe a foto de uma peça (prato, xícara ou caneca), identifica a decoração/estampa através de visão computacional e busca por similaridade vetorial, e devolve a categoria mais provável já cadastrada — com 197 categorias/decorações treinadas hoje.

## Como funciona

```
foto (URL ou base64)
        │
        ▼
 detecção + segmentação (YOLO)        → recorta o objeto, remove o fundo
        │
        ▼
 embedding visual (DINOv2, 768-d)      → assinatura da forma/textura da peça
        │
        ▼
 busca por similaridade (Qdrant)       → cosseno, threshold 0.80 com fallback em 0.65
        │
        ▼
 categoria/decoração + confiança
```

O treinamento (`/treinar`) segue o mesmo caminho até a segmentação, aplica *data augmentation* (rotação, brilho, contraste) para gerar variações sintéticas de cada foto, e grava os vetores resultantes no Qdrant associados à categoria informada.

## Stack

- **FastAPI** — API HTTP
- **Ultralytics YOLO** — detecção e segmentação do objeto na imagem
- **DINOv2** (`facebook/dinov2-base`, via HuggingFace Transformers) — geração do embedding visual
- **Qdrant** (modo embutido, local) — banco vetorial para busca por similaridade
- **MySQL** (`mysql-connector-python`, com pool de conexões) — dados de produto/BOM
- **pydantic-settings** — configuração via `.env`
- **pytest** — testes de contrato dos endpoints

## Estrutura do projeto

```
main.py                 # cria a app FastAPI, registra os routers
config.py                # configuração (variáveis de ambiente)
core/
  detector.py             # YOLO — detecção e segmentação
  embedding_model.py        # DINOv2 — geração do embedding
  vector_db.py                # cliente Qdrant
  database.py                   # pool de conexão MySQL
  image_utils.py                  # carregamento/validação de imagem
  logging_config.py                 # logging estruturado
schemas/
  requests.py              # modelos Pydantic das requisições
services/                  # regras de negócio de cada operação
routers/                     # endpoints HTTP (fino, delega para services/)
tests/                          # testes de contrato (mockando YOLO/DINOv2/Qdrant/MySQL)
```

## Endpoints

| Método | Rota | Descrição |
|---|---|---|
| `POST` | `/treinar` | Indexa uma nova foto (com *data augmentation*) sob uma categoria/decoração |
| `POST` | `/analisarBase64` | Identifica a categoria/decoração de uma foto enviada em base64 |
| `GET` | `/listarCategorias` | Lista todas as categorias já treinadas |
| `PATCH` | `/renomearCategoria` | Renomeia uma categoria já treinada, sem retreinar (só corrige o payload) |
| `DELETE` | `/excluirCategoria` | Remove todos os vetores de uma categoria |
| `GET` | `/imagensRecentes` | Lista imagens de produto recentes (MySQL) |
| `POST` | `/bom/inserir` | Insere um registro na BOM do produto (MySQL) |

Documentação interativa (Swagger) disponível em `/docs` com o servidor rodando.

## Configuração

Crie um `.env` na raiz do projeto:

```env
DB_HOST=
DB_NAME=
DB_USER=
DB_PASSWORD=
LOG_LEVEL=INFO
```

Também é necessário o peso do modelo YOLO em `yolo/model_oxford_seg.pt` (não versionado — arquivo binário grande, mantido fora do Git).

## Rodando localmente

```bash
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt

uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Na primeira subida o YOLO e o DINOv2 são carregados (o DINOv2 baixa do HuggingFace Hub se ainda não estiver em cache local). A API fica disponível em `http://127.0.0.1:8000`.

## Testes

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

## Deploy

Em produção, a API roda via `uvicorn` sob um serviço `systemd`, atrás de um `nginx` fazendo proxy reverso (a API é montada com `root_path="/AI"`). Os dados do Qdrant (`qdrant_local/`) e o peso do modelo YOLO não são versionados no Git — persistem apenas no disco do servidor.
