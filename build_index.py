import json
import pickle
import numpy as np

def build_index():
    with open("catalog.json", "r", encoding="utf-8") as f:
        catalog = json.load(f)

    print(f"Loaded {len(catalog)} assessments")

    try:
        from sentence_transformers import SentenceTransformer
        import faiss
    except ImportError:
        print("pip install sentence-transformers faiss-cpu")
        return

    model = SentenceTransformer("all-MiniLM-L6-v2")

    def make_text(a):
        # richer text = better retrieval accuracy
        parts = [a["name"]]
        if a.get("test_type") and a["test_type"] != "Unknown":
            parts.append(f"Type: {a['test_type']}")
        if a.get("description"):
            parts.append(a["description"])
        return ". ".join(parts)

    texts = [make_text(a) for a in catalog]

    print("Embedding assessments...")
    embeddings = model.encode(texts, normalize_embeddings=True, show_progress_bar=True, batch_size=32)
    embeddings = np.array(embeddings, dtype="float32")

    # IndexFlatIP with normalized vectors = cosine similarity
    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings)

    faiss.write_index(index, "catalog.index")
    with open("catalog.pkl", "wb") as f:
        pickle.dump(catalog, f)

    print("Saved catalog.index and catalog.pkl")

    # quick sanity check
    test_query = "hiring a software developer with communication skills"
    q_vec = model.encode([test_query], normalize_embeddings=True).astype("float32")
    scores, ids = index.search(q_vec, 5)
    print(f"\nTop 5 for: '{test_query}'")
    for score, idx in zip(scores[0], ids[0]):
        print(f"  [{score:.3f}] {catalog[idx]['name']} — {catalog[idx]['test_type']}")


if __name__ == "__main__":
    build_index()