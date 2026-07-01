# TeleNova AI Support Assistant

> A production-grade, cloud-native Conversational AI customer support system built with **Dialogflow CX**, **Gemini 2.5 Flash**, **Google ADK**, and **FastAPI** — deployed on **Google Cloud Run**.

---

## Project Overview

TeleNova AI Support automates customer service interactions for a fictional telecom company, TeleNova. Customers interact through Dialogflow CX and receive intelligent, context-aware responses grounded in a private knowledge base via a RAG pipeline powered by Gemini.

**This project demonstrates:**
- Production Dialogflow CX agent design with multi-turn conversation flows
- Gemini-grounded response generation via RAG (Retrieval-Augmented Generation)
- Google ADK multi-agent orchestration (Support, Billing, Network, Escalation agents)
- Context-aware, session-persistent conversations
- FastAPI webhook backend deployed on Cloud Run
- Full observability (request_id, intent, latency, token_count, cost estimation)

---

## Business Problem

A telecom company needs to deflect 60–70% of Tier 1 support contacts to an AI system that can:

| Customer Need | System Capability |
|---|---|
| Billing questions & disputes | Billing Agent + RAG over billing FAQ |
| Plan upgrades & comparisons | RAG over plan comparison guide |
| Network issues & outages | Network Agent + diagnostics |
| Ticket status lookups | Support Agent with mock CRM |
| Account information | Account verification + session context |
| Escalation to human agents | Escalation Agent with warm handoff |

---

## Architecture

```
Customer (Web / Voice / Chat)
         │
         ▼
  Dialogflow CX Agent
  ┌─────────────────────────┐
  │  Intent Detection        │
  │  Entity Extraction       │
  │  Flow Routing            │
  │  Slot Filling            │
  └────────────┬────────────┘
               │ Webhook (HTTPS POST)
               ▼
  FastAPI Backend (Cloud Run)
  ┌─────────────────────────────────────┐
  │  /webhook  ──►  Agent Orchestrator  │
  │  /chat     ──►  Session Manager     │
  │  /health   ──►  Status Check        │
  └────────────┬────────────────────────┘
               │
               ▼
  Google ADK Multi-Agent Layer
  ┌──────────┐ ┌──────────┐ ┌─────────┐ ┌───────────┐
  │ Support  │ │ Billing  │ │ Network │ │Escalation │
  │  Agent   │ │  Agent   │ │  Agent  │ │   Agent   │
  └────┬─────┘ └────┬─────┘ └────┬────┘ └─────┬─────┘
       └────────────┴────────────┴─────────────┘
                         │
                         ▼
              RAG Pipeline
  ┌─────────────────────────────────────┐
  │  User Query                          │
  │     ▼                                │
  │  ChromaDB Vector Store               │
  │  (text-embedding-004)                │
  │     ▼                                │
  │  Top-K Relevant Chunks               │
  │     ▼                                │
  │  Gemini 2.5 Flash (Grounded)         │
  │     ▼                                │
  │  Structured Response                 │
  └─────────────────────────────────────┘
               │
               ▼
  Knowledge Base (GCS + ChromaDB)
  ┌────────────────────────────┐
  │  billing_faq.md            │
  │  network_troubleshooting.md│
  │  plan_comparison.md        │
  │  escalation_sop.md         │
  │  customer_support_handbook │
  └────────────────────────────┘
```

---

## Project Structure

```
telecom-support-ai/
├── app/
│   ├── agents/
│   │   ├── support_agent.py        # Primary ADK agent (ticket, account, data tools)
│   │   ├── billing_agent.py        # Billing ADK agent (charges, credits, history)
│   │   ├── network_agent.py        # Network ADK agent (outages, diagnostics, reset)
│   │   ├── escalation_agent.py     # Escalation ADK agent (priority, handoff, goodwill)
│   │   └── orchestrator.py         # Intent router → agent selector
│   ├── api/
│   │   ├── models.py               # Pydantic request/response models
│   │   └── routes.py               # FastAPI endpoints (/chat, /webhook, /health)
│   ├── rag/
│   │   ├── vector_store.py         # ChromaDB loader + retrieval
│   │   └── pipeline.py             # Gemini grounded generation
│   ├── utils/
│   │   ├── session.py              # Session + conversation state management
│   │   └── observability.py        # Structured logging + request metrics
│   └── config.py                   # Pydantic settings from environment
├── knowledge_base/
│   ├── billing_faq.md
│   ├── network_troubleshooting.md
│   ├── plan_comparison.md
│   ├── escalation_sop.md
│   └── customer_support_handbook.md
├── dialogflow_cx/
│   ├── agent.json                  # Agent-level configuration
│   ├── intents/intents.json        # All intents + training phrases
│   ├── entities/entities.json      # Custom entities (plan_type, ticket_id, etc.)
│   └── flows/flows.json            # Flows, pages, routes, webhook config
├── deployment/
│   ├── deploy.sh                   # Cloud Run deployment script
│   └── setup_local.sh              # Local development setup
├── docs/
│   ├── INTERVIEW_HANDBOOK.md
│   └── INTERVIEW_QUESTIONS.md
├── main.py                         # Application entrypoint
├── Dockerfile
├── requirements.txt
├── .env.example
└── README.md
```

---

## Dialogflow CX Design

### Intent Hierarchy

