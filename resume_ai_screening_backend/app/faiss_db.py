import faiss
import numpy as np
import os

FAISS_INDEX_PATH = 'data/faiss_index/resume.index'
DIM = 384  # or whatever your embedding dimension is

def create_faiss_index(dim=DIM):
    os.makedirs('data/faiss_index', exist_ok=True)
    # Wrap IndexFlatL2 with IndexIDMap to support add_with_ids
    base_index = faiss.IndexFlatL2(dim)
    index = faiss.IndexIDMap(base_index)
    faiss.write_index(index, FAISS_INDEX_PATH)

def load_faiss_index():
    if not os.path.exists(FAISS_INDEX_PATH):
        create_faiss_index()
    return faiss.read_index(FAISS_INDEX_PATH)

def add_embedding_to_index(embedding, idx):
    index = load_faiss_index()
    embedding = np.array([embedding]).astype('float32')
    index.add_with_ids(embedding, np.array([idx], dtype='int64'))
    faiss.write_index(index, FAISS_INDEX_PATH)

def search_index(query_embedding, top_k=5):
    index = load_faiss_index()
    D, I = index.search(np.array([query_embedding]).astype('float32'), top_k)
    return I[0], D[0]
