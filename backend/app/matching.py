from pathlib import Path
from uuid import uuid4
import cv2
from sqlalchemy.orm import Session

from .config import UPLOAD_DIR
from .models import AuditLog, CaseRecord
from .schemas import CandidateOut, CaseOut, SearchResponse
from .vector_index import VectorIndexService, build_faiss_index
from .vision import (
    OpenFaceEmbedder,
    VisionError,
    deserialize_embedding,
    preprocess_face,
    region_signature,
    serialize_embedding,
)


def confidence_label(score: float) -> str:
    if score >= 70:
        return "review recommended"
    if score >= 50:
        return "needs more info"
    return "low priority"


def similarity_percent(cosine: float) -> float:
    return round(max(0.0, min(100.0, (cosine + 1.0) * 50.0)), 1)


def metadata_adjustment(query: dict, candidate: CaseRecord) -> float:
    adjustment = 0.0
    if query.get("gender") and candidate.gender.lower() != str(query["gender"]).lower():
        adjustment -= 8.0
    if query.get("age") is not None:
        age_gap = abs(int(query["age"]) - candidate.age)
        if age_gap > 2:
            adjustment -= min(14.0, (age_gap - 2) * 2.5)
    if query.get("region") and candidate.region.lower() != str(query["region"]).lower():
        adjustment -= 4.0
    return adjustment


def to_case_out(record: CaseRecord) -> CaseOut:
    return CaseOut(
        case_id=record.case_id,
        report_type=record.report_type,
        display_name=record.display_name,
        age=record.age,
        gender=record.gender,
        region=record.region,
        location=record.location,
        notes=record.notes,
        status=record.status,
        image_url=f"/media/{Path(record.image_path).name}",
        face_url=f"/media/{Path(record.face_path).name}",
    )


class MatchingService:
    def __init__(self):
        self.embedder = OpenFaceEmbedder()

    def create_case(
        self,
        db: Session,
        *,
        image_path: Path,
        report_type: str,
        display_name: str,
        age: int,
        gender: str,
        region: str,
        location: str,
        notes: str = "",
        selected_face: int | None = None,
    ) -> CaseRecord:
        face_result = preprocess_face(image_path, selected_face=selected_face)
        vector = self.embedder.embed(face_result.face)
        case_id = f"PM-DEMO-{uuid4().hex[:8].upper()}"
        face_path = UPLOAD_DIR / f"{case_id}_face.jpg"
        cv2.imwrite(str(face_path), face_result.face)
        record = CaseRecord(
            case_id=case_id,
            report_type=report_type,
            display_name=display_name,
            age=age,
            gender=gender,
            region=region,
            location=location,
            notes=notes,
            status="open",
            image_path=str(image_path),
            face_path=str(face_path),
            embedding=serialize_embedding(vector),
            embedding_dim=int(vector.shape[0]),
            blur_variance=face_result.blur_variance,
            brightness=face_result.brightness,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    def search_image(
        self,
        db: Session,
        *,
        image_path: Path,
        age: int | None = None,
        gender: str | None = None,
        region: str | None = None,
        selected_face: int | None = None,
        top_k: int = 10,
        reviewer_id: str = "demo-reviewer",
    ) -> SearchResponse:
        face_result = preprocess_face(image_path, selected_face=selected_face)
        query_vector = self.embedder.embed(face_result.face)
        query_regions = region_signature(face_result.face)
        query_meta = {"age": age, "gender": gender, "region": region}
        records = db.query(CaseRecord).filter(CaseRecord.report_type == "missing").all()
        ranked: list[CandidateOut] = []
        index_service = VectorIndexService(db)
        hits, index_status = index_service.search(query_vector, top_k=min(top_k * 3, max(1, len(records))))
        for hit in hits:
            record = hit.record
            raw = hit.raw_similarity
            score = similarity_percent(raw)
            adjustment = metadata_adjustment(query_meta, record)
            adjusted_score = round(max(0.0, min(100.0, score + adjustment)), 1)
            candidate_face = cv2.imread(record.face_path)
            candidate_regions = region_signature(candidate_face) if candidate_face is not None else query_regions
            explanation = {
                key: round(max(0.0, 100.0 - abs(query_regions[key] - candidate_regions[key]) * 100.0), 1)
                for key in query_regions
            }
            ranked.append(
                CandidateOut(
                    rank=0,
                    case=to_case_out(record),
                    similarity_score=adjusted_score,
                    confidence_label=confidence_label(adjusted_score),
                    metadata_adjustment=round(adjustment, 1),
                    explanation=explanation,
                )
            )
        ranked.sort(key=lambda item: item.similarity_score, reverse=True)
        ranked = ranked[:top_k]
        for index, item in enumerate(ranked, start=1):
            item.rank = index
        db.add(
            AuditLog(
                reviewer_id=reviewer_id,
                role="Police/NGO reviewer",
                action="candidate_search",
                case_id="uploaded-query",
                detail=f"Search covered {len(records)} stored missing-child demo records.",
            )
        )
        db.commit()
        return SearchResponse(
            coverage={
                "searched_records": len(records),
                "returned_candidates": len(ranked),
                "vector_index": "faiss.IndexFlatIP",
                "index_records": index_status.get("mapped_case_ids", 0),
                "persisted_index": index_status.get("index_exists", False),
                "note": "Ranked candidates only; no automatic identification is made.",
            },
            candidates=ranked,
        )

    def log_action(
        self,
        db: Session,
        *,
        reviewer_id: str,
        action: str,
        case_id: str,
        candidate_case_id: str,
        similarity_score: float,
    ) -> AuditLog:
        if action not in {"confirm_candidate", "reject_candidate", "escalate_candidate"}:
            raise VisionError("invalid_action", "Reviewer action must be confirm, reject, or escalate.")
        log = AuditLog(
            reviewer_id=reviewer_id,
            role="Police/NGO reviewer",
            action=action,
            case_id=case_id,
            candidate_case_id=candidate_case_id,
            similarity_score=similarity_score,
            detail="Reviewer decision recorded with displayed similarity score.",
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        return log
