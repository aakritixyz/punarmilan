import cv2
import numpy as np
import pytest

from app.config import settings
from app.vision import VisionError, preprocess_face, quality_metrics


def write_image(path, image):
    cv2.imwrite(str(path), image)
    return path


def test_blur_metric_drops_after_gaussian_blur():
    sharp = np.zeros((220, 220, 3), dtype=np.uint8)
    cv2.rectangle(sharp, (50, 50), (170, 170), (255, 255, 255), 2)
    cv2.line(sharp, (70, 80), (150, 80), (255, 255, 255), 3)
    blurred = cv2.GaussianBlur(sharp, (31, 31), 0)
    sharp_blur, _ = quality_metrics(sharp)
    blurred_blur, _ = quality_metrics(blurred)
    assert sharp_blur > blurred_blur


def test_too_dark_image_is_rejected(tmp_path):
    image = np.full((180, 180, 3), 5, dtype=np.uint8)
    path = write_image(tmp_path / "dark.jpg", image)
    with pytest.raises(VisionError) as exc:
        preprocess_face(path)
    assert exc.value.code == "image_too_blurry" or exc.value.code == "image_too_dark"


def test_no_face_image_is_rejected_after_quality_pass(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "min_blur_variance", 0)
    image = np.full((220, 220, 3), 180, dtype=np.uint8)
    cv2.line(image, (0, 0), (220, 220), (0, 0, 0), 2)
    path = write_image(tmp_path / "noface.jpg", image)
    with pytest.raises(VisionError) as exc:
        preprocess_face(path)
    assert exc.value.code == "no_face_detected"
