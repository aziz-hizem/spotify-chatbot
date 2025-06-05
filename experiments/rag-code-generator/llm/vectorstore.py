# spotify_chatbot/llm/vectorstore.py
from chromadb import Client
from chromadb.config import Settings
import chromadb.utils.embedding_functions
import json
import os

CHUNKS_PATH = "data/chunks.json"
COLLECTION_NAME = "spotify_api"

def get_chroma_client():
    return Client(Settings(
        persist_directory="./.chroma",
        anonymized_telemetry=False
    ))

def embed_chunks():
    client = get_chroma_client()
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=chromadb.utils.embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
    )

    if not collection.count():
        with open(CHUNKS_PATH, "r", encoding="utf-8") as f:
            chunks = json.load(f)

        collection.add(
            documents=chunks,
            ids=[f"doc_{i}" for i in range(len(chunks))]
        )
        print("✅ Embedded chunks into ChromaDB")
    else:
        print("✅ ChromaDB already populated")

    return collection

def query_relevant_docs(query: str, n_results: int = 5) -> list[str]:
    collection = embed_chunks()
    results = collection.query(query_texts=[query], n_results=n_results)
    return results["documents"][0]
