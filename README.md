# TeleNova

## Enterprise AI-Powered Telecom Customer Support Platform on Google Cloud

TeleNova is a cloud-native conversational AI platform designed for
telecom customer support. It combines FastAPI, Dialogflow CX, Gemini 2.5
Flash, Vertex AI Vector Search, and AlloyDB to provide grounded,
context-aware customer assistance through a modular multi-agent
architecture.

------------------------------------------------------------------------

# Table of Contents

1.  Overview
2.  Problem Statement
3.  Solution Overview
4.  Key Features
5.  System Architecture
6.  Google Cloud Architecture
7.  Multi-Agent Design
8.  RAG Pipeline
9.  Repository Structure
10. Database Design
11. Technology Stack
12. API Overview
13. Configuration
14. Local Development
15. Deployment
16. Testing
17. Roadmap
18. License
19. Author

------------------------------------------------------------------------

# Overview

TeleNova addresses common telecom support challenges such as billing
inquiries, network troubleshooting, plan recommendations, and account
assistance. Rather than relying solely on an LLM, the platform retrieves
verified knowledge using Retrieval-Augmented Generation (RAG) before
generating responses, reducing hallucinations and improving consistency.

------------------------------------------------------------------------

# Problem Statement

Traditional telecom support systems often suffer from:

-   Long wait times
-   Repetitive manual troubleshooting
-   Fragmented knowledge bases
-   Inconsistent customer experiences

TeleNova combines semantic retrieval with large language models to
improve response quality while keeping the architecture modular and
cloud-native.

------------------------------------------------------------------------

# Key Features

-   Multi-agent orchestration
-   Intent-aware routing
-   Retrieval-Augmented Generation
-   Gemini 2.5 Flash
-   Vertex AI Vector Search
-   AlloyDB metadata storage
-   Dialogflow CX integration
-   FastAPI backend
-   Structured logging
-   SQL-based database migrations

------------------------------------------------------------------------

# System Architecture

``` text
User
 │
 ▼
Dialogflow CX
 │
 ▼
FastAPI
 │
 ▼
Intent Classification
 │
 ▼
Orchestrator
 │
 ├── Billing Agent
 ├── Network Agent
 ├── Support Agent
 ├── Knowledge Agent
 └── Escalation Agent
 │
 ▼
RAG Pipeline
 │
 ├── Embed Query
 ├── Vertex AI Vector Search
 ├── Retrieve Metadata (AlloyDB)
 └── Construct Grounded Prompt
 │
 ▼
Gemini 2.5 Flash
 │
 ▼
Grounded Response
```

------------------------------------------------------------------------

# Google Cloud Architecture

  Service                   Responsibility
  ------------------------- ------------------------------------
  Dialogflow CX             Conversation entry point
  Cloud Run                 FastAPI hosting
  Gemini 2.5 Flash          Response generation
  Vertex AI Vector Search   Semantic retrieval
  AlloyDB                   Operational and knowledge metadata
  Cloud Storage             Knowledge assets
  Cloud Build               Container build pipeline

------------------------------------------------------------------------

# Multi-Agent Design

The orchestrator routes incoming requests to specialized agents based on
detected intent.

  Agent        Responsibility
  ------------ ----------------------------------
  Billing      Billing and payment inquiries
  Network      Connectivity and troubleshooting
  Support      General customer assistance
  Knowledge    RAG retrieval and grounding
  Escalation   Human handoff workflows

------------------------------------------------------------------------

# Retrieval-Augmented Generation

1.  Markdown knowledge is loaded.
2.  Documents are chunked.
3.  Chunks are embedded using **gemini-embedding-001**.
4.  Embeddings are indexed in Vertex AI Vector Search.
5.  Metadata is stored in AlloyDB.
6.  User queries are embedded.
7.  Relevant chunks are retrieved.
8.  A grounded prompt is built.
9.  Gemini generates the final response.

------------------------------------------------------------------------

# Repository Structure

``` text
TeleNova/
├── app/
│   ├── agents/
│   ├── api/
│   ├── db/
│   ├── rag/
│   └── utils/
├── database/
│   └── migrations/
├── knowledge_base/
├── tests/
├── Dockerfile
├── requirements.txt
└── .env.example
```

------------------------------------------------------------------------

# Database Design

Primary tables:

-   customers
-   plans
-   billing_accounts
-   devices
-   support_tickets
-   chat_sessions
-   chat_messages
-   knowledge_chunks

`knowledge_chunks` stores textual metadata while vector embeddings are
stored in Vertex AI Vector Search.

------------------------------------------------------------------------

# Technology Stack

  Category       Technology
  -------------- -------------------------
  Language       Python 3.12
  Backend        FastAPI
  LLM            Gemini 2.5 Flash
  Embeddings     gemini-embedding-001
  Retrieval      Vertex AI Vector Search
  Database       AlloyDB for PostgreSQL
  Conversation   Dialogflow CX
  Cloud          Google Cloud
  Containers     Docker

------------------------------------------------------------------------

# API Overview

Core responsibilities include:

-   Customer chat endpoint
-   Health endpoint
-   Agent orchestration
-   Knowledge retrieval
-   Billing and account access

------------------------------------------------------------------------

# Configuration

Populate `.env` from `.env.example` and configure:

-   GOOGLE_CLOUD_PROJECT
-   GOOGLE_CLOUD_LOCATION
-   DATABASE_URL
-   GEMINI_MODEL
-   DIALOGFLOW_AGENT_ID
-   VERTEX_INDEX_ID
-   VERTEX_INDEX_ENDPOINT_ID
-   VERTEX_DEPLOYED_INDEX_ID
-   GCS_BUCKET_NAME

------------------------------------------------------------------------

# Local Development

``` bash
git clone <repository-url>
cd TeleNova

python -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt

cp .env.example .env

uvicorn app.main:app --reload
```

------------------------------------------------------------------------

# Deployment

1.  Provision AlloyDB.
2.  Provision Vertex AI Vector Search.
3.  Create Dialogflow CX agent.
4.  Configure Cloud Storage.
5.  Build and deploy to Cloud Run.
6.  Execute SQL migrations.
7.  Load the knowledge base.
8.  Validate end-to-end retrieval.

------------------------------------------------------------------------

# Testing

Recommended validation:

-   API health check
-   Database connectivity
-   Vector retrieval
-   RAG grounding
-   Multi-turn conversations
-   Dialogflow webhook integration

------------------------------------------------------------------------

# Roadmap

-   Hybrid lexical and semantic retrieval
-   Streaming responses
-   Evaluation pipeline
-   Analytics dashboard
-   Multi-region deployment
-   Enhanced observability

------------------------------------------------------------------------

# License

MIT License

------------------------------------------------------------------------

# Author

**Krishna Joshi**
