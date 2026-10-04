# Building the Autonomous Incident Triage Agent with OpenSpec in Antigravity IDE

A hands-on, step-by-step guide to trying **OpenSpec** (spec-driven development for AI coding assistants) by building the Autonomous Incident Triage Agent: a LangGraph agent with Gemini, Supabase pgvector RAG, a Postgres checkpointer, Human-in-the-Loop (HITL) approval, a FastAPI + Gradio app, and deployment to Render.

You start from nothing more than a two-paragraph idea. The Antigravity agent turns that idea into specs and code **one spec-driven change at a time**. Each change is proposed, reviewed, implemented, and archived, so by the end you have both working code and a living set of specs that describe how the agent behaves.

---

## Contents

1. [What You Will Learn](#1-what-you-will-learn)
2. [OpenSpec in Two Minutes](#2-openspec-in-two-minutes)
3. [Prerequisites](#3-prerequisites)
4. [Step 1 — Install OpenSpec](#step-1--install-openspec)
5. [Step 2 — Create the Project Repository](#step-2--create-the-project-repository)
6. [Step 3 — Initialise OpenSpec](#step-3--initialise-openspec)
7. [Step 4 — Give OpenSpec Your Project Context](#step-4--give-openspec-your-project-context)
8. [Step 5 — Explore Before You Build](#step-5--explore-before-you-build)
9. [The Change Roadmap](#the-change-roadmap)
10. [Step 6 — Change 1: Knowledge Base](#step-6--change-1-knowledge-base)
11. [Step 7 — Change 2: Core Triage Agent](#step-7--change-2-core-triage-agent)
12. [Step 8 — Change 3: Human-in-the-Loop Escalation](#step-8--change-3-human-in-the-loop-escalation)
13. [Step 9 — Change 4: REST API and Gradio UI](#step-9--change-4-rest-api-and-gradio-ui)
14. [Step 10 — Change 5: Deployment to Render](#step-10--change-5-deployment-to-render)
15. [Step 11 — Change 6: Evolve a Spec (MODIFIED Requirements)](#step-11--change-6-evolve-a-spec-modified-requirements)
16. [Step 12 — Inspect the Living Specs](#step-12--inspect-the-living-specs)
17. [Reviewing a Proposal: Checklist](#reviewing-a-proposal-checklist)
18. [Troubleshooting](#troubleshooting)
19. [Quick Reference](#quick-reference)

---

## 1. What You Will Learn

By the end of this guide you will have:

- Set up OpenSpec in a Python project and wired it into Antigravity IDE as workflows and skills.
- Written project context so every AI-generated artifact knows your stack and constraints.
- Run the full OpenSpec loop (**explore → propose → review → apply → archive**) six times.
- Seen how **delta specs** (ADDED / MODIFIED / REMOVED requirements) accumulate into a source-of-truth spec for the agent.
- Used specs to catch a real safety gap in the HITL routing before it reached production.

## 2. OpenSpec in Two Minutes

OpenSpec makes you and your AI assistant agree on **what** to build before any code is written.

There are two places you type commands, and mixing them up is the most common early mistake:

| Where | Commands | Example |
| --- | --- | --- |
| **Terminal** | `openspec ...` | `openspec init`, `openspec list`, `openspec validate` |
| **Antigravity Agent panel** (the chat box where you ask the agent to write code) | `/opsx-...` | `/opsx-explore`, `/opsx-propose`, `/opsx-apply`, `/opsx-archive` |

> **Antigravity spelling.** In Antigravity, OpenSpec commands are installed as *workflows*, so they use a hyphen: `/opsx-propose`, not `/opsx:propose` (the colon form you will see in OpenSpec's docs is the Claude Code spelling). Type `/` in the Agent panel and the `opsx-*` workflows appear in the picker. Throughout this guide, "AI chat" means the Antigravity Agent panel.

The default loop:

```text
/opsx-explore  ──►  /opsx-propose  ──►  (you review)  ──►  /opsx-apply  ──►  /opsx-archive
  (optional)        plan artifacts                        AI builds it      specs merged
```

Each change lives in its own folder:

```text
openspec/
├── specs/                    # Source of truth: how the system behaves today
│   └── <capability>/spec.md
├── changes/                  # Proposed changes, one folder each
│   └── <change-name>/
│       ├── proposal.md       # Why and what
│       ├── design.md         # How (technical approach)
│       ├── tasks.md          # Implementation checklist
│       └── specs/<capability>/spec.md   # Delta specs (ADDED/MODIFIED/REMOVED)
└── config.yaml               # Project context and rules
```

When you archive a change, its delta specs are merged into `openspec/specs/`, and the change folder moves to `openspec/changes/archive/`.

## 3. Prerequisites

| Requirement | Why |
| --- | --- |
| **Node.js 20.19.0 or higher** | OpenSpec is an npm CLI |
| **Python 3.11** | The agent's runtime (matches the Render `PYTHON_VERSION`) |
| **Git + GitHub account** | Version control and Render deployment source |
| **Antigravity IDE** | The Agent panel runs the `/opsx-*` workflows; its integrated terminal runs `openspec` and Python commands |
| **`GEMINI_API_KEY`** | [aistudio.google.com](https://aistudio.google.com/) → **Get API key** → **Create key** |
| **`DATABASE_URL`** | Create a free Supabase project → **Connect** → **Connection pooler** → **Transaction** (port `6543`) → copy the URI and insert your DB password |
| **Render account** | Free web service, only needed for Change 5 |

Get the two credentials first; OpenSpec will not create cloud accounts for you.

---

## Step 1 — Install OpenSpec

In your **terminal**:

```powershell
npm install -g @fission-ai/openspec@latest
openspec --version
```

On macOS or Linux you can alternatively use `brew install openspec`.

## Step 2 — Create the Project Repository

```powershell
mkdir incident-agent
cd incident-agent
git init
mkdir docs
```

Write the **seed idea**: a short, plain-language description of what you want. This is the only input OpenSpec gets about the agent; everything else (requirements, design, tasks) will be worked out with the agent through `/opsx-explore` and `/opsx-propose`. Create `docs/idea.md`:

```markdown
# Idea: Autonomous Incident Triage Agent

When an on-call engineer describes an incident in plain English ("the auth service is timing
out"), an AI agent should investigate on its own: check the health of the affected backend
services, search our internal runbooks for matching remediation steps, and reply with what it
found and what to do next. If the problem needs manual intervention or the service stays
degraded, the agent may escalate by opening a ticket and paging the on-call team, but it must
never do this by itself. Every escalation pauses and waits for an engineer to approve or reject
it, a rejected escalation must not happen, and a paused investigation must survive restarts so
someone can approve it hours later.

Engineers should use it through a simple web UI and a REST API. Everything must run on free
tiers with no credit card: Gemini via Google AI Studio for reasoning and embeddings, Supabase
Postgres with pgvector for runbooks and agent state, LangGraph for the agent, FastAPI with a
Gradio UI for the app, and Render for hosting. Start with a few sample runbooks covering the
auth, database and payments services.
```

Keep it this short. Resist adding design decisions here; the point of the exercise is to watch OpenSpec turn intent into specs.

Create `.gitignore` **now**, before any secrets exist:

```text
.env
__pycache__/
*.pyc
.venv/
```

Create `.env` locally (never committed):

```env
GEMINI_API_KEY="your_gemini_api_key_here"
DATABASE_URL="postgresql://postgres.[PROJECT-REF]:[YOUR-PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres?sslmode=require"
```

Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1      # macOS/Linux: source .venv/bin/activate
```

Commit the skeleton:

```powershell
git add .gitignore docs/
git commit -m "chore: project skeleton with seed idea"
```

## Step 3 — Initialise OpenSpec

```powershell
openspec init
```

The interactive prompt asks which AI tools you use. Select **Antigravity**. Or skip the prompt:

```powershell
openspec init --tools antigravity
```

OpenSpec then:

- Creates the `openspec/` folder.
- Installs OpenSpec **skills** (`openspec-*/SKILL.md`) and **workflows** (`opsx-propose.md`, `opsx-apply.md`, and so on) in Antigravity's project folder. Depending on your OpenSpec version this is `.agent/` (older releases) or the shared `.agents/` root (newer releases, which migrate an existing `.agent/` automatically).
- Prints the exact command spelling for Antigravity.

Confirm the files exist:

```powershell
Get-ChildItem .agent*, .agents* -Recurse -Filter *.md | Select-Object FullName
```

Now make Antigravity pick them up:

1. Open the `incident-agent` folder as the workspace in Antigravity (**File → Open Folder**). Workflows are loaded per workspace, so the folder you open must be the one containing `.agent/` or `.agents/`.
2. Reload the window (Command Palette → **Developer: Reload Window**) or start a new conversation in the Agent panel.
3. In the Agent panel, type `/`. You should see `opsx-explore`, `opsx-propose`, `opsx-apply`, `opsx-update`, `opsx-sync`, `opsx-archive`.

Commit the generated folders so the workflows travel with the repo. Then commit:

```powershell
git add .
git commit -m "chore: initialise OpenSpec"
```

> **Optional: expanded workflow.** The default "core" profile gives you `explore`, `propose`, `apply`, `sync`, `archive`. If you want finer control (`/opsx-new`, `/opsx-continue`, `/opsx-ff`, `/opsx-verify`), run `openspec config profile`, select the expanded workflow, then `openspec update`. This guide uses the core profile and mentions `/opsx-verify` as an optional extra.

### 3.1 Antigravity settings that work well with OpenSpec

| Setting | Recommendation | Why |
| --- | --- | --- |
| **Conversation mode** | **Planning** for `/opsx-explore` and `/opsx-propose`; **Planning** or **Fast** for `/opsx-apply` | Planning mode makes the agent think before acting, which suits spec writing. Fast is fine for applying a well-reviewed `tasks.md`. |
| **Model** | Use a strong reasoning model for explore/propose | Spec quality depends on the model's reasoning more than on speed. |
| **Terminal command execution** | Keep it on *request review* (not auto-run) while learning | You will see every `openspec`, `pip`, and `pytest` command the agent runs, and you avoid it running `seed_rag.py` against Supabase unannounced. |
| **One conversation per change** | Start a new Agent conversation for each OpenSpec change | Keeps context small; OpenSpec artifacts on disk carry the state between conversations. |

> **Two kinds of "artifacts".** Antigravity shows its own *Artifacts* (task lists, implementation plans, walkthroughs) in the Agent panel. OpenSpec's artifacts are the Markdown files in `openspec/changes/<change>/`. **The OpenSpec files are the source of truth.** If Antigravity produces its own implementation plan during `/opsx-apply`, check it matches `tasks.md`, and comment on the plan if it drifts.

## Step 4 — Give OpenSpec Your Project Context

`openspec/config.yaml` is injected into every artifact the AI generates. Good context here is the single biggest quality lever. Replace (or create) the file with:

```yaml
# openspec/config.yaml
schema: spec-driven

context: |
  Project: Autonomous Incident Triage Agent.
  Seed idea: docs/idea.md (the original intent). Once capabilities are archived,
  specs in openspec/specs/ are the source of truth.

  Stack (zero-cost, no credit card):
  - Python 3.11
  - LLM: Gemini via Google AI Studio (langchain-google-genai); confirm current free-tier model names in AI Studio
  - Embeddings: Gemini embeddings, 768 dimensions (output_dimensionality=768)
  - Vector store + state: Supabase Postgres with pgvector, via the transaction pooler on port 6543
  - Agent engine: LangGraph with PostgresSaver checkpointer over psycopg_pool
  - App: FastAPI with Gradio Blocks mounted at "/", single ASGI object `app` in app.py
  - Hosting: Render free web service, start command `uvicorn app:app --host 0.0.0.0 --port $PORT`

  Files: seed_rag.py, agent.py, app.py, requirements.txt, db/migrations/*.sql, tests/.
  Secrets come only from environment variables (GEMINI_API_KEY, DATABASE_URL), loaded with python-dotenv locally.
  Developer OS: Windows + PowerShell (give PowerShell commands).

rules:
  proposal:
    - State which capability (knowledge-base, triage-agent, hitl-approval, triage-api, triage-ui, deployment) is affected
    - Include a rollback note
  specs:
    - Use SHALL/MUST requirements with GIVEN/WHEN/THEN scenarios
    - Every sensitive tool action MUST have a scenario covering approval AND rejection
    - Scenarios must be testable without calling real Gemini or Supabase
  design:
    - Record key decisions and the alternatives considered
    - Note free-tier limits that affect the design (rate limits, pooler, cold starts)
  tasks:
    - Include pytest tasks that mock the LLM and the database
    - Never include a task that writes secrets to a committed file
```

Commit it:

```powershell
git add openspec/config.yaml
git commit -m "chore: OpenSpec project context"
```

## Step 5 — Explore Before You Build

Before creating any change, let the agent turn the seed idea into a plan and challenge it. In your **AI chat**:

```text
/opsx-explore
Read docs/idea.md. I want to build this agent incrementally with OpenSpec.
Propose an architecture, the capabilities it breaks into, and how to split the work into
small changes that are each independently testable. Flag risks: security of the approval
step, making sure escalation can never bypass approval, free-tier limits, Supabase
transaction pooler quirks, and Render cold starts.
```

What to look for in the answer:

- A split similar to the roadmap below. If the agent suggests a different split, that is fine; the roadmap is a starting point, not a rule.
- Known pitfalls, e.g. the Supabase transaction pooler not supporting prepared statements (psycopg needs `prepare_threshold=None`), Render cold starts, and approval routing that only inspects the first tool call.
- Answers to open questions you can decide now (embedding dimension, how "sensitive" tools are marked). Put decisions you care about into the `/opsx-propose` prompts below.

`/opsx-explore` writes no code. Treat it as a design conversation. When you are satisfied, move on.

---

## The Change Roadmap

You will build the agent in six changes. Each one ends with an archive, so the specs grow step by step.

| # | Change name | Capability specs created/changed | Builds on | Outcome |
| --- | --- | --- | --- | --- |
| 1 | `add-knowledge-base` | `knowledge-base` (ADDED) | idea | pgvector table, match function, seeded runbooks |
| 2 | `add-triage-agent-core` | `triage-agent` (ADDED) | Change 1 | LangGraph agent with health + RAG tools and Postgres checkpointer |
| 3 | `add-hitl-escalation` | `hitl-approval` (ADDED) | Change 2 | `escalate_ticket` gated by an interrupt |
| 4 | `add-api-and-ui` | `triage-api`, `triage-ui` (ADDED) | Changes 2–3 | `/chat`, `/approve`, Gradio UI |
| 5 | `add-render-deployment` | `deployment` (ADDED) | Change 4 | Live service on Render |
| 6 | `harden-hitl-routing` | `hitl-approval` (MODIFIED) | Change 3 | Fixes a routing gap found via specs |

Every change follows the same five moves:

1. **Propose** in chat with `/opsx-propose <change-name>` plus a clear description.
2. **Review** the generated `proposal.md`, delta specs, `design.md`, and `tasks.md`. Edit them or ask the AI to revise (`/opsx-update`).
3. **Validate** in the terminal: `openspec validate <change-name>`.
4. **Apply** in chat with `/opsx-apply`, then run the tests yourself.
5. **Archive** in chat with `/opsx-archive`, then commit.

---

## Step 6 — Change 1: Knowledge Base

### 6.1 Propose

In AI chat:

```text
/opsx-propose add-knowledge-base
Build the runbook knowledge base described in docs/idea.md:
- A SQL migration file db/migrations/001_incident_docs.sql that enables pgvector, creates an
  incident_docs table (content, jsonb metadata, 768-dim embedding) and a match_incident_docs
  RPC function (cosine similarity, match_count, metadata filter). I will run it manually in the
  Supabase SQL Editor.
- requirements.txt for the whole project (gradio, fastapi, uvicorn, langgraph,
  langgraph-checkpoint-postgres, langchain-google-genai, langchain-core, psycopg[binary,pool],
  python-dotenv, pydantic, pytest).
- seed_rag.py that embeds three sample runbooks (auth 504 timeouts, database high latency,
  payment gateway failures) with Gemini embeddings (task_type RETRIEVAL_DOCUMENT, 768 dims)
  and inserts them through the pooler.
- Seeding must be idempotent (re-running must not create duplicates).
- Unit tests that mock the embeddings client and the DB connection.
```

### 6.2 Review what was generated

```powershell
openspec list
openspec show add-knowledge-base
```

Open `openspec/changes/add-knowledge-base/specs/knowledge-base/spec.md`. It should look roughly like this (edit if not):

```markdown
# Delta for knowledge-base

## ADDED Requirements

### Requirement: Runbook storage
The system SHALL store runbooks in the `incident_docs` table with content, JSON metadata,
and a 768-dimension embedding.

#### Scenario: Schema matches embedding size
- GIVEN the migration has been applied
- WHEN a 768-dimension vector is inserted
- THEN the insert succeeds
- AND a vector of any other dimension is rejected

### Requirement: Idempotent seeding
Running the seed script more than once SHALL NOT create duplicate runbook rows.

#### Scenario: Re-running the seed
- GIVEN the three runbooks were already seeded
- WHEN seed_rag.py runs again
- THEN the table still contains exactly three runbook rows

### Requirement: Semantic retrieval function
The database SHALL expose `match_incident_docs(query_embedding, match_count, filter)`
returning rows ordered by cosine similarity, filtered by metadata containment.

#### Scenario: Filter by service
- GIVEN runbooks for auth, database and payments
- WHEN match_incident_docs is called with filter {"service": "auth"}
- THEN only auth runbooks are returned
```

Also check `design.md` explains **how** idempotency works (e.g. a unique constraint on a content hash, or `ON CONFLICT DO NOTHING`), and that `tasks.md` includes tests.

### 6.3 Validate

```powershell
openspec validate add-knowledge-base
```

Fix any formatting errors it reports (usually a missing `#### Scenario:` under a requirement).

### 6.4 Apply

In AI chat:

```text
/opsx-apply
```

The assistant works through `tasks.md`, ticking boxes as it goes. Then do the manual parts yourself:

1. Open Supabase **SQL Editor** and run `db/migrations/001_incident_docs.sql`.
2. In the terminal:

   ```powershell
   pip install -r requirements.txt
   pytest -q
   python .\seed_rag.py
   python .\seed_rag.py     # run twice to prove idempotency
   ```

3. In Supabase **Table Editor**, confirm `incident_docs` has exactly three rows.

### 6.5 Archive and commit

In AI chat:

```text
/opsx-archive
```

Then in the terminal:

```powershell
git add .
git commit -m "feat: knowledge base (openspec: add-knowledge-base)"
```

Check `openspec/specs/knowledge-base/spec.md` now exists — that is your first living spec.

---

## Step 7 — Change 2: Core Triage Agent

This change deliberately includes **only the safe tools**. Escalation comes in Change 3, so you can see a spec evolve.

### 7.1 Propose

```text
/opsx-propose add-triage-agent-core
Implement agent.py with LangGraph, but ONLY the safe (read-only) path for now:
- psycopg_pool ConnectionPool (max_size 10, autocommit, connect_timeout 15, prepare_threshold None)
- Tools: query_service_health (mocked service table) and search_remediation_runbooks
  (pgvector search, embeddings with task_type RETRIEVAL_QUERY, top 2)
- AgentState with add_messages, system prompt: inspect health first, then search runbooks
- extract_text helper that normalises list-structured model content to a string
- LangGraph: agent -> safe_tools -> agent loop, END when no tool calls
- PostgresSaver checkpointer with setup(); get_agent_app() returns the compiled graph
- Do NOT add escalate_ticket yet.
- Tests: mock the LLM to emit tool calls and verify routing and state persistence by thread_id.
```

### 7.2 Review

Key requirements you should see in `specs/triage-agent/spec.md`:

- **Health-first investigation** — the agent SHALL check service health before searching runbooks.
- **Runbook retrieval** — returns the top 2 matches, or "No relevant runbooks found."
- **Unknown service** — `query_service_health("billing")` returns a not-found message rather than raising.
- **State persistence** — given a `thread_id`, a new process can load the same conversation state.
- **Content normalisation** — list-structured model output is flattened to plain text.

If "state persistence" is missing, ask the assistant to add it:

```text
/opsx-update add-triage-agent-core
Add a requirement with a scenario proving that conversation state survives a process restart
for the same thread_id.
```

### 7.3 Validate, apply, test

```powershell
openspec validate add-triage-agent-core
```

```text
/opsx-apply
```

```powershell
pytest -q
python -c "from agent import get_agent_app; from langchain_core.messages import HumanMessage; a=get_agent_app(); r=a.invoke({'messages':[HumanMessage('Auth service is timing out')]}, {'configurable':{'thread_id':'smoke-1'}}); print(r['messages'][-1].content)"
```

You should see a response that references the auth health status and the Redis/token-refresh runbook.

### 7.4 Archive and commit

```text
/opsx-archive
```

```powershell
git add .
git commit -m "feat: core triage agent (openspec: add-triage-agent-core)"
```

---

## Step 8 — Change 3: Human-in-the-Loop Escalation

### 8.1 Propose

```text
/opsx-propose add-hitl-escalation
Add the escalation path from docs/idea.md:
- Tool escalate_ticket(ticket_title, severity) — marked CRITICAL
- Separate sensitive_tools node; route_tools sends escalate_ticket there
- Compile with interrupt_before=["sensitive_tools"] so execution pauses for approval
- Resume on approval by invoking with None; on rejection, inject a ToolMessage
  "Rejected by engineer: <reason>" via update_state(as_node="sensitive_tools") and resume
- Update the system prompt: escalate if manual intervention is needed or the service stays degraded
- Tests for pause, approve, and reject paths using mocked LLM tool calls.
```

### 8.2 Review — this is the most important review in the guide

Open `specs/hitl-approval/spec.md`. Because of the rule in `config.yaml`, there must be scenarios for **both** approval and rejection. Expect something like:

```markdown
## ADDED Requirements

### Requirement: Sensitive actions require human approval
The agent MUST pause before executing any sensitive tool and MUST NOT execute it
without an explicit approval for that thread.

#### Scenario: Escalation pauses
- GIVEN an incident where the model decides to call escalate_ticket
- WHEN the graph runs
- THEN execution stops before the sensitive_tools node
- AND no ticket is created

#### Scenario: Approved escalation executes
- GIVEN a thread paused before sensitive_tools
- WHEN an engineer approves
- THEN escalate_ticket runs once and the agent produces a final response

#### Scenario: Rejected escalation is not executed
- GIVEN a thread paused before sensitive_tools
- WHEN an engineer rejects with a reason
- THEN escalate_ticket is never executed
- AND the agent receives the rejection reason and continues reasoning

#### Scenario: Pause survives restart
- GIVEN a thread paused before sensitive_tools
- WHEN the process restarts
- THEN the thread is still awaiting approval
```

Ask yourself: *is there any way a sensitive tool could run without approval?* Keep that question in mind; you will come back to it in Change 6.

### 8.3 Validate, apply, test, archive

```powershell
openspec validate add-hitl-escalation
```

```text
/opsx-apply
```

```powershell
pytest -q
```

```text
/opsx-archive
```

```powershell
git add .
git commit -m "feat: HITL escalation (openspec: add-hitl-escalation)"
```

---

## Step 9 — Change 4: REST API and Gradio UI

### 9.1 Propose

```text
/opsx-propose add-api-and-ui
Implement app.py:
- FastAPI app with POST /chat {thread_id, message} returning COMPLETED or AWAITING_APPROVAL
  (with pending_action and parameters)
- POST /approve {thread_id, approved, rejection_reason?} returning RESOLVED or REJECTED_AND_RESUMED,
  and HTTP 400 when nothing is pending for the thread
- Gradio Blocks UI: Thread ID, Incident Description, Trigger Triage, Approve Escalation,
  Reject Action, Rejection Reason, Workflow State label, Agent Log markdown
- Mount Gradio at "/" and expose the combined ASGI object as `app`
- Local run on PORT env var with 7860 fallback
- The REST handlers and the Gradio callbacks must share one service layer (no duplicated
  approve/reject logic).
- Tests with FastAPI TestClient and a mocked agent.
```

Note the last bullet: specs and design are the right place to record structural decisions like this, so they survive future changes.

### 9.2 Review

Check `specs/triage-api/spec.md` covers every status value and the 400 case, and `specs/triage-ui/spec.md` covers the approve/reject buttons with an empty Thread ID.

### 9.3 Validate, apply, run locally

```powershell
openspec validate add-api-and-ui
```

```text
/opsx-apply
```

```powershell
pytest -q
python app.py
```

- UI: `http://localhost:7860`
- API docs: `http://localhost:7860/docs`

Manual acceptance test (maps directly to your HITL scenarios):

1. Trigger triage with the default "Auth service is timing out… Escalate immediately." → state should be `AWAITING_APPROVAL`.
2. Click **Reject Action** with a reason → state `REJECTED`, no ticket created.
3. Use a new Thread ID, trigger again, click **Approve Escalation** → state `RESOLVED`, ticket text shown.
4. Stop the server while a thread is awaiting approval, restart, approve → it resumes (checkpointer works).

### 9.4 Archive and commit

```text
/opsx-archive
```

```powershell
git add .
git commit -m "feat: REST API and Gradio UI (openspec: add-api-and-ui)"
```

---

## Step 10 — Change 5: Deployment to Render

### 10.1 Propose

```text
/opsx-propose add-render-deployment
Prepare deployment to Render's free tier:
- Add a render.yaml blueprint (free web service, Python 3.11.9, build: pip install -r requirements.txt,
  start: uvicorn app:app --host 0.0.0.0 --port $PORT, env vars GEMINI_API_KEY and DATABASE_URL
  marked sync:false)
- Add a GET /healthz endpoint for Render health checks
- Add a README section with deploy steps and free-tier notes (15-minute spin-down, 30-60s cold start,
  state preserved via Postgres checkpointer)
- A task that verifies .env is not tracked by git
```

### 10.2 Review

Expected requirements in `specs/deployment/spec.md`:

- The service SHALL bind to the port provided in `$PORT`.
- Secrets SHALL come only from environment variables; `.env` SHALL NOT be committed.
- `GET /healthz` SHALL return 200 without calling Gemini or the database.
- A paused approval SHALL still be resumable after a cold start.

### 10.3 Validate, apply, deploy

```powershell
openspec validate add-render-deployment
```

```text
/opsx-apply
```

```powershell
git ls-files | Select-String ".env"     # must print nothing
git add .
git commit -m "feat: Render deployment (openspec: add-render-deployment)"
git branch -M main
git remote add origin https://github.com/<YOUR-USERNAME>/<YOUR-REPO>.git
git push -u origin main
```

Then in Render: **New → Blueprint** (uses `render.yaml`) or **New → Web Service** with build command `pip install -r requirements.txt`, start command `uvicorn app:app --host 0.0.0.0 --port $PORT`, instance type **Free**, and `PYTHON_VERSION=3.11.9`. Enter `GEMINI_API_KEY` and `DATABASE_URL` in the dashboard. Once deployed, repeat the manual acceptance test from Step 9.3 against `https://<YOUR-SERVICE-NAME>.onrender.com`.

### 10.4 Archive

```text
/opsx-archive
```

```powershell
git add .
git commit -m "docs: archive add-render-deployment"
git push
```

---

## Step 11 — Change 6: Evolve a Spec (MODIFIED Requirements)

This is where spec-driven development pays off. Re-read the HITL requirement you archived:

> The agent MUST pause before executing any sensitive tool and MUST NOT execute it without an explicit approval.

Now open `route_tools` (or whatever the agent named the routing function) in `agent.py`. A very common implementation, and quite possibly what was generated for you, looks like this:

```python
if last_message.tool_calls[0]["name"] == "escalate_ticket":
    return "sensitive_tools"
return "safe_tools"
```

It only inspects the **first** tool call. If your version already checks every tool call, still run this step: the change becomes "add regression tests and tighten the spec wording", which is just as good practice. If the model emits parallel tool calls such as `[query_service_health, escalate_ticket]`, the message is routed to `safe_tools`, which does not contain `escalate_ticket` — so the call either fails or, in a future refactor, runs unapproved. Either way, the code does not honour the spec.

### 11.1 Explore the gap

```text
/opsx-explore
Compare openspec/specs/hitl-approval/spec.md against route_tools in agent.py.
Can a sensitive tool bypass approval or break when the model returns multiple tool calls?
What are the options to fix it?
```

Typical options: route to `sensitive_tools` if **any** call is sensitive; disable parallel tool calls; or split mixed batches. Choose one.

### 11.2 Propose the change

```text
/opsx-propose harden-hitl-routing
Modify the HITL approval behaviour: if ANY tool call in the model's message is sensitive,
the whole message MUST go through the approval interrupt. The approval payload must list
every pending sensitive call. Rejection must answer every pending tool call with a ToolMessage.
Update /chat, /approve and the Gradio UI accordingly. Add regression tests for mixed
safe+sensitive tool calls.
```

### 11.3 Review the delta

This time the delta spec should use **MODIFIED**, not ADDED:

```markdown
# Delta for hitl-approval

## MODIFIED Requirements

### Requirement: Sensitive actions require human approval
The agent MUST pause before executing a model message if ANY of its tool calls is sensitive,
and MUST NOT execute any sensitive tool without explicit approval for that thread.
(Previously: only the first tool call was inspected.)

#### Scenario: Mixed safe and sensitive calls
- GIVEN the model returns [query_service_health, escalate_ticket] in one message
- WHEN the graph runs
- THEN execution pauses for approval
- AND the approval payload lists escalate_ticket

#### Scenario: Rejection answers every pending call
- GIVEN a paused message with two tool calls
- WHEN an engineer rejects
- THEN each tool call receives a ToolMessage and no sensitive tool executes
```

### 11.4 Validate, apply, archive

```powershell
openspec validate harden-hitl-routing
```

```text
/opsx-apply
```

```powershell
pytest -q
```

```text
/opsx-archive
```

```powershell
git add .
git commit -m "fix: route any sensitive tool call through HITL (openspec: harden-hitl-routing)"
git push
```

On archive, the MODIFIED requirement **replaces** the old one in `openspec/specs/hitl-approval/spec.md`, and the change folder is kept under `openspec/changes/archive/` as an audit trail.

---

## Step 12 — Inspect the Living Specs

```powershell
openspec list                 # should show no active changes
openspec view                 # interactive dashboard
Get-ChildItem openspec\specs -Recurse -Filter spec.md
Get-ChildItem openspec\changes\archive
```

You should have six capabilities: `knowledge-base`, `triage-agent`, `hitl-approval`, `triage-api`, `triage-ui`, `deployment`. These specs now describe the agent's behaviour better than the code comments do, and every future change (a new tool, PagerDuty integration, an auth layer for `/approve`) starts from them.

**Ideas for your next changes**

- `add-approve-endpoint-auth` — require an API key or role for `/approve` (currently anyone with the URL can approve).
- `add-real-health-checks` — replace the mocked `query_service_health` with real HTTP probes.
- `add-ticketing-integration` — make `escalate_ticket` create a real issue (GitHub Issues is free).
- `add-runbook-ingestion` — load runbooks from a `runbooks/` folder of Markdown files.

---

## Reviewing a Proposal: Checklist

Use this every time before you run `/opsx-apply`:

- [ ] **Scope** — `proposal.md` says what is in *and* out of scope for this change.
- [ ] **Capability** — the delta spec is under the right capability folder.
- [ ] **Requirements** — each uses SHALL/MUST and describes behaviour, not implementation.
- [ ] **Scenarios** — every requirement has at least one GIVEN/WHEN/THEN scenario; sensitive actions have approve *and* reject scenarios.
- [ ] **Testability** — scenarios can be tested with mocked Gemini and database.
- [ ] **Design** — `design.md` explains key decisions and alternatives, and stays consistent with `docs/idea.md` and existing specs.
- [ ] **Tasks** — small, ordered, include tests, and never write secrets to tracked files.
- [ ] **Validation** — `openspec validate <change>` passes.

If something is wrong, either edit the Markdown directly or ask: `/opsx-update <change> <what to fix>`.

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `/opsx-propose` doesn't appear when typing `/` | Wrong workspace folder open, or window not reloaded after `openspec init` | Open the `incident-agent` folder itself as the workspace; reload the window; run `openspec update` |
| Typed `/opsx:propose` (colon) | That's the Claude Code spelling | In Antigravity use `/opsx-propose` |
| Workflows exist but under `.agent/` and `.agents/` both | Upgraded OpenSpec across the folder migration | Run `openspec update`; keep the folder it regenerates and remove the stale duplicate |
| Agent writes code during `/opsx-propose` | Fast mode, or it skipped ahead | Use Planning mode; tell it "planning artifacts only, no code until /opsx-apply" |
| Antigravity's own plan differs from `tasks.md` | Agent generated a separate implementation plan | Comment on the plan in the Agent panel and point it back to `openspec/changes/<change>/tasks.md` |
| Agent runs `seed_rag.py` or `git push` unexpectedly | Terminal auto-execution enabled | Switch terminal execution to request review |
| `openspec validate` fails | Requirement without a `#### Scenario:` or wrong delta heading | Ensure headings are `## ADDED Requirements`, `### Requirement: ...`, `#### Scenario: ...` |
| Archive merged nothing into `openspec/specs/` | Change had no delta specs | Add a delta spec under `changes/<name>/specs/<capability>/spec.md`, re-validate, then archive |
| AI ignores your stack | `config.yaml` context is thin | Enrich `context:`; make sure `docs/idea.md` is referenced |
| `prepared statement already exists` errors | Transaction pooler + prepared statements | Keep `prepare_threshold=None` in the pool kwargs |
| Model or embedding name errors | Gemini model names change over time | Check the current names in Google AI Studio and update `agent.py`/`seed_rag.py` (and the spec, via a small change) |
| Render first request is slow | Free-tier spin-down | Expected; state persists in Postgres |

## Quick Reference

**Terminal**

```powershell
npm install -g @fission-ai/openspec@latest   # install / upgrade
openspec init --tools antigravity            # set up in a project for Antigravity
openspec update                               # regenerate Antigravity workflows after upgrade/profile change
openspec config profile                       # switch to the expanded workflow
openspec list                                 # active changes
openspec show <change>                        # view a change
openspec validate <change>                    # check spec formatting
openspec view                                 # dashboard
```

**Antigravity Agent panel**

```text
/opsx-explore                     think it through, no code
/opsx-propose <change> <details>  create proposal, delta specs, design, tasks
/opsx-update <change> <fix>       revise planning artifacts
/opsx-apply [<change>]            implement tasks
/opsx-sync                        merge delta specs into main specs (optional; archive also does it)
/opsx-archive                     merge specs and move change to archive
/opsx-verify                      (expanded profile) check code matches the artifacts
```

**Per-change rhythm**

```text
propose  →  review & edit  →  validate  →  apply  →  test  →  archive  →  commit
```
