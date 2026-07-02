# TeleNova

::: {align="center"}
## Enterprise AI-Powered Telecom Customer Support Platform on Google Cloud

TeleNova is a cloud-native conversational AI platform that modernizes
telecom customer support through a combination of Retrieval-Augmented
Generation (RAG), a modular multi-agent architecture, and managed Google
Cloud services.

It is designed to deliver grounded, context-aware responses for billing,
network, account, and general support requests while remaining scalable,
maintainable, and production-oriented.
:::

------------------------------------------------------------------------

## Table of Contents

-   Overview
-   Why TeleNova?
-   Features
-   System Architecture
-   Google Cloud Architecture
-   Multi-Agent Architecture
-   Retrieval-Augmented Generation Pipeline
-   Repository Structure
-   Database Design
-   Technology Stack
-   API Overview
-   Configuration
-   Local Development
-   Deployment
-   Testing
-   Security Considerations
-   Future Roadmap
-   License
-   Author

------------------------------------------------------------------------

# Overview

TeleNova combines FastAPI, Dialogflow CX, Gemini 2.5 Flash, Vertex AI
Vector Search, and AlloyDB into a single conversational platform.

Instead of relying exclusively on a language model, TeleNova retrieves
relevant knowledge from a curated knowledge base before response
generation. This grounding process helps produce responses that are more
consistent, explainable, and aligned with enterprise documentation.

------------------------------------------------------------------------

# Why TeleNova?

Telecom support organizations routinely handle:

-   Billing disputes
-   Plan comparisons
-   Network troubleshooting
-   Account management
-   Escalation requests

These requests often require searching multiple internal knowledge
sources before an accurate answer can be produced.

TeleNova addresses this by combining semantic retrieval with specialized
AI agents that can route requests, retrieve verified knowledge, and
generate grounded responses.

------------------------------------------------------------------------

# Features

-   Intent-aware request routing
-   Modular multi-agent architecture
-   Retrieval-Augmented Generation (RAG)
-   Gemini 2.5 Flash response generation
-   Vertex AI Vector Search semantic retrieval
-   AlloyDB metadata storage
-   Dialogflow CX integration
-   FastAPI REST backend
-   Structured logging
-   SQL migration workflow
-   Cloud-native deployment

------------------------------------------------------------------------

# System Architecture

``` text
                    User
                      │
                      ▼
               Dialogflow CX
                      │
                      ▼
                FastAPI Backend
                      │
                      ▼
             Intent Classification
                      │
                      ▼
                 Orchestrator
                      │
      ┌───────────────┼────────────────┐
      ▼               ▼                ▼
 Billing Agent   Network Agent   Support Agent
      │               │                │
      └───────────────┼────────────────┘
                      ▼
                Knowledge Agent
                      │
                      ▼
               Retrieval Pipeline
                      │
      ┌───────────────┼────────────────┐
      ▼               ▼                ▼
 Query Embedding  Vector Search   Metadata Lookup
      │               │                │
      └───────────────┼────────────────┘
                      ▼
              Gemini 2.5 Flash
                      │
                      ▼
               Grounded Response
```

------------------------------------------------------------------------

# Google Cloud Architecture

  Service                   Responsibility
  ------------------------- -------------------------------------------------
  Dialogflow CX             Conversation entry point and session management
  Gemini 2.5 Flash          Natural language generation
  Vertex AI Vector Search   Semantic nearest-neighbor retrieval
  AlloyDB for PostgreSQL    Customer records and knowledge metadata
  Cloud Storage             Knowledge base assets
  Cloud Run                 Backend deployment
  Cloud Build               Container build pipeline

------------------------------------------------------------------------

# Multi-Agent Architecture

TeleNova follows an orchestration pattern where incoming requests are
classified and routed to specialized agents.

  Agent              Purpose
  ------------------ --------------------------------
  Billing Agent      Billing and payment assistance
  Network Agent      Connectivity troubleshooting
  Support Agent      General support requests
  Knowledge Agent    Retrieval and grounding
  Escalation Agent   Human escalation workflows

