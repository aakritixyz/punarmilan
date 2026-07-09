import numpy as np

from app.vector_index import build_faiss_index
from app.vision import serialize_embedding


class DummyRecord:
    def __init__(self, vector):
        self.embedding = serialize_embedding(np.array(vector, dtype="float32"))
        self.embedding_dim = len(vector)


def test_faiss_index_returns_nearest_inner_product_neighbor():
    records = [
        DummyRecord([1.0, 0.0, 0.0]),
        DummyRecord([0.0, 1.0, 0.0]),
        DummyRecord([0.0, 0.0, 1.0]),
    ]
    index, _ = build_faiss_index(records)
    query = np.array([[0.9, 0.1, 0.0]], dtype="float32")
    import faiss

    faiss.normalize_L2(query)
    distances, indices = index.search(query, 3)
    assert indices[0][0] == 0
    assert distances[0][0] > distances[0][1]
