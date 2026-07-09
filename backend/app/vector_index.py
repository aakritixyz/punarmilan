import json
from dataclasses import dataclass

import faiss
import numpy as np
from sqlalchemy.orm import Session

from .config import FAISS_INDEX_PATH, FAISS_MAP_PATH
from .models import CaseRecord
from .vision import deserialize_embedding


@dataclass
class SearchHit:
    record: CaseRecord
    raw_similarity: float


def _vectors_for(records: list[CaseRecord]) -> np.ndarray:
    vectors = np.vstack([deserialize_embedding(record.embedding, record.embedding_dim) for record in records]).astype("float32")
    faiss.normalize_L2(vectors)
    return vectors


def build_faiss_index(records: list[CaseRecord]) -> tuple[faiss.IndexFlatIP | None, np.ndarray]:
    if not records:
        return None, np.empty((0, 0), dtype="float32")
    vectors = _vectors_for(records)
    index = faiss.IndexFlatIP(vectors.shape[1])
    index.add(vectors)
    return index, vectors


class VectorIndexService:
    """FAISS index manager for stored missing-child embeddings."""

    def __init__(self, db: Session):
        self.db = db

    def records(self) -> list[CaseRecord]:
        return self.db.query(CaseRecord).filter(CaseRecord.report_type == "missing").order_by(CaseRecord.id).all()

    def rebuild(self) -> dict:
        records = self.records()
        index, _vectors = build_faiss_index(records)
        if index is None:
            if FAISS_INDEX_PATH.exists():
                FAISS_INDEX_PATH.unlink()
            FAISS_MAP_PATH.write_text("[]")
            return {"records": 0, "index_path": str(FAISS_INDEX_PATH), "map_path": str(FAISS_MAP_PATH)}
        faiss.write_index(index, str(FAISS_INDEX_PATH))
        FAISS_MAP_PATH.write_text(json.dumps([record.case_id for record in records], indent=2))
        return {
            "records": len(records),
            "dimension": index.d,
            "index_path": str(FAISS_INDEX_PATH),
            "map_path": str(FAISS_MAP_PATH),
            "index_type": "faiss.IndexFlatIP",
        }

    def status(self) -> dict:
        records = self.records()
        mapped = []
        if FAISS_MAP_PATH.exists():
            mapped = json.loads(FAISS_MAP_PATH.read_text() or "[]")
        return {
            "stored_missing_records": len(records),
            "index_exists": FAISS_INDEX_PATH.exists(),
            "mapped_case_ids": len(mapped),
            "index_path": str(FAISS_INDEX_PATH),
            "map_path": str(FAISS_MAP_PATH),
            "index_type": "faiss.IndexFlatIP",
        }

    def search(self, query_vector: np.ndarray, top_k: int) -> tuple[list[SearchHit], dict]:
        records = self.records()
        if not records:
            return [], self.status()

        # Rebuild on demand when the persisted artifact is missing or stale.
        mapped = []
        if FAISS_MAP_PATH.exists():
            mapped = json.loads(FAISS_MAP_PATH.read_text() or "[]")
        current_ids = [record.case_id for record in records]
        if not FAISS_INDEX_PATH.exists() or mapped != current_ids:
            self.rebuild()

        index = faiss.read_index(str(FAISS_INDEX_PATH))
        query = query_vector.astype("float32").reshape(1, -1)
        faiss.normalize_L2(query)
        distances, indices = index.search(query, min(top_k, len(records)))
        hits = [
            SearchHit(record=records[int(idx)], raw_similarity=float(distances[0][pos]))
            for pos, idx in enumerate(indices[0])
            if idx >= 0
        ]
        status = self.status()
        status["searched_with_persisted_index"] = True
        return hits, status
