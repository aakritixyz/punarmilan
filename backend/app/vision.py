from dataclasses import dataclass
from pathlib import Path
import cv2
import numpy as np

from .config import OPENFACE_MODEL, settings


class VisionError(ValueError):
    def __init__(self, code: str, message: str, detail: dict | None = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.detail = detail or {}


@dataclass
class FaceResult:
    face: np.ndarray
    box: tuple[int, int, int, int]
    blur_variance: float
    brightness: float


def read_image(path: str | Path) -> np.ndarray:
    image = cv2.imread(str(path))
    if image is None:
        raise VisionError("invalid_image", "The uploaded file could not be read as an image.")
    return image


def quality_metrics(image: np.ndarray) -> tuple[float, float]:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blur = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    brightness = float(gray.mean())
    return blur, brightness


def _largest_centered_faces(faces: np.ndarray) -> list[tuple[int, int, int, int]]:
    boxes = [tuple(map(int, face)) for face in faces]
    return sorted(boxes, key=lambda box: box[2] * box[3], reverse=True)


def detect_faces(image: np.ndarray) -> list[tuple[int, int, int, int]]:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    detector = cv2.CascadeClassifier(cascade_path)
    faces = detector.detectMultiScale(gray, scaleFactor=1.08, minNeighbors=5, minSize=(38, 38))
    return _largest_centered_faces(faces)


def crop_and_align(image: np.ndarray, box: tuple[int, int, int, int], size: int = 96) -> np.ndarray:
    x, y, w, h = box
    pad_x = int(w * 0.22)
    pad_y = int(h * 0.28)
    x0 = max(0, x - pad_x)
    y0 = max(0, y - pad_y)
    x1 = min(image.shape[1], x + w + pad_x)
    y1 = min(image.shape[0], y + h + pad_y)
    crop = image[y0:y1, x0:x1]
    if crop.size == 0:
        raise VisionError("invalid_face_crop", "The detected face crop was empty.")
    return cv2.resize(crop, (size, size), interpolation=cv2.INTER_AREA)


def preprocess_face(path: str | Path, selected_face: int | None = None) -> FaceResult:
    image = read_image(path)
    blur, brightness = quality_metrics(image)
    if blur < settings.min_blur_variance:
        raise VisionError(
            "image_too_blurry",
            "The image is too blurry for reliable face matching. Please upload a clearer photo.",
            {"blur_variance": blur, "minimum": settings.min_blur_variance},
        )
    if brightness < settings.min_brightness:
        raise VisionError(
            "image_too_dark",
            "The image is too dark for reliable face matching. Please upload a brighter photo.",
            {"brightness": brightness, "minimum": settings.min_brightness},
        )
    if brightness > settings.max_brightness:
        raise VisionError(
            "image_too_bright",
            "The image is overexposed for reliable face matching. Please upload a clearer photo.",
            {"brightness": brightness, "maximum": settings.max_brightness},
        )

    faces = detect_faces(image)
    if not faces:
        raise VisionError("no_face_detected", "No face was detected in the photo. Please upload a front-facing image.")
    if len(faces) > 1 and selected_face is None:
        raise VisionError(
            "multiple_faces_detected",
            "Multiple faces were detected. Please select the child face before continuing.",
            {"faces": [{"index": i, "box": box} for i, box in enumerate(faces)]},
        )
    index = selected_face or 0
    if index >= len(faces):
        raise VisionError("invalid_face_selection", "The selected face index is not present in this image.")
    face = crop_and_align(image, faces[index])
    return FaceResult(face=face, box=faces[index], blur_variance=blur, brightness=brightness)


class OpenFaceEmbedder:
    """Real pretrained embedding backend using OpenFace's nn4.small2.v1.t7 model."""

    def __init__(self, model_path: Path = OPENFACE_MODEL):
        if not model_path.exists():
            raise FileNotFoundError(
                f"Missing pretrained embedding model: {model_path}. "
                "Run backend/scripts/download_models.py before seeding or searching."
            )
        self.net = cv2.dnn.readNetFromTorch(str(model_path))

    def embed(self, face_bgr: np.ndarray) -> np.ndarray:
        resized = cv2.resize(face_bgr, (96, 96), interpolation=cv2.INTER_AREA)
        blob = cv2.dnn.blobFromImage(resized, 1.0 / 255, (96, 96), (0, 0, 0), swapRB=True, crop=False)
        self.net.setInput(blob)
        vector = self.net.forward().flatten().astype("float32")
        norm = np.linalg.norm(vector)
        if norm == 0:
            raise VisionError("embedding_failed", "The embedding model returned an empty vector.")
        return vector / norm


def region_signature(face_bgr: np.ndarray) -> dict[str, float]:
    gray = cv2.cvtColor(cv2.resize(face_bgr, (96, 96)), cv2.COLOR_BGR2GRAY).astype("float32") / 255.0
    regions = {
        "upper_face": gray[:32, :].mean(),
        "mid_face": gray[32:64, :].mean(),
        "lower_face": gray[64:, :].mean(),
    }
    return {key: round(float(value), 4) for key, value in regions.items()}


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b) / ((np.linalg.norm(a) * np.linalg.norm(b)) or 1.0))


def serialize_embedding(vector: np.ndarray) -> bytes:
    return vector.astype("float32").tobytes()


def deserialize_embedding(raw: bytes, dim: int) -> np.ndarray:
    return np.frombuffer(raw, dtype="float32", count=dim)
