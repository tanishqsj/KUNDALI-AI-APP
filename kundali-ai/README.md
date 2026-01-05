# 🪐 Kundali-AI

**An explainable, AI-assisted Vedic astrology platform**

---

## 📌 Overview

**Kundali-AI** is a  backend system that generates Vedic kundali charts, derives astrological insights, evaluates rule-based interpretations, and uses AI **only as a language layer** — never as a source of facts.

The system is designed to be:

* ✅ **Explainable** (rules + derived data first, AI last)
* ✅ **Safe** (guardrails, no medical/legal claims)
* ✅ **Scalable** (Redis caching, async APIs)
* ✅ **Extensible** (new charts, rules, AI providers)
* ✅ **Investor-ready** (clean architecture, no hacks)

---

## 🧠 Core Philosophy

> **Astrology logic ≠ AI logic**

* Astrology calculations, rules, and transits are **deterministic**
* AI is used **only to explain** already-computed results
* AI never invents placements, dates, or predictions
* Every answer can be traced back to data or rules

This makes the system:

* auditable
* debuggable
* safer than AI-only astrology apps

---

## 🏗️ High-Level Architecture

```
API Layer (FastAPI)
        ↓
Service Layer (business orchestration)
        ↓
Domain Layer (kundali, rules, transits)
        ↓
Persistence Layer (Postgres via SQLAlchemy)
        ↓
Cache Layer (Redis)
        ↓
AI Layer (LLM + guardrails + prompts)
```

---

## 📁 Project Structure

```
kundali-ai/
├── app/
│   ├── main.py                # App entry point
│   ├── config.py              # Environment & settings
│   ├── dependencies.py        # Core dependencies
│
│   ├── api/
│   │   └── v1/
│   │       ├── routes/        # Public APIs (kundali, report, location)
│   │       └── admin/         # Admin-only APIs
│
│   ├── services/              # Business orchestration (PDF, Location, Report)
│   ├── domain/                # Astrology logic
│   ├── ai/                    # LLM + prompts + guardrails
│   ├── cache/                 # Redis caching layer
│   ├── persistence/           # DB models & repositories
│
│   ├── ui/
│   │   └── templates/         # HTML templates (create, report, etc.)
│
├── migrations/                # Alembic migrations
├── alembic.ini
├── requirements.txt
├── .env
└── README.md
```

---

## 🔑 Key Features

### 🌌 Kundali Generation

* Birth chart calculation
* **North Indian Style Chart Visualization**
* Derived charts (houses, nakshatras, doshas)
* Divisional charts (D9, D10)
* Stored and versioned in DB

### 🌍 Smart Location Search

* Integration with **Open-Meteo Geocoding API**
* Free, accurate global city search
* Auto-detection of latitude, longitude, and timezone

### 📜 Rule Engine

* Deterministic rule matching
* Admin-managed rule definitions
* Rule-to-kundali mappings
* Explainable outputs

### 🤖 AI-Assisted Answers

* Grounded prompts (facts + rules only)
* Domain-specific prompts (career, health, etc.)
* Guardrails against:

  * medical claims
  * legal advice
  * fatalistic language
* Structured, UI-ready responses

### ⚡ Caching (Redis)

* Kundali snapshots
* Ask/AI responses
* PDF reports
* Transits & gochar
* TTL-controlled, read-through caching

### 📄 PDF Reports

* **Instant HTML Preview**: View full report in browser immediately
* Cached, downloadable kundali reports
* Optional transit inclusion
* No double billing on cache hits

### 🎙️ Voice-Based Astrology

* Voice input → text → grounded AI → voice output
* Uses same rule & AI pipeline

### 🛠️ Admin Mode

* Rule creation & management
* Rule preview on kundali
* Fully protected admin APIs

---

## 🧪 Safety & Ethics

Built-in protections:

* No disease diagnosis
* No death predictions
* No legal advice
* No guaranteed outcomes
* Clear disclaimers
* Tone softening

This makes Kundali-AI suitable for:

* consumer apps
* enterprise integrations
* regulated markets

---

## 🚀 Running Locally

### 1️⃣ Prerequisites

* Python **3.10+**
* PostgreSQL
* Redis
* OpenAI API key

---

### 2️⃣ Clone & Install

```bash
git clone <repo-url>
cd kundali-ai

python -m venv venv
source venv/bin/activate

pip install -r requirements.txt
```

---

### 3️⃣ Create `.env`

```env
# App
ENV=local
DEBUG=true

# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/kundali_ai

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# OpenAI
OPENAI_API_KEY=sk-xxxx
OPENAI_MODEL=gpt-4o-mini
```

---

### 4️⃣ Run Migrations

```bash
alembic revision --autogenerate -m "initial schema"
alembic upgrade head
```

---

### 5️⃣ Start the App

```bash
uvicorn app.main:app --reload
```

---

### 6️⃣ Access

* 📘 **Swagger API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
* 🖥️ **Frontend UI**: [http://localhost:8000/ui/](http://localhost:8000/ui/)
* ❤️ **Health Check**: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)

---

## 🔐 Authentication (Current State)

* Dev mode uses a **stubbed user**
* Admin access enforced via `require_admin`
* Designed to plug in:

  * JWT
  * OAuth
  * Session auth

---

## 🧭 Future Roadmap

* Swiss Ephemeris integration
* More divisional charts
* ML-assisted rule discovery
* Multi-language support
* Docker & cloud deployment
* Mobile-ready APIs

---

## 📈 Why This Architecture Scales

* Clear separation of concerns
* Stateless services
* Async everywhere
* Cache-first design
* Replaceable AI provider
* Testable at every layer

---
