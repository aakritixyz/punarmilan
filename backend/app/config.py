from pathlib import Path
from pydantic import BaseModel
import os


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
INDEX_DIR = DATA_DIR / "indexes"
MODEL_DIR = ROOT / "models"
OPENFACE_MODEL = MODEL_DIR / "nn4.small2.v1.t7"
FAISS_INDEX_PATH = INDEX_DIR / "missing_faces.faiss"
FAISS_MAP_PATH = INDEX_DIR / "missing_faces_map.json"


class Settings(BaseModel):
    database_url: str = os.getenv("DATABASE_URL", f"sqlite:///{DATA_DIR / 'punarmilan.db'}")
    reviewer_token: str = os.getenv("REVIEWER_TOKEN", "demo-reviewer-token")
    min_blur_variance: float = float(os.getenv("MIN_BLUR_VARIANCE", "45"))
    min_brightness: float = float(os.getenv("MIN_BRIGHTNESS", "35"))
    max_brightness: float = float(os.getenv("MAX_BRIGHTNESS", "235"))
    top_k: int = int(os.getenv("TOP_K", "10"))


settings = Settings()
DATA_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
INDEX_DIR.mkdir(parents=True, exist_ok=True)
MODEL_DIR.mkdir(parents=True, exist_ok=True)
