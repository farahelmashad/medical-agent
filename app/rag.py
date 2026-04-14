import os
import json
from pathlib import Path
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct
from sentence_transformers import SentenceTransformer

load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

COLLECTION_NAME = "clinic_knowledge"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"   
VECTOR_SIZE= 384
DATA_PATH= Path(__file__).parent.parent / "data" / "doctors.json"

_client   = None
_embedder = None


def _get_client() -> QdrantClient:
    global _client
    if _client is None:
        _client = QdrantClient(
            url=os.getenv("QDRANT_URL"),
            api_key=os.getenv("QDRANT_API_KEY"),
        )
    return _client


def _get_embedder() -> SentenceTransformer:
    global _embedder
    if _embedder is None:
        _embedder = SentenceTransformer(EMBEDDING_MODEL)
    return _embedder


def _load_data() -> dict:
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _build_chunks(data: dict) -> list[dict]:
    chunks = []
    idx = 0

    for doctor in data["doctors"]:
        text = (
            f"Doctor: {doctor['name']}\n"
            f"Specialization: {doctor['specialization']}\n"
            f"Bio: {doctor['bio']}\n"
            f"Working Days: {', '.join(doctor['working_days'])}\n"
            f"Working Hours: {doctor['working_hours']}\n"
            f"Slot Duration: {doctor['slot_duration_minutes']} minutes\n"
            f"Consultation Fee: {doctor['consultation_fee']}"
        )
        chunks.append({"id": idx, "text": text, "type": "doctor", "name": doctor["name"]})
        idx += 1

    for faq in data["faqs"]:
        text = f"Question: {faq['question']}\nAnswer: {faq['answer']}"
        chunks.append({"id": idx, "text": text, "type": "faq"})
        idx += 1

    return chunks


def build_index():
    client= _get_client()
    embedder = _get_embedder()
    data= _load_data()
    chunks= _build_chunks(data)

    if client.collection_exists(COLLECTION_NAME):
        return

    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
    )

    texts= [c["text"] for c in chunks]
    embeddings = embedder.encode(texts, show_progress_bar=False).tolist()

    points = [
        PointStruct(
            id=chunk["id"],
            vector=embedding,
            payload={"text": chunk["text"], "type": chunk["type"]},
        )
        for chunk, embedding in zip(chunks, embeddings)
    ]

    client.upsert(collection_name=COLLECTION_NAME, points=points)


def force_rebuild_index():
    client = _get_client()
    if client.collection_exists(COLLECTION_NAME):
        client.delete_collection(COLLECTION_NAME)
        print("[RAG] Existing collection deleted.")
    build_index()


def search(query: str, top_k: int = 3) -> str:
    client   = _get_client()
    embedder = _get_embedder()

    query_vector = embedder.encode(query, show_progress_bar=False).tolist()

    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        limit=top_k,
    ).points

    if not results:
        return "No relevant information found."

    context = "\n\n---\n\n".join(r.payload["text"] for r in results)
    return context


if __name__ == "__main__":
    build_index()
