from datetime import datetime
from pydantic import BaseModel


class CaseOut(BaseModel):
    case_id: str
    report_type: str
    display_name: str
    age: int
    gender: str
    region: str
    location: str
    notes: str
    status: str
    image_url: str
    face_url: str


class CandidateOut(BaseModel):
    rank: int
    case: CaseOut
    similarity_score: float
    confidence_label: str
    metadata_adjustment: float
    explanation: dict[str, float]


class SearchResponse(BaseModel):
    query_case_id: str | None = None
    coverage: dict[str, int | str]
    candidates: list[CandidateOut]


class AuditOut(BaseModel):
    timestamp: datetime
    reviewer_id: str
    role: str
    action: str
    case_id: str
    candidate_case_id: str | None
    similarity_score: float | None
    detail: str
