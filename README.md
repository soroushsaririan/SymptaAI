# SymptaAI — Clinical AI Co-Pilot

A production-grade healthcare SaaS platform built with LangGraph multi-agent orchestration, FastAPI, and Next.js. SymptaAI assists clinicians with patient intake, symptom analysis, lab interpretation, drug interaction checking, differential diagnosis generation, care planning, and physician-ready PDF report generation.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                            Next.js Frontend                             │
│    Dashboard · Patients · AI Analysis (SSE) · Clinical Reports         │
└───────────────────────────────────┬─────────────────────────────────────┘
                                    │ HTTPS / SSE
┌───────────────────────────────────▼─────────────────────────────────────┐
│                          FastAPI Backend                                │
│  JWT Auth · Rate Limiting · HIPAA Audit Logs · Structured Logging      │
│                                                                         │
│  ┌──────────────┐  ┌───────────────┐  ┌──────────────────────────────┐ │
│  │  REST API    │  │  SSE Stream   │  │   Celery Worker              │ │
│  │  /patients   │  │  /analysis/   │  │   (async task queue)         │ │
│  │  /labs       │  │  {id}/stream  │  │                              │ │
│  │  /reports    │  └───────────────┘  └──────────────────────────────┘ │
│  └──────────────┘                                                       │
│                                                                         │
│  ┌──────────────────── LangGraph Workflow ────────────────────────────┐ │
│  │                                                                    │ │
│  │  PatientIntake → [SymptomAnalysis ‖ RecordSummarizer] → Merge     │ │
│  │       → LabInterpretation → DrugInteraction                       │ │
│  │       → DifferentialDiagnosis → CarePlan → ClinicalReport         │ │
│  │                                                                    │ │
│  │  Each agent: BaseHealthcareAgent + tenacity retry + safe_run()    │ │
│  │  RAG-enhanced with ChromaDB medical knowledge base                │ │
│  └────────────────────────────────────────────────────────────────────┘ │
└───────┬────────────────────────────┬────────────────────────────────────┘
        │                            │
┌───────▼──────┐            ┌────────▼───────┐      ┌──────────────────┐
│  PostgreSQL  │            │     Redis      │      │    ChromaDB      │
│  (primary)   │            │  (cache+queue) │      │  (vector RAG)    │
└──────────────┘            └────────────────┘      └──────────────────┘
```

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 14 App Router, TypeScript, Tailwind CSS, shadcn/ui, Framer Motion, React Query |
| Backend | FastAPI, Python 3.11, Pydantic v2, SQLAlchemy 2.0 async |
| AI/Agents | LangGraph, LangChain, OpenAI GPT-4o, `with_structured_output()` |
| Vector DB | ChromaDB with OpenAI `text-embedding-3-small` |
| Task Queue | Celery + Redis (analysis, records, reports queues) |
| Database | PostgreSQL 16 (asyncpg driver), Alembic migrations |
| Auth | JWT (python-jose), bcrypt (passlib), OAuth2 bearer |
| Logging | structlog (JSON in prod, console in dev) |
| PDF Export | ReportLab |
| Monitoring | Prometheus metrics, Sentry error tracking, Celery Flower |

## LangGraph Agent Pipeline

```
patient_intake
     │
     ├─── symptom_analysis  (parallel)
     └─── record_summarizer (parallel)
              │
           [merge]
              │
         lab_interpretation
              │
         drug_interaction
              │
       differential_diagnosis
              │
           care_plan
              │
        clinical_report
              │
             END
```

Each agent:
- Extends `BaseHealthcareAgent` with `abstract async def run(state)`
- Uses `safe_run()` wrapper — failures add to `state["errors"]` and continue
- Uses `_invoke_with_retry()` with tenacity (3 retries, exponential backoff)
- Uses `with_structured_output()` for type-safe Pydantic model responses
- Has access to ChromaDB RAG for medical knowledge retrieval

## Quick Start

### Prerequisites
- Docker & Docker Compose
- OpenAI API key

### 1. Clone and configure

```bash
git clone <repo-url>
cd SymptaAI
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

### 2. Start all services

```bash
cd infrastructure
docker-compose up -d
```

This starts: PostgreSQL, Redis, ChromaDB, FastAPI backend, Celery workers, Next.js frontend.

