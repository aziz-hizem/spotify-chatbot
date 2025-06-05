import json
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

# === Step 1: Load endpoints ===
with open("data/endpoints.json", "r", encoding="utf-8") as f:
    endpoints = json.load(f)

# === Step 2: Convert each endpoint into a readable chunk ===
def make_text_chunk(ep):
    lines = []

    # Add the title and URL
    lines.append(f"Title: {ep['title']}")
    lines.append(f"URL: {ep['url']}")

    # Include method + path if available
    if ep.get("method") and ep.get("path"):
        lines.append(f"Method: {ep['method']} {ep['path']}")

    if ep.get("description"):
        lines.append(f"Description: {ep['description']}")

    # Add scopes
    if ep.get("scopes"):
        lines.append("Scopes:")
        lines.extend([f"  - {s}" for s in ep["scopes"]])

    # Add parameters
    if ep.get("parameters"):
        lines.append("Parameters:")
        for name, desc in ep["parameters"].items():
            lines.append(f"  - {name}: {desc}")

    return "\n".join(lines)

docs = []
metadatas = []
ids = []

for i, ep in enumerate(endpoints):
    text = make_text_chunk(ep)
    docs.append(text)
    metadatas.append({
        "title": ep.get("title", ""),
        "url": ep.get("url", "")
    })
    ids.append(f"doc_{i}")

# Optional debug: save to file
with open("data/chunks.json", "w", encoding="utf-8") as f:
    json.dump(docs, f, indent=2, ensure_ascii=False)

# === Step 3: Embed chunks using SentenceTransformer ===
print("Loading embedding model...")
model = SentenceTransformer("all-MiniLM-L6-v2")  # Small & fast

print(f"Embedding {len(docs)} chunks...")
embeddings = model.encode(docs, show_progress_bar=True)

# === Step 4: Store in ChromaDB ===
print("Creating vector DB...")
client = chromadb.PersistentClient(path="data/chroma/")

# Clear collection by recreating it instead of using delete
try:
    client.delete_collection("spotify_docs")
except:
    pass  # Ignore if collection doesn't exist

collection = client.get_or_create_collection(name="spotify_docs")

# Add embeddings
collection.add(
    documents=docs,
    embeddings=embeddings.tolist(),  # Convert numpy array to list
    metadatas=metadatas,
    ids=ids
)

print(f"✅ All done. Stored {len(docs)} documents in vector DB.")