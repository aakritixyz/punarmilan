import numpy as np
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Base, CaseRecord
from app.vector_index import VectorIndexService
from app.vision import serialize_embedding


def test_vector_index_service_rebuilds_and_searches(tmp_path, monkeypatch):
    index_path = tmp_path / "faces.faiss"
    map_path = tmp_path / "faces.json"
    monkeypatch.setattr("app.vector_index.FAISS_INDEX_PATH", index_path)
    monkeypatch.setattr("app.vector_index.FAISS_MAP_PATH", map_path)

    engine = create_engine(f"sqlite:///{tmp_path / 'index.db'}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    db.add_all(
        [
            CaseRecord(
                case_id="PM-DEMO-A",
                report_type="missing",
                display_name="Synthetic A",
                age=8,
                gender="unknown",
                region="Delhi",
                location="Demo",
                notes="SYNTHETIC DEMO DATA",
                image_path="a.jpg",
                face_path="a_face.jpg",
                embedding=serialize_embedding(np.array([1.0, 0.0, 0.0], dtype="float32")),
                embedding_dim=3,
                blur_variance=100,
                brightness=100,
            ),
            CaseRecord(
                case_id="PM-DEMO-B",
                report_type="missing",
                display_name="Synthetic B",
                age=9,
                gender="unknown",
                region="Delhi",
                location="Demo",
                notes="SYNTHETIC DEMO DATA",
                image_path="b.jpg",
                face_path="b_face.jpg",
                embedding=serialize_embedding(np.array([0.0, 1.0, 0.0], dtype="float32")),
                embedding_dim=3,
                blur_variance=100,
                brightness=100,
            ),
        ]
    )
    db.commit()

    service = VectorIndexService(db)
    status = service.rebuild()
    assert status["records"] == 2
    assert Path(index_path).exists()
    assert Path(map_path).read_text().count("PM-DEMO") == 2

    hits, search_status = service.search(np.array([0.9, 0.1, 0.0], dtype="float32"), top_k=2)
    assert hits[0].record.case_id == "PM-DEMO-A"
    assert search_status["searched_with_persisted_index"] is True
    db.close()
