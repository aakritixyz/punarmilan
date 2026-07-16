# Punarmilan — Reuniting India's Missing Children

Punarmilan is an ethical missing/found-child case-management demo that helps verified reviewers compare a found child's photo against stored missing-child reports using real face similarity search.

The system does **not** identify a child automatically. It surfaces **ranked candidate records** for trained human review.

## One-Line Pitch

Punarmilan turns a manual, memory-based photo review process into a real ranked face-similarity workflow, while keeping every final decision with trained, accountable human reviewers.

## Live Demo Flow

Use this flow when presenting the project:

1. Open the dashboard and point out the synthetic-data warning.
2. Show the vector index status: FAISS backend, stored embeddings, and last sync.
3. Open **Case List** to show stored missing-child demo records.
4. Open **Report Found**.
5. Upload a consented/demo face photo.
6. Submit the found-child report.
7. The app stores the case, runs the backend matching pipeline, and opens ranked candidates automatically.
8. Review confidence bars and labels: `review recommended`, `needs more info`, `low priority`.
9. Confirm, reject, or escalate a candidate.
10. Open **Audit Trail** to show accountability.

## What Makes It Different

- It replaces manual scrolling through photos with ranked vector search.
- It uses a real image pipeline: OpenCV -> OpenFace embeddings -> FAISS search.
- It never says "match found" or "identified."
- It restricts ranked results to reviewer/admin screens.
- It logs reviewer actions for accountability.
- It uses public benchmark/demo data, not real missing-child photos.

## Architecture

```text
React + Vite frontend
        |
        | HTTPS API calls
        v
FastAPI backend
        |
        | image validation and face preprocessing
        v
OpenCV
        |
        | face embedding
        v
OpenFace
        |
        | nearest-neighbor vector search
        v
FAISS
        |
        | case records, embeddings, audit events
        v
SQLite demo database
```

Deployment:

```text
Frontend: Vercel
Backend: Render
Code: GitHub
```

## Technology

### React + Vite

The frontend provides the reviewer dashboard, case queue, intake forms, ranked candidate view, and audit trail.

The deployed frontend reads the backend URL from:

```text
VITE_API_URL
```

### FastAPI

The backend exposes the API routes used by the reviewer UI:

```text
/health
/cases
/search
/audit
/vector-index
/vector-index/rebuild
/review-actions
```

### OpenCV

OpenCV handles image processing before matching:

- reads uploaded images
- checks blur using Laplacian variance
- checks brightness and overexposure
- detects faces
- rejects no-face images
- flags multiple-face images
- crops and resizes the selected face

### OpenFace

OpenFace converts each cropped face into a 128-dimensional embedding vector.

The system compares embeddings, not raw image pixels.

### FAISS

FAISS performs fast nearest-neighbor search over stored face embeddings.

This demo uses:

```text
faiss.IndexFlatIP
```

Stored vectors are normalized, so inner-product search behaves like cosine-similarity ranking.

### SQLite

SQLite stores demo case records, embeddings, image paths, and audit logs.

For production, this should move to PostgreSQL.

## Matching Pipeline

```text
Uploaded found-child photo
        |
        v
OpenCV quality checks
        |
        v
Face detection and crop
        |
        v
OpenFace embedding generation
        |
        v
FAISS vector search
        |
        v
Metadata adjustment
        |
        v
Ranked candidates for reviewer triage
```

The UI shows:

- exact percentage score
- confidence label
- confidence bar
- metadata adjustment
- simple region-level explainability

## Real-Time Demo Behavior

The current demo includes a more realistic intake-to-search flow:

```text
Report Found form submitted
        |
        v
Case is stored
        |
        v
Embedding is generated
        |
        v
FAISS search runs immediately
        |
        v
Ranked candidates are displayed
        |
        v
Audit trail updates
```

The dashboard also refreshes periodically and shows a live sync timestamp.

## Ethics And Safety

Punarmilan is designed as decision support, not automated identification.

The language intentionally avoids:

- "match found"
- "identified"
- "confirmed by AI"

The correct language is:

- candidate
- ranked candidate
- similarity score
- recommended for review
- needs more info
- low priority

This matters because false positives can harm children, families, and investigations.

## Demo Data Policy

This project must never use real missing-child photos.

The demo uses Labeled Faces in the Wild (LFW), a public benchmark face dataset, wrapped in fictional case metadata.

The matching math is real, but the case records are synthetic demo records.

Every image shown in the UI is watermarked:

```text
SYNTHETIC DEMO DATA - LFW PUBLIC DATASET
```

## Local Setup

### Frontend

```bash
npm install
npm run dev
```

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/download_models.py
python scripts/download_lfw.py
python scripts/seed_lfw_demo.py
RELOAD=false python run_api.py
```

Backend runs on:

```text
http://127.0.0.1:8000
```

Frontend usually runs on:

```text
http://127.0.0.1:5173
```

## Deployment

### Backend On Render

Root directory:

```text
backend
```

Build command:

```bash
pip install -r requirements.txt && python scripts/download_models.py && python scripts/download_lfw.py && python scripts/seed_lfw_demo.py
```

Start command:

```bash
RELOAD=false python run_api.py
```

Python is pinned with:

```text
backend/.python-version
```

### Frontend On Vercel

Framework:

```text
Vite
```

Build command:

```bash
npm run build
```

Output directory:

```text
dist
```

Environment variable:

```text
VITE_API_URL=https://your-render-backend-url.onrender.com
```

Apply it to Production and Preview environments.

## Testing

Run backend tests:

```bash
cd backend
pytest tests
```

The test suite covers:

- blur detection behavior
- no-face rejection
- FAISS nearest-neighbor ordering
- vector index persistence
- LFW-based same-identity retrieval
- zero-results coverage metadata

## Current Limitations

- OpenFace is used for demo stability; a production version should use InsightFace/ArcFace.
- SQLite is used for demo storage; production should use PostgreSQL.
- Uploaded files are stored locally; production should use S3, Cloudflare R2, or Supabase Storage.
- Render free tier can sleep, so the backend may take time to wake up.
- LFW is public benchmark data, not actual case data.
- Face recognition can show bias across age, skin tone, lighting, occlusion, and image quality.
- All results require human review.

## Production Upgrade Path

The most important next upgrades:

1. Replace OpenFace with InsightFace/ArcFace.
2. Add JWT authentication and real roles: public, NGO reviewer, CWC reviewer, police reviewer, admin.
3. Move SQLite to PostgreSQL.
4. Store images in object storage.
5. Run image processing in background jobs.
6. Add WebSocket or polling-based processing status.
7. Add reviewer notes and escalation workflow.
8. Add case retention/deletion policy.

## Final Note

Punarmilan is not a public face-search tool. It is an accountability-first reviewer workflow for surfacing possible leads from already-submitted case records.
