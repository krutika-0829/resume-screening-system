import numpy as np
import faiss


def create_faiss_index(model, chunks):
    texts = [chunk.page_content for chunk in chunks]

    embeddings = model.encode(texts)
    embeddings = np.array(embeddings).astype("float32")

    dimension = embeddings.shape[1]

    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)

    return index


def retrieve_chunks(query, model, index, chunks, k):
    query_embedding = model.encode(query)
    query_embedding = np.array([query_embedding]).astype("float32")

    distances, indices = index.search(query_embedding, k)

    retrieved_chunks = [chunks[i] for i in indices[0]]

    return retrieved_chunks