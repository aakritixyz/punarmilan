from pathlib import Path
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import OPENFACE_MODEL
from app.matching import MatchingService
from app.models import Base


DATA_ROOT = Path(__file__).resolve().parents[1] / "data" / "lfw"
LFW_ROOT = DATA_ROOT / "lfw"
if not LFW_ROOT.exists():
    LFW_ROOT = DATA_ROOT / "lfw_funneled"


def _lfw_pair():
    if not LFW_ROOT.exists():
        pytest.skip("LFW not downloaded. Run backend/scripts/download_lfw.py for full pipeline tests.")
    for person_dir in LFW_ROOT.iterdir():
        files = sorted(person_dir.glob("*.jpg"))
        if len(files) >= 2:
            return files[0], files[1]
    pytest.skip("LFW is present but no identity with two photos was found.")


@pytest.mark.skipif(not OPENFACE_MODEL.exists(), reason="OpenFace model not downloaded")
def test_same_lfw_identity_returns_as_candidate(tmp_path):
    db_path = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    first, second = _lfw_pair()
    Base.metadata.create_all(bind=engine)
    db = TestingSession()
    service = MatchingService()
    record = service.create_case(
        db,
        image_path=first,
        report_type="missing",
        display_name="Synthetic LFW person",
        age=10,
        gender="unknown",
        region="Delhi",
        location="Synthetic demo",
        notes="SYNTHETIC DEMO DATA - LFW public dataset",
    )
    response = service.search_image(db, image_path=second, age=12, gender="unknown", region="Maharashtra", top_k=10)
    assert response.coverage["searched_records"] == 1
    assert response.candidates
    assert response.candidates[0].case.case_id == record.case_id
    assert response.candidates[0].confidence_label in {"review recommended", "needs more info", "low priority"}
    db.close()


@pytest.mark.skipif(not OPENFACE_MODEL.exists(), reason="OpenFace model not downloaded")
def test_zero_results_has_coverage_metadata(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'empty.db'}", connect_args={"check_same_thread": False})
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)
    db = TestingSession()
    service = MatchingService()
    first, _ = _lfw_pair()
    response = service.search_image(db, image_path=first, top_k=10)
    assert response.coverage["searched_records"] == 0
    assert response.candidates == []
    db.close()
