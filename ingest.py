"""Build the knowledge base: load docs -> chunk -> embed -> store.

Run this whenever you change anything in the data/ folder:
    python ingest.py
"""
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

from rag import config
from rag.chunking import chunk_text


def build_index():
    data_dir = Path(config.DATA_DIR)
    files = sorted(list(data_dir.glob("*.md")) + list(data_dir.glob("*.txt")))
    if not files:
        raise SystemExit(f"No .md or .txt files found in {data_dir.resolve()}")

    ids, texts, metas = [], [], []
    for path in files:
        for i, chunk in enumerate(chunk_text(path.read_text(encoding="utf-8"))):
            ids.append(f"{path.name}::{i}")
            texts.append(chunk)
            metas.append({"source": path.name, "chunk": i})
        print(f"  {path.name}")

    print(f"Embedding {len(texts)} chunks with {config.EMBED_MODEL} ...")
    embedder = SentenceTransformer(config.EMBED_MODEL)
    vectors = embedder.encode(texts, normalize_embeddings=True).tolist()

    client = chromadb.PersistentClient(path=config.DB_DIR)
    try:
        client.delete_collection(config.COLLECTION)  # rebuild from scratch
    except Exception:
        pass
    collection = client.create_collection(
        config.COLLECTION, metadata={"hnsw:space": "cosine"}
    )
    collection.add(ids=ids, documents=texts, embeddings=vectors, metadatas=metas)
    print(f"Done. {len(texts)} chunks from {len(files)} files stored in {config.DB_DIR}/")


if __name__ == "__main__":
    build_index()
