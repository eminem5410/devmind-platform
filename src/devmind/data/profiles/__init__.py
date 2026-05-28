"""
Perfiles de setup para DevMind.

Cada perfil define un stack completo de desarrollo AI adaptado
al hardware detectado. Los templates generan archivos reales
en el directorio del proyecto.

Perfiles disponibles:
  - local-llm  : Ollama + modelo + OpenWebUI para chat local
  - ai-dev     : Entorno completo de desarrollo AI (Docker + Ollama + Jupyter + tools)
  - rag-lab    : Stack RAG con Ollama + ChromaDB + FastAPI template
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SetupProfile:
    """Definicion de un perfil de setup."""
    name: str
    description: str
    min_ram_gb: float = 4.0
    min_disk_gb: float = 10.0
    needs_gpu: bool = False
    needs_docker: bool = False
    needs_ollama: bool = False
    files: dict[str, str] = field(default_factory=dict)  # filename -> content
    post_setup_commands: list[str] = field(default_factory=list)


# ── Template generators ──────────────────────────────────────────────────

def _recommended_model(ram_gb: float, has_gpu: bool) -> str:
    """Recomienda un modelo basado en hardware."""
    if has_gpu and ram_gb >= 16:
        return "llama3.1:8b"
    elif has_gpu and ram_gb >= 8:
        return "llama3.2:3b"
    elif ram_gb >= 8:
        return "llama3.2:3b"
    elif ram_gb >= 4:
        return "phi3:mini"
    else:
        return "llama3.2:1b"


def _get_openwebui_port(has_gpu: bool) -> str:
    """Puerto diferente si hay GPU (por si hay otra cosa corriendo)."""
    return "3100" if has_gpu else "3000"


def generate_local_llm_profile(ram_gb: float, has_gpu: bool,
                                python_version: str = "3.12",
                                ollama_version: Optional[str] = None) -> SetupProfile:
    """Genera el perfil local-llm: Ollama + OpenWebUI para chat local."""
    model = _recommended_model(ram_gb, has_gpu)
    port = _get_openwebui_port(has_gpu)

    docker_compose = f"""version: "3.8"

# DevMind Setup — local-llm
# Chat local con LLM usando Ollama + OpenWebUI
# Generado automaticamente por DevMind v0.4.0

services:
  ollama:
    image: ollama/ollama:latest
    container_name: devmind-ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama-data:/root/.ollama
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: {int(ram_gb * 0.6)}G

  open-webui:
    image: ghcr.io/open-webui/open-webui:main
    container_name: devmind-webui
    ports:
      - "{port}:8080"
    environment:
      - OLLAMA_BASE_URL=http://ollama:11434
    volumes:
      - open-webui-data:/app/backend/data
    depends_on:
      - ollama
    restart: unless-stopped

volumes:
  ollama-data:
  open-webui-data:
"""
    env_content = f"""# DevMind Setup — local-llm
# Variables de entorno
# Generado por DevMind v0.4.0

# Modelo LLM por defecto
DEFAULT_MODEL={model}

# Puerto de OpenWebUI
WEBUI_PORT={port}

# Puerto de Ollama API
OLLAMA_PORT=11434

# Ollama URL (para apps externas)
OLLAMA_BASE_URL=http://localhost:11434
"""
    readme_content = f"""# Local LLM — DevMind Setup

Stack de chat local con LLM usando Ollama + OpenWebUI.

## Que se instaló

- **Ollama**: Motor de inferencia local
- **OpenWebUI**: Interfaz web tipo ChatGPT (puerto {port})
- **Modelo**: {model} (recomendado para tu hardware)

## Iniciar

```bash
docker compose up -d
```

## Acceder

- **Chat UI**: http://localhost:{port}
- **Ollama API**: http://localhost:11434

## Descargar modelo

```bash
docker exec devmind-ollama ollama pull {model}
```

## Comandos útiles

```bash
# Ver logs
docker compose logs -f

# Ver modelos disponibles
docker exec devmind-ollama ollama list

# Probar modelo desde terminal
docker exec devmind-ollama ollama run {model}

# Detener
docker compose down

# Detener y borrar datos
docker compose down -v
```

## Modelos recomendados

| RAM | Modelo | Params | Tamano |
|-----|--------|--------|--------|
| 4GB | llama3.2:1b | 1.3B | ~800MB |
| 4-8GB | phi3:mini | 3.8B | ~2.3GB |
| 8GB+ | llama3.2:3b | 3.2B | ~2GB |
| 16GB+ GPU | llama3.1:8b | 8B | ~4.9GB |

