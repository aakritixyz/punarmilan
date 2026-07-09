from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parents[1]
MODEL_DIR = ROOT / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

OPENFACE_URL = "https://storage.cmusatyalab.org/openface-models/nn4.small2.v1.t7"
TARGET = MODEL_DIR / "nn4.small2.v1.t7"


def main():
    if TARGET.exists() and TARGET.stat().st_size > 1_000_000:
        print(f"Model already present: {TARGET}")
        return
    print(f"Downloading pretrained OpenFace embedding model to {TARGET}")
    with requests.get(OPENFACE_URL, stream=True, timeout=60) as response:
        response.raise_for_status()
        with TARGET.open("wb") as f:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)
    print("Done.")


if __name__ == "__main__":
    main()
