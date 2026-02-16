# **Product Brief: PDFProc v.2**

## **1\. Executive Summary**

**PDFProc v.2** is a complete re-architecture of an existing Python-based utility used daily for processing invoice PDFs. The current version (v.1) is functional but fragile, relying on file-system watchers, in-memory state, and expensive, non-deterministic AI prompting.

Version 2 aims to transform this utility into a robust, API-first application. It introduces a modular design that decouples business logic from AI providers, implements a cost-saving "Cascade" workflow for AI processing, and ensures data persistence via a database.

## **2\. Core Objectives**

* **Reliability:** Eliminate "amnesia" by persisting job state in a database (SQLite) instead of volatile memory.  
* **Cost Efficiency:** Implement a "fallback" workflow that attempts extraction using cheap, fast models (Text-Only) before escalating to expensive, smart models (Vision).  
* **Modularity:** Decouple the AI provider from the application logic using the Strategy Pattern. Allow seamless switching between OpenAI and Anthropic without code changes.  
* **Deterministic Logic:** Move business rules (company name normalization) out of the AI prompt and into pure Python code for instant, zero-cost, and error-free execution.

## **3\. Architecture Comparison**

| **Feature** | **PDFProc v.1 (Current)** | **PDFProc v.2 (Target)** |

| **Trigger** | watchdog (File System Events) | **FastAPI** (HTTP Upload Endpoint) |

| **State** | In-Memory Python Dictionary | **SQLModel** (SQLite Database) |

| **AI Parsing** | ast.literal\_eval (Fragile) | **Structured Outputs** (Pydantic Validation) |

| **AI Strategy** | Single Prompt (Text dumping) | **Cascade Workflow** (Text-First, Vision-Fallback) |

| **Normalization** | AI Hallucination/Prompting | **Local Python Logic** (Regex/Dict Matching) |

| **Dependency** | Hardcoded OpenAI | **Provider Agnostic** (OpenAI / Anthropic via Interface) |

## 

## **4\. Key Features & Components**

### **4.1. The "Cascade" AI Workflow**

To handle messy real-world PDFs (scans, garbled text) without breaking the bank, v.2 implements a two-tier processing pipeline:

1. **Tier 1 (Model A):** Fast, cheap, text-only model (e.g., gpt-4o-mini). It attempts to extract data from the raw text layer.  
2. **Tier 2 (Model B):** If Tier 1 fails or returns low-confidence results, the system renders the PDF pages as images and sends them to a smart, vision-capable model (e.g., gpt-4o).

### **4.2. Provider-Agnostic LLM Backend**

The system uses an abstract base class (LLMBackend) to interface with AI providers. This "MCP-like" philosophy allows the application to remain neutral regarding the underlying model.

* **Configuration:** controlled via .env (e.g., LLM\_PROVIDER="anthropic").  
* **Standardization:** Uses the instructor library to ensure all providers return the exact same Pydantic object structure.

### **4.3. Local Normalization Service**

Business logic for standardizing company names (e.g., mapping "Home Depot Inc." to "HomeDepot") is ported from the AI prompt to a dedicated Python service (app/services/normalizer.py).

* **Benefit:** Zero token cost, 100% consistency, easy to update shortnames dictionary.

### **4.4. Persistence Layer**

A lightweight SQLite database stores:

* **Jobs:** Upload status, timestamps, and error logs.  
* **Invoices:** Extracted metadata (Company, PO\#, Invoice\#) and links to the generated split files.

## **5\. Technical Stack**

* **Language:** Python 3.11+  
* **Web Framework:** FastAPI (Async)  
* **Database:** SQLModel (SQLite)  
* **PDF Processing:** PyMuPDF (fitz) for text extraction, image rendering, and splitting.  
* **AI Integration:** openai, anthropic, instructor.  
* **Validation:** Pydantic.

## 

## **6\. Configuration Strategy**

As defined in app/core/config.py, the system is highly configurable via environment variables:

\# Provider Selection  
LLM\_PROVIDER="openai" \# or "anthropic"

\# Model Selection for Cascade  
MODEL\_A\_NAME="gpt-4o-mini" \# The Cheap "Text" Worker  
MODEL\_B\_NAME="gpt-4o"      \# The Expensive "Vision" Worker

\# Paths  
UPLOAD\_DIR="uploads"  
PROCESSED\_DIR="processed"  
FAILED\_DIR="failed"

## **7\. Success Metrics**

* **Processing Success Rate:** \>99% of valid PDFs processed without crashing.  
* **Cost Reduction:** \>80% of invoices processed by Model A (Cheap) rather than Model B.  
* **Recovery:** Zero data loss on server restart (due to DB persistence).