Generado por [DevMind](https://github.com/eminem5410/devmind-platform) v0.4.0
"""
    return SetupProfile(
        name="local-llm",
        description="Chat local con LLM: Ollama + OpenWebUI",
        min_ram_gb=4.0,
        min_disk_gb=10.0,
        needs_docker=True,
        needs_ollama=False,  # Ollama viene en Docker
        files={
            "docker-compose.yml": docker_compose,
            ".env": env_content,
            "README.md": readme_content,
        },
        post_setup_commands=[
            f"docker compose up -d",
            f"echo 'Esperando a Ollama...'",
            f"sleep 10",
            f"docker exec devmind-ollama ollama pull {model}",
            f"echo 'Listo! Abri http://localhost:{port}'",
        ],
    )


def generate_ai_dev_profile(ram_gb: float, has_gpu: bool,
                              ollama_version: Optional[str] = None,
                              python_version: str = "3.12") -> SetupProfile:
    """Genera el perfil ai-dev: entorno completo de desarrollo AI."""
    model = _recommended_model(ram_gb, has_gpu)

    requirements = """# DevMind Setup — ai-dev
# Dependencias de Python para desarrollo AI

# Core ML
numpy>=1.26.0
scikit-learn>=1.5.0
pandas>=2.2.0

# Deep Learning (CPU)
torch>=2.3.0 --index-url https://download.pytorch.org/whl/cpu

# LLM / NLP
transformers>=4.42.0
sentence-transformers>=3.0.0
langchain>=0.2.0
langchain-community>=0.2.0

# Ollama client
ollama>=0.3.0

# Vector stores
chromadb>=0.5.0

# API
fastapi>=0.111.0
uvicorn>=0.30.0

# Notebooks
jupyter>=1.0.0
ipywidgets>=8.1.0

# Dev tools
python-dotenv>=1.0.0
httpx>=0.27.0
rich>=13.7.0
pytest>=8.0.0
"""
    docker_compose = """version: "3.8"

# DevMind Setup — ai-dev
# Entorno de desarrollo AI con Ollama + Jupyter
# Generado automaticamente por DevMind v0.4.0

services:
  ollama:
    image: ollama/ollama:latest
    container_name: devmind-ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama-data:/root/.ollama
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 4G

  jupyter:
    image: jupyter/scipy-notebook:latest
    container_name: devmind-jupyter
    ports:
      - "8888:8888"
    volumes:
      - ./notebooks:/home/jovyan/work
    environment:
      - JUPYTER_TOKEN=devmind
    depends_on:
      - ollama
    restart: unless-stopped

volumes:
  ollama-data:
"""
    example_notebook = """{
 "cells": [
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": ["# DevMind AI-Dev Environment", "", "Este notebook verifica que todo funciona correctamente."]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": ["import sys\\nprint(f'Python: {sys.version}')"]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": ["import torch\\nprint(f'PyTorch: {torch.__version__}')\\nprint(f'CUDA available: {torch.cuda.is_available()}')"]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": ["import ollama\\nclient = ollama.Client()\\nmodels = client.list()\\nprint(f'Modelos Ollama: {[m.model for m in models]}')"]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": ["from transformers import pipeline\\n\\n# Sentiment analysis como ejemplo\\nclassifier = pipeline('sentiment-analysis')\\nresult = classifier('DevMind is amazing for AI development!')\\nprint(result)"]
  }
 ],
 "metadata": {
  "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
  "language_info": {"name": "python", "version": "3.12.0"}
 },
 "nbformat": 4,
 "nbformat_minor": 4
}"""
    readme_content = f"""# AI-Dev Environment — DevMind Setup

Entorno completo de desarrollo AI con Docker, Ollama y Jupyter.

## Que se instaló

