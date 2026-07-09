from pathlib import Path
from uuid import uuid4
from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from .config import UPLOAD_DIR, settings
from .database import Base, engine, get_db
from .matching import MatchingService, to_case_out
from .models import AuditLog, CaseRecord
from .schemas import AuditOut, CaseOut, SearchResponse
from .vector_index import VectorIndexService
from .vision import VisionError


Base.metadata.create_all(bind=engine)
app = FastAPI(title="Punarmilan Matching API", version="0.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[],
    allow_origin_regex=r"https?://(127\.0\.0\.1|localhost):\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/media", StaticFiles(directory=str(UPLOAD_DIR)), name="media")


def require_reviewer(authorization: str | None = Header(default=None)) -> str:
    expected = f"Bearer {settings.reviewer_token}"
    if authorization != expected:
        raise HTTPException(status_code=401, detail="Reviewer authentication required for matching results.")
    return "demo-reviewer"


def save_upload(upload: UploadFile) -> Path:
    suffix = Path(upload.filename or "upload.jpg").suffix.lower() or ".jpg"
    path = UPLOAD_DIR / f"{uuid4().hex}{suffix}"
    with path.open("wb") as f:
        f.write(upload.file.read())
    return path


def vision_error_to_http(error: VisionError) -> HTTPException:
    return HTTPException(status_code=422, detail={"code": error.code, "message": error.message, **error.detail})


@app.get("/health")
def health():
    return {"status": "ok", "data_policy": "SYNTHETIC DEMO DATA - LFW public dataset wrappers; no real case records."}


@app.get("/vector-index")
def vector_index_status(db: Session = Depends(get_db), reviewer_id: str = Depends(require_reviewer)):
    return VectorIndexService(db).status()


@app.post("/vector-index/rebuild")
def rebuild_vector_index(db: Session = Depends(get_db), reviewer_id: str = Depends(require_reviewer)):
    status = VectorIndexService(db).rebuild()
    db.add(
        AuditLog(
            reviewer_id=reviewer_id,
            role="Police/NGO reviewer",
            action="vector_index_rebuilt",
            case_id="system",
            detail=f"FAISS index rebuilt with {status.get('records', 0)} missing-record embeddings.",
        )
    )
    db.commit()
    return status


@app.get("/cases", response_model=list[CaseOut])
def list_cases(db: Session = Depends(get_db), reviewer_id: str = Depends(require_reviewer)):
    records = db.query(CaseRecord).order_by(CaseRecord.created_at.desc()).all()
    return [to_case_out(record) for record in records]


@app.post("/cases", response_model=CaseOut)
def create_case(
    report_type: str = Form(...),
    display_name: str = Form(...),
    age: int = Form(...),
    gender: str = Form(...),
    region: str = Form(...),
    location: str = Form(...),
    notes: str = Form(""),
    selected_face: int | None = Form(None),
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    reviewer_id: str = Depends(require_reviewer),
):
    try:
        service = MatchingService()
        record = service.create_case(
            db,
            image_path=save_upload(image),
            report_type=report_type,
            display_name=display_name,
            age=age,
            gender=gender,
            region=region,
            location=location,
            notes=notes,
            selected_face=selected_face,
        )
        return to_case_out(record)
    except VisionError as error:
        raise vision_error_to_http(error)
    except FileNotFoundError as error:
        raise HTTPException(status_code=503, detail=str(error))


@app.post("/search", response_model=SearchResponse)
def search_candidates(
    age: int | None = Form(None),
    gender: str | None = Form(None),
    region: str | None = Form(None),
    selected_face: int | None = Form(None),
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    reviewer_id: str = Depends(require_reviewer),
):
    try:
        service = MatchingService()
        return service.search_image(
            db,
            image_path=save_upload(image),
            age=age,
            gender=gender,
            region=region,
            selected_face=selected_face,
            top_k=settings.top_k,
            reviewer_id=reviewer_id,
        )
    except VisionError as error:
        raise vision_error_to_http(error)
    except FileNotFoundError as error:
        raise HTTPException(status_code=503, detail=str(error))


@app.post("/review-actions", response_model=AuditOut)
def review_action(
    action: str = Form(...),
    case_id: str = Form(...),
    candidate_case_id: str = Form(...),
    similarity_score: float = Form(...),
    db: Session = Depends(get_db),
    reviewer_id: str = Depends(require_reviewer),
):
    try:
        service = MatchingService()
        log = service.log_action(
            db,
            reviewer_id=reviewer_id,
            action=action,
            case_id=case_id,
            candidate_case_id=candidate_case_id,
            similarity_score=similarity_score,
        )
        return log
    except VisionError as error:
        raise vision_error_to_http(error)


@app.get("/audit", response_model=list[AuditOut])
def audit_log(db: Session = Depends(get_db), reviewer_id: str = Depends(require_reviewer)):
    records = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(50).all()
    return records
