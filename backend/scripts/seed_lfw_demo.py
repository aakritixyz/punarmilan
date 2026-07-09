from pathlib import Path
import random
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from app.config import UPLOAD_DIR
from app.database import Base, SessionLocal, engine
from app.matching import MatchingService
from app.models import CaseRecord


NAMES = [
    ("Arjun Sharma", "Delhi", "Connaught Place Metro Station", "Male", 8),
    ("Priya Patel", "Maharashtra", "Dadar Railway Station", "Female", 12),
    ("Rahul Kumar", "West Bengal", "Sealdah station area", "Male", 6),
    ("Sneha Gupta", "Tamil Nadu", "Chennai bus stand", "Female", 10),
    ("Aisha Begum", "Uttar Pradesh", "Lucknow shelter intake", "Female", 9),
    ("Kabir Khan", "Rajasthan", "Jaipur railway platform", "Male", 11),
]


def lfw_images(limit: int = 12) -> list[Path]:
    data_root = ROOT / "data" / "lfw"
    root = data_root / "lfw"
    if not root.exists():
        root = data_root / "lfw_funneled"
    if not root.exists():
        raise SystemExit("LFW is not downloaded. Run: python backend/scripts/download_lfw.py")
    people = [p for p in root.iterdir() if p.is_dir()]
    random.seed(7)
    random.shuffle(people)
    images: list[Path] = []
    for person in people:
        files = sorted(person.glob("*.jpg"))
        if files:
            images.append(files[0])
        if len(images) >= limit:
            break
    return images


def main():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    if db.query(CaseRecord).count():
        print("Database already has case records; not reseeding.")
        return
    service = MatchingService()
    for index, src in enumerate(lfw_images(len(NAMES))):
        name, region, location, gender, age = NAMES[index]
        target = UPLOAD_DIR / f"lfw_demo_{index}_{src.name}"
        shutil.copyfile(src, target)
        record = service.create_case(
            db,
            image_path=target,
            report_type="missing",
            display_name=name,
            age=age,
            gender=gender,
            region=region,
            location=location,
            notes="SYNTHETIC DEMO DATA wrapper around an LFW public benchmark photo; not a real case record.",
        )
        print(f"Seeded {record.case_id}: {name}")
    db.close()


if __name__ == "__main__":
    main()
