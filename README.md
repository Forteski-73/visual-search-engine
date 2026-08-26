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
