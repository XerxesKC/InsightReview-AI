# InsightReview AI

InsightReview AI is an AI-powered local life service review platform. It started from a lightweight review and merchant discovery system, then evolved into a three-sided intelligent platform for users, merchants, and administrators.

The project combines a traditional business system with AI agent capabilities. It supports merchant search, review management, knowledge base governance, document processing, retrieval-augmented generation, conversational assistants, and natural-language data analysis.

## What It Does

InsightReview AI is designed around three roles:

- Users can search for merchants, view shop details, interact with content, save favorites, and ask the user assistant for consumption suggestions.
- Merchants can manage shop information, publish posts, handle reviews, upload documents, and use the merchant assistant to understand feedback and operational issues.
- Administrators can manage users and merchants, review documents, maintain knowledge bases, configure agent parameters, and analyze conversation logs.

The goal is to turn scattered business data such as merchant profiles, user reviews, operation documents, and chat records into searchable, conversational, analyzable, and auditable knowledge assets.

## Architecture

The project is organized into three main applications:

```text
RateVue
  Frontend application built with Vue.
  Provides user, merchant, and administrator interfaces.

ReviewPulse Engine
  Java Spring Boot business backend.
  Handles core business data, MySQL persistence, file upload, and API proxying.

ReviewPulse Agent
  Python FastAPI AI service.
  Provides RAG, multi-turn chat, knowledge base management, document processing,
  OCR, Pandas analysis, and sandboxed code execution.
```

## Repository Structure

```text
.
├─ RateVue/                 Vue frontend source code
├─ ReviewPulse Engine/      Spring Boot backend source code
├─ ReviewPulse Agent/       Python FastAPI AI agent source code
├─ sample-data/             Typical sample data and SQL scripts
└─ docs/                    Deployment notes, resource notes, and helper scripts
```

## Key Features

- Three-sided business platform for users, merchants, and administrators.
- Merchant search, map search, shop details, favorites, posts, reviews, and replies.
- User-side and merchant-side AI assistants with multi-turn context support.
- Knowledge base management with document upload, review, chunk preview, intelligent splitting, and vectorization.
- RAG workflow with vector retrieval, sparse retrieval, reranking, query rewriting, and context trimming.
- Multi-agent task handling for planning, routing, retrieval, analysis, tool execution, and response synthesis.
- OCR support for extracting text from image inputs.
- Natural-language Pandas analysis for CSV/Excel-style business data.
- E2B sandbox execution for generated analysis code.
- Conversation log management with hot question analysis, message trends, and retrieval success statistics.

## Tech Stack

Frontend:

- Vue
- Vite
- Element Plus
- Axios

Business Backend:

- Java
- Spring Boot
- MyBatis Plus
- MySQL

AI Agent Service:

- Python
- FastAPI
- LangGraph
- Chroma
- Redis
- BGE embedding model
- Large language model API
- E2B Code Interpreter
- Pandas

## Local Development Notes

This repository contains source code and typical sample data. It does not include heavy dependencies, build outputs, local virtual environments, runtime logs, complete model files, or private API keys.

A complete local demo usually requires:

- Java 21 or a compatible JDK
- Maven
- Node.js and npm
- Python or Conda environment
- MySQL
- Redis
- Local Chroma storage directory
- Local BGE embedding model path
- LLM API key
- E2B API key

See the documentation under `docs/` for more detailed deployment notes and resource descriptions.

## Data And Models

The `sample-data/` directory contains typical SQL scripts and small sample files for development and demonstration. Full datasets, runtime vector databases, dependency libraries, and model weights are intentionally excluded from the repository.

You should configure local paths and credentials according to your own environment before running the full system.

## Security Notes

Do not commit real `.env` files, API keys, database passwords, model credentials, or private runtime data. Use example configuration files and local environment variables for sensitive settings.

## Project Status

InsightReview AI is a personal full-stack AI application project focused on combining practical business workflows with agent-based AI capabilities. The current version supports local demonstration and further extension.