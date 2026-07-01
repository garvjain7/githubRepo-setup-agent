# Repo Setup Agent

> An AI-powered repository setup assistant that analyzes public GitHub repositories, generates setup instructions, and answers repository-specific questions using deterministic static analysis and agentic context retrieval.

---

## Overview

Setting up an unfamiliar GitHub repository is often more complicated than following a README. Projects may have undocumented environment variables, hidden dependencies, multiple startup steps, or framework-specific configurations that are difficult to infer manually.

Repo Setup Agent automates this process by combining **deterministic static analysis** with an **AI reasoning agent**.

Instead of sending an entire repository to an LLM, the system performs a one-time static analysis, builds lightweight code representations, and allows the AI to request only the information it actually needs during a conversation.

The project is completely **session-based**. No repository data, user conversations, or analysis results are permanently stored after the session ends.

---

# Features

- Analyze any public GitHub repository
- Generate step-by-step local setup instructions
- Interactive repository-specific AI chat
- Python AST skeletonization for efficient context retrieval
- Lazy function expansion through AI tool calls
- Automatic environment variable detection
- Framework and manifest detection
- Session-based architecture with automatic cleanup
- Redis-backed temporary caching
- Streaming AI responses

---

# How It Works

The system is divided into two phases.

## Phase 1 — Repository Analysis

When a repository is submitted, the backend performs a deterministic static analysis.

The analysis includes:

- Repository download
- Archive extraction
- Language detection
- Framework detection
- Manifest discovery
- Python AST parsing
- Skeleton generation
- Environment variable scanning
- Import map generation
- Session cache creation

No LLM is involved during this phase.

---

## Phase 2 — AI Conversation

After analysis is complete, users can interact with the repository through an AI assistant.

The agent receives:

- Stable repository context
- Conversation history
- Previously loaded code context

If additional information is required, the AI requests it using backend tools instead of receiving the complete repository.

This significantly reduces token usage while improving response quality.

---

# Architecture

```
GitHub Repository
        │
        ▼
 Repository Analysis
        │
        ▼
 Static Analysis
        │
        ▼
 Session Cache (Redis)
        │
        ▼
    AI Agent
        │
        ▼
  Interactive Chat
```

---

# Technology Stack

## Backend

- Python
- FastAPI

## Frontend

- HTML
- CSS
- JavaScript

## AI

- Gemini 2.5 Flash

## Cache

- Redis

## Static Analysis

- Python AST

---

# Project Structure

```
repo-setup-agent/

├── app/
│   ├── api/
│   ├── agent/
│   ├── repository/
│   ├── parser/
│   ├── context/
│   ├── llm/
│   ├── cache/
│   ├── templates/
│   ├── static/
│   └── utils/
│
├── workspaces/
├── logs/
├── tests/
```

---

# AI Context Retrieval

The AI never receives the entire repository by default.

Instead, it progressively gathers information as needed.

### Python files

- AST skeletons are generated during repository analysis.
- Function implementations are loaded only when requested.

### Non-Python files

- Raw file contents are provided on demand.

Configuration files such as:

- requirements.txt
- Dockerfile
- package.json
- .env.example

are always provided in full because of their relatively small size.

---

# Design Principles

The project is built around the following principles:

- Deterministic analysis before AI reasoning
- Minimize LLM token usage
- Progressive context retrieval
- Session-only storage
- Explicit failure over silent assumptions
- Simple, maintainable architecture

---

# Current Scope

### Supported

- Public GitHub repositories
- Python AST skeletonization
- Repository setup generation
- Repository Q&A
- Environment variable discovery
- Manifest parsing

### Not Supported

- Repository modification
- Code generation
- Pull requests
- Repository execution
- Multi-language AST analysis
- Persistent user sessions

---

# Session Lifecycle

```
Repository Submitted

        │

Download & Extract

        │

Static Analysis

        │

Session Cache

        │

Repository Chat

        │

Session Ends

        │

Workspace Deleted

        │

Redis Cache Cleared
```

---

# Project Status

🚧 Under active development.

The current version focuses on delivering a reliable and token-efficient repository understanding experience through deterministic analysis and controlled AI reasoning.

---

# License

This project is currently under development.
License information will be added upon the first public release.