# Smart Assistant for Video/Audio Content

A web service that helps users extract insights, summaries, and answers from video and audio content.

## Features

- Automatic Speech Recognition (ASR) using Vosk (replacing Whisper)
- Content segmentation into chapters for easy navigation
- Semantic search and RAG (Retrieval Augmented Generation)
- LLM-powered Q&A about content
- Summaries and "explain like I'm 5" feature
- Language translation (RU/EN)
- Text-to-Speech for listening to answers

## Architecture

This project uses a "micro-pipeline" architecture where each processing step runs as a separate Docker worker:

- FastAPI backend with WebSockets support
- Next.js frontend
- Redis for message queue and caching
- FAISS for vector storage
- OpenAI services for embeddings and LLM
- OpenTelemetry, Prometheus, and Grafana for observability

## Development Setup

1. Clone this repository
2. Install dependencies:
   ```bash
   poetry install
   ```
3. Run the complete transcription pipeline with a single command:
   ```bash
   poetry run run-all
   ```

   Or run components separately:
   ```bash
   # Start Redis server if not already running
   redis-server
   
   # Start API server
   poetry run api
   
   # Start worker
   poetry run worker
   ```

4. Access the API:
   - Swagger UI: http://localhost:8001/docs
   - Upload endpoint: http://localhost:8001/api/v1/transcribe

## Project Structure

```
repo-root/
├─ backend/
│  ├─ app/                 # FastAPI routers
│  ├─ workers/             # Processing workers
│  ├─ core/                # utils, prompts, config
│  └─ tests/
├─ frontend/               # Next.js 14 (app router)
├─ charts/                 # Helm
├─ docker-compose.yml
└─ Makefile
```

## License

[MIT](LICENSE)