- **Docker Compose**: Ollama + Jupyter
- **requirements.txt**: Todas las dependencias Python para AI
- **notebooks/**: Notebook de verificacion
- **Modelo recomendado**: {model}

## Iniciar

```bash
# 1. Levantar servicios Docker
docker compose up -d

# 2. Crear venv e instalar dependencias
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. Descargar modelo
ollama pull {model}
```

## Acceder

- **Jupyter**: http://localhost:8888?token=devmind
- **Ollama API**: http://localhost:11434

## Verificar instalacion

```bash
# Python + PyTorch
python -c "import torch; print(f'PyTorch {{torch.__version__}}, CUDA: {{torch.cuda.is_available()}}')"

# Transformers
python -c "from transformers import pipeline; print(pipeline('sentiment-analysis')('OK'))"

# Ollama
ollama list
```

Generado por [DevMind](https://github.com/eminem5410/devmind-platform) v0.4.0
"""
    return SetupProfile(
        name="ai-dev",
        description="Entorno completo de desarrollo AI: Docker + Ollama + Jupyter + deps",
        min_ram_gb=4.0,
        min_disk_gb=15.0,
        needs_docker=True,
        needs_ollama=True,
        files={
            "docker-compose.yml": docker_compose,
            "requirements.txt": requirements,
            ".env": f"DEFAULT_MODEL={model}\nJUPYTER_TOKEN=devmind\n",
            "notebooks/test-setup.ipynb": example_notebook,
            "README.md": readme_content,
        },
        post_setup_commands=[
            "docker compose up -d",
            f"ollama pull {model}",
            "echo 'Instala dependencias Python con: source .venv/bin/activate && pip install -r requirements.txt'",
        ],
    )


def generate_rag_lab_profile(ram_gb: float, has_gpu: bool,
                               python_version: str = "3.12",
                               ollama_version: Optional[str] = None) -> SetupProfile:
    """Genera el perfil rag-lab: stack RAG con Ollama + ChromaDB + FastAPI."""
    model = _recommended_model(ram_gb, has_gpu)

    docker_compose = """version: "3.8"

# DevMind Setup — rag-lab
# Stack RAG: Ollama + ChromaDB + FastAPI
# Generado automaticamente por DevMind v0.4.0

services:
  ollama:
    image: ollama/ollama:latest
    container_name: devmind-ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama-data:/root/.ollama
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 4G

  chromadb:
    image: chromadb/chroma:latest
    container_name: devmind-chroma
    ports:
      - "8000:8000"
    volumes:
      - chroma-data:/chroma/chroma
    environment:
      - IS_PERSISTENT=TRUE
      - ANONYMIZED_TELEMETRY=FALSE
    restart: unless-stopped

volumes:
  ollama-data:
  chroma-data:
"""
    requirements = """# DevMind Setup — rag-lab
# Dependencias para RAG (Retrieval-Augmented Generation)

# LLM
ollama>=0.3.0

# Embeddings + Vector Store
chromadb>=0.5.0
sentence-transformers>=3.0.0

# Framework
langchain>=0.2.0
langchain-community>=0.2.0
langchain-chroma>=0.1.0

# API
fastapi>=0.111.0
uvicorn>=0.30.0
pydantic>=2.5.0

# Document loading
pypdf>=4.0.0
python-docx>=1.1.0

# Dev
python-dotenv>=1.0.0
httpx>=0.27.0
rich>=13.7.0
"""
    rag_engine = f'''"""DevMind RAG Lab — Motor RAG basico.

Usa Ollama para generacion y ChromaDB para retrieval.
"""
import os
from pathlib import Path

import chromadb
from langchain_chroma import Chroma
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.llms import Ollama
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.prompts import ChatPromptTemplate


MODEL = os.getenv("DEFAULT_MODEL", "{model}")
CHROMA_URL = os.getenv("CHROMA_URL", "http://localhost:8000")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")


def get_embedding_model():
    """Retorna el modelo de embeddings via Ollama."""
    return OllamaEmbeddings(
        model="nomic-embed-text",
        base_url=OLLAMA_URL,
    )


def get_llm():
    """Retorna el LLM via Ollama."""
    return Ollama(model=MODEL, base_url=OLLAMA_URL)


def get_vectorstore(collection_name: str = "documents"):
    """Retorna un vectorstore de ChromaDB."""
    client = chromadb.HttpClient(host="localhost", port=8000)
    embeddings = get_embedding_model()
    return Chroma(
        collection_name=collection_name,
        embedding_function=embeddings,
        client=client,
    )


def ingest_text(text: str, collection_name: str = "documents",
                 chunk_size: int = 1000, chunk_overlap: int = 200):
    """Ingesta texto en el vectorstore."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    chunks = splitter.create_documents([text])

    vectorstore = get_vectorstore(collection_name)
    vectorstore.add_documents(chunks)
    return len(chunks)


def query(question: str, collection_name: str = "documents",
          k: int = 4) -> str:
    """Query RAG: busca contexto y genera respuesta."""
    vectorstore = get_vectorstore(collection_name)
    retriever = vectorstore.as_retriever(search_kwargs={{"k": k}})

    docs = retriever.invoke(question)
    context = "\\n\\n".join(d.page_content for d in docs)

    llm = get_llm()
    prompt = ChatPromptTemplate.from_template("""
Basandote en el siguiente contexto, responde la pregunta.
Si no sabes la respuesta, di "No tengo informacion suficiente".

Contexto:
{{context}}

Pregunta: {{question}}

Respuesta:
""")
    chain = prompt | llm
    return chain.invoke({{"context": context, "question": question}})


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Uso: python rag_engine.py <pregunta>")
        print("     python rag_engine.py --ingest <archivo.txt>")
        sys.exit(1)

    if sys.argv[1] == "--ingest":
        filepath = sys.argv[2]
        text = Path(filepath).read_text()
        n = ingest_text(text)
        print(f"Ingestadas {{n}} chunks de {{filepath}}")
    else:
        question = " ".join(sys.argv[1:])
        answer = query(question)
        print(f"Pregunta: {{question}}")
        print(f"Respuesta: {{answer}}")
'''
    api_main = '''"""DevMind RAG Lab — API FastAPI.

Endpoints:
  POST /query — Hacer una pregunta RAG
  POST /ingest — Ingestar un documento
  GET /health — Health check
"""
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="DevMind RAG Lab", version="0.1.0")


class QueryRequest(BaseModel):
    question: str
    collection: str = "documents"
    k: int = 4


class IngestRequest(BaseModel):
    text: str
    collection: str = "documents"
    chunk_size: int = 1000


@app.get("/health")
async def health():
    return {"status": "ok", "service": "devmind-rag-lab"}


@app.post("/query")
async def query_rag(req: QueryRequest):
    from rag_engine import query
    answer = query(req.question, req.collection, req.k)
    return {"question": req.question, "answer": str(answer)}


@app.post("/ingest")
async def ingest(req: IngestRequest):
    from rag_engine import ingest_text
    n = ingest_text(req.text, req.collection, req.chunk_size)
    return {"chunks_ingested": n, "collection": req.collection}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
'''
    readme_content = f"""# RAG Lab — DevMind Setup

Stack de Retrieval-Augmented Generation con Ollama + ChromaDB + FastAPI.

## Que se instaló

- **Docker Compose**: Ollama + ChromaDB
- **rag_engine.py**: Motor RAG (ingest + query)
- **api.py**: API FastAPI para RAG
- **Modelo**: {model} + nomic-embed-text (embeddings)

## Iniciar

```bash
# 1. Levantar servicios Docker
docker compose up -d

# 2. Instalar dependencias
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. Descargar modelos
ollama pull {model}
ollama pull nomic-embed-text

# 4. Probar
python rag_engine.py "que es machine learning?"
```

## API

```bash
# Iniciar API
uvicorn api:app --reload --port 8001

# Query
curl -X POST http://localhost:8001/query \\
  -H "Content-Type: application/json" \\
  -d '{{"question": "que es RAG?"}}'

# Ingestar documento
curl -X POST http://localhost:8001/ingest \\
  -H "Content-Type: application/json" \\
  -d '{{"text": "Tu documento aqui..."}}'
```

## Servicios

| Servicio | URL | Descripcion |
|----------|-----|-------------|
| Ollama | http://localhost:11434 | Motor LLM |
| ChromaDB | http://localhost:8000 | Vector store |
| RAG API | http://localhost:8001 | API de consultas |

Generado por [DevMind](https://github.com/eminem5410/devmind-platform) v0.4.0
"""
    return SetupProfile(
        name="rag-lab",
        description="Stack RAG: Ollama + ChromaDB + FastAPI para retrieval-augmented generation",
        min_ram_gb=4.0,
        min_disk_gb=15.0,
        needs_docker=True,
        needs_ollama=True,
        files={
            "docker-compose.yml": docker_compose,
            "requirements.txt": requirements,
            "rag_engine.py": rag_engine,
            "api.py": api_main,
            ".env": f"DEFAULT_MODEL={model}\nCHROMA_URL=http://localhost:8000\nOLLAMA_URL=http://localhost:11434\n",
            "README.md": readme_content,
        },
        post_setup_commands=[
            "docker compose up -d",
            f"ollama pull {model}",
            "ollama pull nomic-embed-text",
            "echo 'Instala deps: source .venv/bin/activate && pip install -r requirements.txt'",
        ],
    )


# ── Registry ────────────────────────────────────────────────────────────

PROFILES: dict[str, callable] = {
    "local-llm": generate_local_llm_profile,
    "ai-dev": generate_ai_dev_profile,
    "rag-lab": generate_rag_lab_profile,
}


def get_available_profiles() -> list[dict]:
    """Retorna la lista de perfiles disponibles con metadata."""
    return [
        {
            "name": "local-llm",
            "description": "Chat local con LLM: Ollama + OpenWebUI",
            "needs": ["Docker"],
        },
        {
            "name": "ai-dev",
            "description": "Entorno completo AI: Docker + Ollama + Jupyter + deps",
            "needs": ["Docker", "Ollama"],
        },
        {
            "name": "rag-lab",
            "description": "Stack RAG: Ollama + ChromaDB + FastAPI",
            "needs": ["Docker", "Ollama"],
        },
    ]


def generate_profile(name: str, ram_gb: float, has_gpu: bool,
                     ollama_version: str | None = None,
                     python_version: str = "3.12") -> SetupProfile:
    """Genera un perfil con los parametros del sistema."""
    if name not in PROFILES:
        raise ValueError(f"Perfil desconocido: {name}. Disponibles: {list(PROFILES.keys())}")
    return PROFILES[name](ram_gb, has_gpu, ollama_version, python_version)
