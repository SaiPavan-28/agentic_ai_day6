# 🚀 Autonomous Incident Triage Agent

An autonomous SRE incident triage agent built with **LangGraph**, **Google Gemini**, **Supabase pgvector (RAG)**, **FastAPI**, and **Gradio**, featuring **Human-in-the-Loop (HITL)** execution control and state persistence.

Designed and verified strictly according to **OpenSpec** specifications.

---

## 📐 Architecture Overview

```
+-----------------------------------------------------------------------------------+
|                                  USER INTERFACE                                   |
|               Gradio Interactive Web UI  /  FastAPI REST Endpoints                |
+----------------------------------------+------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|                                SHARED SERVICE LAYER                               |
|                         service_chat()  |  service_approve()                      |
+----------------------------------------+------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|                                 LANGGRAPH ENGINE                                  |
|                                                                                   |
|    +---------------+      +-------------------+      +-----------------------+    |
|    |  agent_node   | ---> |   route_tools()   | ---> |   execute_safe_tools  |    |
|    | (Gemini 3.5)  |      +---------+---------+      | (Health & Vector RAG) |    |
|    +---------------+                |                +-----------------------+    |
|                                     |                                             |
|                                     v (Sensitive tool: escalate_ticket)           |
|                          +------------------------+                               |
|                          |   HITL INTERRUPT       |                               |
|                          |  (sensitive_tools)     |                               |
|                          +-----------+------------+                               |
|                                      |                                            |
|                                      v                                            |
|                          AWAITING_APPROVAL State                                  |
|                       (Approve / Reject Action)                                   |
+----------------------------------------+------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|                                 PERSISTENCE LAYER                                 |
|               Supabase PostgresSaver (State) + pgvector (768-dim RAG)             |
+-----------------------------------------------------------------------------------+
```

---

## ✨ Features

- **🤖 Autonomous Triage**: Investigates incidents automatically by checking service health (`query_service_health`) and searching internal runbooks (`search_remediation_runbooks`).
- **🛡️ Human-in-the-Loop (HITL) Security**: Critical actions (`escalate_ticket`) automatically trigger an execution pause before running (`AWAITING_APPROVAL`), requiring human engineer approval.
- **💾 Persistent Workflow State**: Uses LangGraph's `PostgresSaver` connected to Supabase transaction pooler (`prepare_threshold=None`). State survives cold starts and server restarts.
- **🔍 Vector RAG System**: Uses Google Gemini Embeddings (`models/gemini-embedding-001` with `output_dimensionality=768`) and Supabase `pgvector` with cosine similarity (`1 - (embedding <=> query_embedding)`).
- **🖥️ Dual UI & API**: Web UI built with Gradio and REST API built with FastAPI (`/chat`, `/approve`, `/healthz`).
- **📐 OpenSpec Validated**: All specs validated using `openspec validate --all`.

---

## 🛠️ Prerequisites

- **Python**: `3.11+`
- **Google AI Studio Key**: `GEMINI_API_KEY` ([Get Key](https://aistudio.google.com/))
- **Supabase Postgres Database**: `DATABASE_URL` transaction pooler connection string (Port `6543`) with `pgvector` extension.

---

## 🚀 Quickstart & Local Setup

### 1. Clone & Navigate to Project
```bash
git clone https://github.com/SaiPavan-28/agentic_ai_day6.git
cd agentic_ai_day6/incident-agent
```

### 2. Set Up Virtual Environment & Install Dependencies
* **Windows (PowerShell):**
  ```powershell
  python -m venv .venv
  .\.venv\Scripts\Activate.ps1
  pip install -r requirements.txt
  ```
* **Linux / macOS:**
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  pip install -r requirements.txt
  ```

### 3. Configure Environment Variables (`.env`)
Create a `.env` file in `incident-agent/`:
```env
GEMINI_API_KEY=your_gemini_api_key_here
DATABASE_URL=postgresql://postgres:[PASSWORD]@[HOST]:6543/postgres?sslmode=require
```

### 4. Initialize Database & Seed RAG Knowledge Base
Apply migration schema (`db/migrations/001_incident_docs.sql`) and seed standard runbooks:
```bash
python seed_rag.py
```

### 5. Run Tests
Verify the complete test suite (22 unit & integration tests):
```bash
pytest -q
```

### 6. Start Application Server
```bash
uvicorn app:app --reload --port 8000
```

---

## 🌐 API & UI Usage

### Web UI
Open your browser and navigate to:
👉 **`http://localhost:8000/`**

### REST API Endpoints

#### 1. Health Check (`GET /healthz`)
```bash
curl http://localhost:8000/healthz
```
**Response:** `{"status": "ok"}`

#### 2. Submit Incident (`POST /chat`)
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"thread_id": "thread-1", "message": "Auth service is timing out"}'
```
**Response (Awaiting Approval):**
```json
{
  "status": "AWAITING_APPROVAL",
  "pending_action": {
    "calls": [
      {
        "name": "escalate_ticket",
        "args": {
          "ticket_title": "Auth Service Timing Out",
          "severity": "HIGH"
        },
        "id": "call_123"
      }
    ]
  },
  "response": ""
}
```

#### 3. Approve or Reject Action (`POST /approve`)

* **Approve:**
  ```bash
  curl -X POST http://localhost:8000/approve \
    -H "Content-Type: application/json" \
    -d '{"thread_id": "thread-1", "approved": true}'
  ```
  **Response:** `{"status": "RESOLVED", "response": "Ticket created: Auth Service Timing Out..."}`

* **Reject:**
  ```bash
  curl -X POST http://localhost:8000/approve \
    -H "Content-Type: application/json" \
    -d '{"thread_id": "thread-1", "approved": false, "rejection_reason": "False alarm"}'
  ```
  **Response:** `{"status": "REJECTED_AND_RESUMED", "response": "Understood. Escalation cancelled..."}`

---

## ☁️ Deployment to Render

This repository includes a [`render.yaml`](file:///c:/Users/sadvi/Downloads/autonomousaiagent/incident-agent/render.yaml) blueprint for one-click deployment on Render's free tier.

### Blueprint Deployment Steps:
1. Push code to your GitHub repository.
2. In [Render Dashboard](https://dashboard.render.com/), select **New → Blueprint**.
3. Connect your repository. Render will automatically read [`render.yaml`](file:///c:/Users/sadvi/Downloads/autonomousaiagent/incident-agent/render.yaml).
4. Configure required Environment Variables in Dashboard:
   - `GEMINI_API_KEY`: Google AI Studio Key.
   - `DATABASE_URL`: Supabase Transaction Pooler URL (`port 6543`).
5. Click **Apply**.

### Free-Tier Operational Notes:
- **Automatic Spin-down**: Render spins down free web services after 15 minutes of inactivity.
- **Cold Start**: Initial request after spin-down may take 30–60 seconds.
- **State Resilience**: Paused approval states (`AWAITING_APPROVAL`) survive cold starts and server restarts because state is checkpointed in Supabase via `PostgresSaver`.

---

## 📐 OpenSpec Specification Validation

To validate specification compliance:
```bash
openspec validate --all
```

**Validated Specs:**
- `spec/deployment`
- `spec/hitl-approval`
- `spec/knowledge-base`
- `spec/triage-agent`
- `spec/triage-api`
- `spec/triage-ui`
