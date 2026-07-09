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