| Intent Display Name | Category | Key Parameters |
|---|---|---|
| `general.support` | Entry | — |
| `billing.inquiry` | Billing | — |
| `billing.dispute` | Billing | `charge_amount` |
| `plan.upgrade` | Plan | `plan_name` |
| `network.issue` | Network | `zip_code`, `issue_type` |
| `ticket.status` | Account | `ticket_id` |
| `escalation.request` | Escalation | — |
| `account.information` | Account | `account_number` |

### Flow Architecture

```
Default Start Flow
    │
    ├── billing.inquiry / billing.dispute ──► Billing Flow
    │       ├── Page: Account Verification (slot fill: account_number)
    │       └── Page: Billing Resolution (webhook: billing_inquiry)
    │
    ├── network.issue / signal_problem ──► Network Flow
    │       ├── Page: Collect Network Info (slot fill: zip_code)
    │       └── Page: Network Troubleshooting (webhook: network_issue)
    │
    ├── plan.upgrade / plan.inquiry ──► Plan Flow
    │       └── Page: Plan Comparison (webhook: plan_inquiry)
    │
    ├── ticket.status ──► Ticket Flow
    │       └── Page: Ticket Lookup (slot fill: ticket_id)
    │
    └── escalation.request ──► Escalation Flow
            ├── Page: Assess Escalation (webhook: escalation_request)
            └── Page: Live Agent Handoff
```

### Slot Filling Example

For network issues, Dialogflow CX collects `zip_code` through multi-turn slot filling before invoking the webhook, ensuring the backend has all parameters needed for outage lookups.

---

## RAG Pipeline

```
1. User query arrives at /chat or /webhook
2. Intent classification determines topic category
3. Category-filtered semantic search against ChromaDB
   (text-embedding-004 embeddings, cosine similarity)
4. Top-4 chunks retrieved with relevance scores
5. Chunks injected into Gemini prompt template with:
   - Knowledge base context
   - Conversation history (last 10 turns)
   - Intent classification
   - System persona (Nova)
6. Gemini 2.5 Flash generates grounded response
7. Response returned with source attribution
```

**Embedding Model**: `text-embedding-004` (768 dimensions)
**Vector Store**: ChromaDB (persistent, cosine similarity)
**Generation Model**: Gemini 2.5 Flash
**Chunk Size**: 600 words with 100-word overlap

---

## Google ADK Agents

Each ADK agent has specialized tools:

### Support Agent
- `check_account_status` — Account status, plan, balance
- `get_ticket_status` — Ticket lookup by ID
- `get_data_usage` — Current cycle data consumption
- `create_support_ticket` — New ticket creation

### Billing Agent
- `get_billing_details` — Itemized bill breakdown
- `apply_billing_credit` — Goodwill credit (up to $50)
- `check_payment_history` — Recent payment records

### Network Agent
- `check_network_status` — ZIP-code outage lookup
- `run_remote_diagnostic` — Line-level signal/SIM diagnostics
- `provision_network_reset` — Remote provisioning reset

### Escalation Agent
- `assess_escalation_priority` — Priority scoring + tier recommendation
- `initiate_human_handoff` — Context-aware transfer with case ID
- `apply_goodwill_gesture` — Credits, data bonus, or free month

---

## Observability

Every request returns structured telemetry:

```json
{
  "observability": {
    "request_id": "550e8400-e29b-41d4-a716-446655440000",
    "session_id": "d290f1ee-6c54-4b01-90e6-d701748f0851",
    "intent": "billing_inquiry",
    "latency_ms": 487.3,
    "token_count_input": 842,
    "token_count_output": 156,
    "total_tokens": 998,
    "estimated_cost_usd": 0.000110
  }
}
```

---

## Local Development

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/telecom-support-ai.git
cd telecom-support-ai

# 2. Set up credentials
cp .env.example .env
# Edit .env with your GCP project ID and API keys

# 3. Run setup script
chmod +x deployment/setup_local.sh
./deployment/setup_local.sh

# 4. Start the server
source venv/bin/activate
python main.py
```

API docs available at: `http://localhost:8080/docs`

### Test the API

```bash
# Health check
curl http://localhost:8080/health

# Start a conversation
curl -X POST http://localhost:8080/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Why is my bill higher than usual this month?"}'

# Continue with session context
curl -X POST http://localhost:8080/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Can you show me my usage breakdown?",
    "session_id": "SESSION_ID_FROM_PREVIOUS_RESPONSE",
    "account_number": "TN-100001"
  }'
```

---

## Cloud Run Deployment

### Prerequisites
- Google Cloud project with billing enabled
- APIs enabled: Cloud Run, Artifact Registry, Cloud Storage, Vertex AI, Dialogflow CX
- Service account with roles: `run.admin`, `storage.admin`, `aiplatform.user`, `dialogflow.admin`

### Deploy

```bash
export GOOGLE_CLOUD_PROJECT=your-project-id
export GOOGLE_CLOUD_LOCATION=us-central1
chmod +x deployment/deploy.sh
./deployment/deploy.sh
```

The script:
1. Builds and pushes the Docker image to Google Container Registry
2. Creates the GCS bucket and uploads knowledge base documents
3. Deploys to Cloud Run with auto-scaling (1–10 instances)
4. Outputs the service URL for Dialogflow CX webhook configuration

### Configure Dialogflow CX Webhook

After deployment, update your Dialogflow CX agent:

1. Navigate to **Manage → Webhooks** in Dialogflow CX Console
2. Create webhook: `https://YOUR_CLOUD_RUN_URL/webhook`
3. Set timeout: 10 seconds
4. Assign webhook to fulfillment in relevant flow pages


