# Horizons Secure AI Infrastructure

> A locally-hosted AI system powering intelligent automation for [Horizons Electronics Repair](https://github.com/YOUR_USERNAME) — from lead generation to customer intake to real-time repair status updates.

![Status](https://img.shields.io/badge/status-in%20development-yellow)
![License](https://img.shields.io/badge/license-MIT-blue)
![LLM](https://img.shields.io/badge/LLM-Ollama-green)

---

## Overview

Horizons Secure AI is a self-hosted AI infrastructure built to automate the full customer lifecycle for an electronics repair business. Every component runs locally — no data leaves the building, no per-request API costs, full control over the stack.

### Why Local-First?

- **Data privacy**: Customer device info, contact details, and repair records stay on-premise
- **Cost control**: No per-token API fees — just hardware and electricity
- **Reliability**: No dependency on external AI providers for daily operations
- **Customization**: Models fine-tuned on repair industry language and workflows

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    HORIZONS SECURE AI                     │
│                                                           │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────────┐ │
│  │   Lead Gen   │  │   Intake    │  │  Status Service  │ │
│  │   Service    │  │   Bot       │  │                  │ │
│  └──────┬───────┘  └──────┬──────┘  └────────┬─────────┘ │
│         │                 │                   │           │
│         ▼                 ▼                   ▼           │
│  ┌─────────────────────────────────────────────────────┐ │
│  │                   API Gateway                        │ │
│  │            (FastAPI / Express.js)                     │ │
│  └──────────────────────┬──────────────────────────────┘ │
│                         │                                 │
│         ┌───────────────┼───────────────┐                │
│         ▼               ▼               ▼                │
│  ┌────────────┐  ┌────────────┐  ┌─────────────┐        │
│  │   Ollama    │  │ PostgreSQL │  │ Task Queue  │        │
│  │  (Local LLM)│  │ (Data)     │  │ (Scheduling)│        │
│  └────────────┘  └────────────┘  └─────────────┘        │
│                                                           │
│  ┌─────────────────────────────────────────────────────┐ │
│  │              OpenClaw (Management Layer)              │ │
│  │        24/7 monitoring · mobile dashboard            │ │
│  └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

---

## Services

### 🔍 Lead Generation & Follow-Up (`/lead-gen`)
Automated pipeline that identifies potential repair customers from online sources, scores leads, and manages outreach sequences.

- Source monitoring (classifieds, social media, web inquiries)
- Lead scoring with LLM-powered relevance analysis
- Automated follow-up sequences with configurable cadence
- Human-in-the-loop approval for outreach messages

### 💬 AI Customer Intake (`/intake-bot`)
Conversational AI that handles first contact with customers — collecting device info, diagnosing issues, and scheduling appointments.

- Natural language device & issue identification
- Automatic ticket creation in the repair system
- Appointment scheduling with availability checking
- Handoff to human technician when needed

### 📊 Repair Status Service (`/status-service`)
Customer-facing system that translates internal repair tracking into plain-language updates.

- Real-time status lookups via chat or web
- Proactive notifications at key milestones
- Cost estimates and timeline explanations
- Photo/diagnostic report delivery

### 🔧 API Gateway (`/api`)
Central API layer that manages all communication between services and the LLM.

- Unified prompt management and versioning
- Conversation memory and context handling
- Rate limiting and request logging
- Health monitoring for all services

### 🖥️ Infrastructure (`/infra`)
Configuration and deployment for the local hosting environment.

- Ollama model configuration
- Docker Compose for local deployment
- Database migrations
- Backup and recovery scripts

---

## Tech Stack

| Layer          | Technology                          |
|----------------|-------------------------------------|
| LLM Runtime   | Ollama (Llama 3.1 / Mistral)       |
| API Layer      | FastAPI (Python) or Express (Node)  |
| Database       | PostgreSQL                          |
| Task Queue     | Celery + Redis (or BullMQ)          |
| Management     | OpenClaw                            |
| Dev Tooling    | Claude Code                         |
| Containerization | Docker + Docker Compose           |

---

## Getting Started

### Prerequisites

- Linux or macOS host machine
- 16GB+ RAM (32GB recommended for larger models)
- [Ollama](https://ollama.ai) installed
- Docker & Docker Compose
- PostgreSQL 15+
- Python 3.11+ or Node.js 22+

### Quick Start

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/horizons-secure-ai.git
cd horizons-secure-ai

# Copy environment template
cp .env.example .env

# Pull the LLM model
ollama pull llama3.1:8b

# Start infrastructure
docker compose up -d

# Run database migrations
python scripts/migrate.py

# Start the API gateway
cd api && python main.py
```

> ⚠️ **Note**: Detailed setup instructions for each service are in their respective directories.

---

## Project Roadmap

See [ROADMAP.md](./ROADMAP.md) for the full development plan and milestones.

---

## Development Journal

One goal of this project is learning in public. The [`/docs`](./docs) directory contains architecture decision records and notes on what I learned building each component.

---

## License

This project is licensed under the MIT License — see [LICENSE](./LICENSE) for details.

---

## About

Built by [YOUR NAME] as the AI backbone for **Horizons Electronics Repair** — a real business solving real problems with locally-hosted AI.

Questions or want to collaborate? Open an issue or reach out.
