# Smart Assistant for Video/Audio Content

A web service that helps users extract insights, summaries, and answers from video and audio content.

## Features (Planned)

- Automatic Speech Recognition (ASR) using OpenAI Whisper
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
   make install
   ```
3. Run development environment:
   ```bash
   make dev
   ```

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
