# AI Knowledge Base API

A Retrieval-Augmented Generation (RAG) API for building searchable, question-answerable knowledge bases. Users upload documents, the system automatically chunks and embeds them, and questions are answered by retrieving the most relevant chunks and passing them to an LLM as context.

![CI](https://github.com/erbolboribaev/ai-knowledge-base-api/actions/workflows/ci.yml/badge.svg)

## Features

- JWT-based authentication with secure password hashing (bcrypt)
- Document management with per-user access control
- Asynchronous document processing (chunking + embedding) via Celery
- Semantic vector search using PostgreSQL + pgvector
- RAG-based chat endpoint using Groq LLM, grounded strictly in uploaded documents, with source attribution
- 13 automated tests covering authentication, authorization, and the full RAG pipeline (LLM calls are mocked)
- Fully containerized: API, worker, PostgreSQL, and Redis run with a single `docker compose up`
- CI pipeline via GitHub Actions running the full test suite on every push

## Architecture
Client
|
v
FastAPI (JWT-protected)
|
|--> Upload document --> PostgreSQL (status: pending)
| |
| v
| Celery task queued via Redis
| |
| v
| Text split into chunks
| |
| v
| Embeddings generated (sentence-transformers)
| |
| v
| Stored in pgvector (status: completed)
|
|--> Ask question --> Question embedded
|
v
Nearest chunks retrieved via pgvector
|
v
Context + question sent to Groq LLM
|
v
Answer returned with sources
## Tech Stack

| Layer | Technology |
|---|---|
| API framework | FastAPI (async) |
| ORM | SQLAlchemy 2.0 (async) |
| Database | PostgreSQL + pgvector |
| Background tasks | Celery + Redis |
| Authentication | JWT (python-jose) + bcrypt |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) |
| LLM | Groq (llama-3.3-70b-versatile) |
| Migrations | Alembic |
| Testing | pytest, pytest-asyncio, httpx |
| Containerization | Docker, docker-compose |
| CI/CD | GitHub Actions |

## Running Locally with Docker

### Requirements
- Docker and Docker Compose
- A Groq API key (free at [console.groq.com](https://console.groq.com))

### Steps

1. Clone the repository:
```bash
git clone https://github.com/erbolboribaev/ai-knowledge-base-api.git
cd ai-knowledge-base-api
```

2. Create your environment file:
```bash
cp .env.example .env
```
Set `GROQ_API_KEY` and `SECRET_KEY` in `.env` to your own values.

3. Start the stack:
```bash
cd docker
docker compose up --build
```
This starts PostgreSQL (with pgvector), Redis, the API server, and the Celery worker, and applies database migrations automatically.

4. Open the interactive API docs:
http://localhost:8000/docs
## API Examples

### Register
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "securepass123"}'
```

### Login
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -d "username=user@example.com&password=securepass123"
```

### Upload a document
```bash
curl -X POST http://localhost:8000/api/v1/documents/ \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"filename": "company_policy.txt", "content": "..."}'
```

### Ask a question (RAG)
```bash
curl -X POST http://localhost:8000/api/v1/chat/ask \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the company policy about?"}'
```

## Running Tests

```bash
pip install -r requirements.txt
pytest tests/ -v
```

Tests require a separate test database, configurable via the `TEST_DATABASE_URL` environment variable.

## Project Structure
app/
├── api/v1/ # Route handlers (auth, documents, chat)
├── core/ # Settings, security, logging
├── db/ # Database engine and session management
├── models/ # SQLAlchemy models
├── schemas/ # Pydantic request/response schemas
├── services/ # Business logic (RAG, embeddings, auth)
└── workers/ # Celery background tasks
tests/ # pytest test suite
alembic/ # Database migrations
docker/ # Dockerfile and docker-compose.yml
## License

MIT
