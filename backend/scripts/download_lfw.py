from pathlib import Path
import tarfile
import requests

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "lfw"
DATA_DIR.mkdir(parents=True, exist_ok=True)

LFW_URLS = [
    "https://vis-www.cs.umass.edu/lfw/lfw.tgz",
    "http://vis-www.cs.umass.edu/lfw/lfw.tgz",
    "https://ndownloader.figshare.com/files/5976015",
]
ARCHIVE = DATA_DIR / "lfw.tgz"


def main():
    extracted = DATA_DIR / "lfw"
    if extracted.exists():
        print(f"LFW already extracted: {extracted}")
        return
    print("Downloading Labeled Faces in the Wild from official/public benchmark mirrors.")
    last_error = None
    for url in LFW_URLS:
        try:
            print(f"Trying {url}")
            with requests.get(url, stream=True, timeout=120) as response:
                response.raise_for_status()
                with ARCHIVE.open("wb") as f:
                    for chunk in response.iter_content(chunk_size=1024 * 1024):
                        if chunk:
                            f.write(chunk)
            last_error = None
            break
        except requests.RequestException as exc:
            last_error = exc
            print(f"Download failed: {exc}")
    if last_error:
        raise SystemExit(f"Could not download LFW from configured sources: {last_error}")
    print("Extracting LFW...")
    with tarfile.open(ARCHIVE, "r:gz") as tar:
        tar.extractall(DATA_DIR)
    print("Done. These photos are used only as SYNTHETIC DEMO DATA wrappers, not real case records.")


if __name__ == "__main__":
    main()