This modular approach allows responsibilities to remain isolated and
simplifies future expansion.

------------------------------------------------------------------------

# Retrieval-Augmented Generation Pipeline

``` text
Markdown Knowledge Base
          │
          ▼
Document Chunking
          │
          ▼
gemini-embedding-001
          │
          ▼
Vertex AI Vector Search
          │
          ▼
Nearest Neighbor Retrieval
          │
          ▼
AlloyDB Metadata Lookup
          │
          ▼
Grounded Prompt Construction
          │
          ▼
Gemini 2.5 Flash
          │
          ▼
Customer Response
```

Workflow:

1.  Knowledge documents are loaded.
2.  Documents are chunked.
3.  Chunks are embedded with `gemini-embedding-001`.
4.  Embeddings are indexed in Vertex AI Vector Search.
5.  Metadata is stored in AlloyDB.
6.  Incoming queries are embedded.
7.  Similar knowledge chunks are retrieved.
8.  Retrieved context is added to the prompt.
9.  Gemini generates the final grounded response.

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

Core tables include:

-   customers
-   plans
-   billing_accounts
-   devices
-   support_tickets
-   chat_sessions
-   chat_messages
-   knowledge_chunks

`knowledge_chunks` stores textual content and metadata. Embeddings are
stored separately in Vertex AI Vector Search.

------------------------------------------------------------------------

# Technology Stack

  Layer                   Technology
  ----------------------- -------------------------
  Programming Language    Python 3.12
  Backend                 FastAPI
  AI SDK                  Google Gen AI SDK
  Language Model          Gemini 2.5 Flash
  Embeddings              gemini-embedding-001
  Semantic Retrieval      Vertex AI Vector Search
  Database                AlloyDB for PostgreSQL
  Conversation Platform   Dialogflow CX
  Cloud Platform          Google Cloud
  Containers              Docker

------------------------------------------------------------------------

# API Overview

The backend exposes endpoints for:

-   Health monitoring
-   Customer conversations
-   Agent orchestration
-   Knowledge retrieval
-   Billing and account operations

------------------------------------------------------------------------

# Configuration

Create a `.env` file from `.env.example` and configure:

-   GOOGLE_CLOUD_PROJECT
-   GOOGLE_CLOUD_LOCATION
-   DATABASE_URL
-   GEMINI_MODEL
-   DIALOGFLOW_AGENT_ID
-   GCS_BUCKET_NAME
-   VERTEX_INDEX_ID
-   VERTEX_INDEX_ENDPOINT_ID
-   VERTEX_DEPLOYED_INDEX_ID

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

Provision:

1.  AlloyDB
2.  Vertex AI Vector Search
3.  Dialogflow CX
4.  Cloud Storage
5.  Cloud Run

Deployment workflow:

1.  Apply SQL migrations.
2.  Configure environment variables.
3.  Load the knowledge base.
4.  Populate the vector index.
5.  Deploy the API.
6.  Configure the Dialogflow webhook.
7.  Validate end-to-end conversations.

------------------------------------------------------------------------

# Testing

Recommended validation:

-   API health endpoint
-   Database connectivity
-   Knowledge ingestion
-   Semantic retrieval
-   RAG grounding
-   Multi-turn conversations
-   Dialogflow webhook integration

------------------------------------------------------------------------

# Security Considerations

-   Secrets are managed through environment variables.
-   `.env` is excluded from version control.
-   Customer data is stored in AlloyDB.
-   Vector embeddings are managed by Vertex AI Vector Search.
-   Sensitive configuration remains outside the repository.

------------------------------------------------------------------------

# Future Roadmap

-   Hybrid lexical and semantic retrieval
-   Streaming responses
-   Automated evaluation pipeline
-   Conversation analytics dashboard
-   Multi-region deployment
-   Enhanced observability
-   Agent performance metrics

------------------------------------------------------------------------

# License

This project is licensed under the MIT License.

------------------------------------------------------------------------

# Author

**Krishna Joshi**
