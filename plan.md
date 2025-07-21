# Smart Assistant for Video/Audio Content: Development Plan

## Notes
- Project scope (MVP): file upload → ASR (Whisper) → chapters → search/RAG → LLM answer → cache.
- Micro-pipeline architecture: each step is a separate Docker worker.
- Key tech stack: OpenAI Whisper (ASR), text-embedding-3-small, GPT-4o (LLM), FAISS (vector DB), FastAPI (backend), Next.js (frontend), docker-compose/Helm (DevOps), OpenTelemetry/Prometheus/Grafana (observability).
- Redis Streams as shared message bus; artefacts stored at minimum on S3.
- Semantic versioning + DVC for embedding indexes.
- Security: Pydantic validators for PII, explicit user consent for external APIs.

## Task List
- [x] Sprint 1: Bootstrap & CI
  - [x] Set up repository, poetry/lock, pre-commit hooks
  - [x] Create docker-compose.yml with hello-FastAPI
  - [x] Configure GitHub Actions for test/lint
  - [x] Ensure `make test` is green, CI runs < 5 min
- [ ] Sprint 2: ASR-MVP
  - [x] Implement worker for file upload and Redis RQ queue
  - [ ] Integrate Whisper CLI → JSON/VTT
  - [ ] REST endpoint /transcribe
- [ ] Sprint 3: Segment + Embedding-3
  - [ ] Sentence splitter, 8192 token batcher
  - [ ] Async OpenAI Embed-3 wrapper + LRU-cache
  - [ ] Ruptures (Pelt) → chapters.json
- [ ] Sprint 4: RAG PoC
  - [ ] FAISS index (IP 1536-d)
  - [ ] LangChain RetrievalQA (prompt-template v0)
  - [ ] REST /ask?q=
- [ ] Sprint 5: UI v1
  - [ ] Next.js app, video-player, chapters-sidebar
  - [ ] Chat-pane (WS stream)
  - [ ] Drag-n-drop upload
- [ ] Sprint 6: Cache & Latency
  - [ ] Redis hash <prompt_hash, LLM-resp>
  - [ ] CDN for static resources
  - [ ] Rate-limit middleware
- [ ] Sprint 7: TL;DR + Translation
  - [ ] GPT-4o: summary / explain like I’m 5
  - [ ] Batch-translate (RU/EN)
  - [ ] UI toggle for summary
- [ ] Sprint 8: TTS (Voice→Voice)
  - [ ] Coqui XTTS GPU-server
  - [ ] Endpoint /tts?text= → .wav
  - [ ] UI 'Listen to answer' button
- [ ] Sprint 9: Prod-Infra & Observability
  - [ ] Helm-chart, Ingress, Cert-manager
  - [ ] Grafana dashboard: latency, $/request, GPU-util
  - [ ] Alertmanager integration
- [ ] Sprint 10: Polish & Alpha-launch
  - [ ] Smoke tests, stress-test (Locust)
  - [ ] Privacy policy, cost monitoring
  - [ ] Public link for 20 alpha-users

## Current Goal
Start Sprint 2: ASR-MVP (file upload worker)