### 3. Access the app

| Service | URL |
|---|---|
| Frontend | http://localhost:3000 |
| API docs | http://localhost:8000/docs |
| API ReDoc | http://localhost:8000/redoc |
| Celery Flower | http://localhost:5555 |

### 4. Create your first account

Navigate to http://localhost:3000/register and create a physician account.

---

## Local Development

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Start dependencies
docker-compose -f ../infrastructure/docker-compose.yml up -d postgres redis chromadb

# Run migrations
alembic upgrade head

# Start dev server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Run Tests

```bash
cd backend
pytest                          # All tests
pytest tests/unit/              # Unit tests only (no services needed)
pytest tests/integration/ -m integration  # Integration tests
pytest --cov=app --cov-report=html  # With coverage
```

---

## API Reference

### Authentication

```
POST /api/v1/auth/register   — Register new user
POST /api/v1/auth/token      — Login (OAuth2 form)
GET  /api/v1/auth/me         — Current user
```

### Patients

```
GET    /api/v1/patients              — List patients (paginated, searchable)
POST   /api/v1/patients              — Create patient
GET    /api/v1/patients/{id}         — Get patient detail
PUT    /api/v1/patients/{id}         — Update patient
POST   /api/v1/patients/{id}/intake  — Submit clinical intake
GET    /api/v1/patients/{id}/summary — AI-generated summary
```

### AI Analysis

```
POST /api/v1/analysis/run            — Start full analysis workflow
GET  /api/v1/analysis/{id}/status    — Get run status
GET  /api/v1/analysis/{id}/stream    — SSE stream (real-time agent events)
GET  /api/v1/analysis/history/{pid}  — Patient analysis history
```

### Reports

```
GET  /api/v1/reports                 — List reports
GET  /api/v1/reports/{id}            — Get report with full content
GET  /api/v1/reports/{id}/export     — Export as PDF (ReportLab)
POST /api/v1/reports/{id}/review     — Physician review notes
```

---

## Security & HIPAA Considerations

- **JWT authentication** with 24-hour expiry, RS256-compatible
- **Role-based access control**: physician, nurse, admin, viewer
- **Audit logs** on every PHI access (patient, labs, records, reports)
- **Soft deletes** — patient records are never hard deleted
- **Rate limiting** via Redis sliding window (60 req/min per user, configurable)
- **Structured logging** with `request_id` injection for traceability
- **CORS** configured for specific origins
- Passwords hashed with bcrypt (12 rounds)
- All DB queries use parameterized statements (SQLAlchemy ORM)

> **Note**: This platform is a clinical decision support tool. All AI-generated outputs must be reviewed by a licensed physician. Not a substitute for clinical judgment.

---

## Project Structure

```
SymptaAI/
├── backend/
│   ├── app/
│   │   ├── agents/          # 8 LangGraph agents
│   │   ├── api/v1/          # FastAPI route handlers
│   │   ├── core/            # Config, security, exceptions, logging
│   │   ├── db/              # SQLAlchemy engine & session
│   │   ├── middleware/       # Rate limiting, auth middleware
│   │   ├── models/          # SQLAlchemy ORM models
│   │   ├── schemas/         # Pydantic v2 request/response schemas
│   │   ├── services/        # Business logic (patient, analysis, report, RAG)
│   │   ├── tools/           # LangChain tools (lab reference, medical search)
│   │   ├── workers/         # Celery task definitions
│   │   └── workflows/       # LangGraph state & healthcare workflow
│   ├── alembic/             # Database migrations
│   ├── Dockerfile
│   ├── main.py
│   ├── pytest.ini
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── (auth)/      # Login, register pages
│   │   │   └── (dashboard)/ # All protected pages
│   │   ├── components/
│   │   │   ├── layout/      # Sidebar, Header
│   │   │   └── ui/          # shadcn-style UI primitives
│   │   ├── hooks/           # useDebounce
│   │   ├── lib/             # API client, auth utils
│   │   └── types/           # TypeScript interfaces
│   ├── Dockerfile
│   └── next.config.js
├── infrastructure/
│   └── docker-compose.yml
├── tests/
│   ├── unit/                # Pure unit tests
│   ├── integration/         # API integration tests
│   └── agents/              # Agent/workflow tests
├── .env.example
└── README.md
```
