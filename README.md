# Punarmilan — Reuniting India's Missing Children

Punarmilan is a portfolio-ready demo of an ethical missing/found-child case-management system. It shows how a found-child photo could be ranked against open missing-child reports, while keeping every decision in the hands of trained, accountable reviewers.

## What this demo includes

- Reviewer dashboard with synthetic case counts, case-density view, case queue, ranked candidates, confidence bars, and explainability indicators.
- Public-style intake flows for missing-child and found/unidentified-child reports.
- Append-only audit log for searches, views, and reviewer actions.
- FastAPI backend for real reviewer-only candidate search.
- OpenCV face detection, face crop preprocessing, blur/brightness/no-face/multiple-face validation.
- Pretrained OpenFace embedding generation using `nn4.small2.v1.t7`.
- FAISS vector search over stored normalized face embeddings.
- Browser upload flow that calls the real backend instead of computing fake scores in React.
- Persistent warnings that all records are synthetic/demo data.

## Important safety boundary

Do not use real missing children's photos in this demo.

For a YouTube or college review demo, use:

- Your own consented photos.
- A friend/family member's photos only with explicit permission.
- Synthetic AI faces or public consented datasets.

The current backend computes real face embeddings and searches a FAISS index. It is still a demo because the records are synthetic wrappers around public benchmark/consented photos, not real case records.

## How the face-matching backend works

1. Upload image to FastAPI.
2. OpenCV checks blur and brightness.
3. OpenCV Haar cascade detects face boxes.
4. If no face is detected, the API returns a clear 422 error.
5. If multiple faces are detected, the API asks for `selected_face` instead of guessing.
6. The selected face is cropped and resized.
7. OpenFace generates a fixed-length embedding vector.
8. The embedding is stored once with the case record.
9. Searches build a FAISS `IndexFlatIP` over normalized stored embeddings.
10. Results are metadata-adjusted, ranked, bucketed into confidence tiers, and logged.

Production upgrade path: replace OpenFace with InsightFace/ArcFace, move SQLite to PostgreSQL, and persist FAISS indexes or use a managed vector store. The API boundaries stay the same.

## How to run

Frontend:

```bash
cd ~/Desktop/punarmilan
npm install
npm run dev
```

Backend:

```bash
cd ~/Desktop/punarmilan
/Users/Dell/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m venv backend/.venv312
backend/.venv312/bin/pip install -r backend/requirements.txt
backend/.venv312/bin/python backend/scripts/download_models.py
backend/.venv312/bin/python backend/scripts/download_lfw.py
backend/.venv312/bin/python backend/scripts/seed_lfw_demo.py
backend/.venv312/bin/python backend/run_api.py
```

Then open the local URL printed by Vite, usually:

```text
http://127.0.0.1:5173
```

The backend runs at:

```text
http://127.0.0.1:8000
```

## Suggested 60-second video narrative

1. Start on the dashboard and point out the synthetic-data banner.
2. Open Case Queue and select Arjun Sharma.
3. Show ranked candidates and say: “This never says match found. It only says review recommended.”
4. Use Confirm / Need info / Reject and show the audit log entry.
5. Scroll to Live similarity demo.
6. Upload one old/reference photo of yourself and two or three candidate photos.
7. Run ranked search and show that the most visually similar photo rises to the top.
8. Close by explaining that production would swap the browser demo engine for InsightFace + FAISS, with restricted reviewer access.

## What would make this stronger next

- Replace the demo bearer token with real JWT/OAuth2 roles.
- Add PostgreSQL migrations and move off local SQLite.
- Swap OpenFace to InsightFace/ArcFace for stronger production-grade embeddings.
- Add pytest tests for degraded images: blur, side profile, masks, low light, and time gaps.
- Add public case-status lookup by case ID without exposing candidate data.

## Ethical limitation statement

Face-recognition systems can be less accurate across age, skin tone, lighting, image quality, camera angle, and occlusion. False positives can harm families and children. Punarmilan is therefore designed as reviewer decision-support, not automated identification.
