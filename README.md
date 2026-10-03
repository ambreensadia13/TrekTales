# 🥾 TrekTales AI

## 8-Agent AI Tourism System

TrekTales is an AI-powered tourism planning application built with Streamlit, CrewAI, hybrid RAG, and xAI/Grok.

The application creates grounded travel plans using a tourism knowledge base containing PDF documents.

---

## 🤖 8 Agents

TrekTales contains exactly 8 agents:

1. Master Orchestrator
2. Knowledge Agent
3. Planner Agent
4. Budget Agent
5. Safety Agent
6. Summarizer Agent
7. Payment Agent
8. Vision Agent

The Master Orchestrator is included in the total count.

---

## 🧠 Architecture

```text
                    STREAMLIT
                       │
                       ▼
              MASTER ORCHESTRATOR
                       │
       ┌───────────────┼───────────────┐
       ▼               ▼               ▼
   KNOWLEDGE        PLANNER          BUDGET
     AGENT           AGENT            AGENT
       │               │               │
       └───────────────┼───────────────┘
                       ▼
                    SAFETY
                     AGENT
                       │
                       ▼
                 SUMMARIZER
                    AGENT
                       │
                       ▼
               FINAL ITINERARY
```

Payment:

```text
User
 │
 ▼
Day 1 FREE
 │
 ▼
Day 2/3 LOCKED
 │
 ▼
JazzCash QR
 │
 ▼
Screenshot Upload
 │
 ▼
VISION AGENT
 │
 ▼
Extract:
recipient
amount
status
 │
 ▼
PAYMENT AGENT
 │
 ▼
Deterministic Demo Validation
 │
 ▼
Unlock Day 2/3
```

---

## 📚 Hybrid RAG

TrekTales uses:

```text
Tourism PDFs
     ↓
PDF extraction
     ↓
Chunking
     ↓
FAISS + BM25
     ↓
Hybrid retrieval
     ↓
Cross-Encoder reranking
     ↓
Relevant evidence
     ↓
CrewAI agents
     ↓
Final answer
```

Each evidence item preserves:

* source filename
* page number
* department
* content

Example:

```text
SOURCE:
Pindi_Hotels.pdf

PAGE:
1

DEPARTMENT:
Hotels

CONTENT:
...
```

---

## 📁 Knowledge Base

Place these files inside:

```text
tourism_knowledge_base/
```

Expected files:

```text
Pindi_Places.pdf
Pindi_Hotels.pdf
Pindi_Transport.pdf
Pindi_Safety.pdf
Pindi_Food.pdf
Pindi_Activities.pdf
```

---

## ⚙️ Installation

Use Python 3.12.

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## 🧱 Build the Knowledge Base

After placing the PDFs inside:

```text
tourism_knowledge_base/
```

run:

```bash
python ingest.py
```

This creates:

```text
data/
└── faiss_index/
    ├── index.faiss
    └── metadata.json
```

Commit these generated files to GitHub before deploying if you do not want Streamlit Cloud to build the index during deployment.

---

## 🔑 Streamlit Secrets

Create:

```text
.streamlit/secrets.toml
```

for local testing:

```toml
XAI_API_KEY = "YOUR_XAI_API_KEY"
TEXT_MODEL = "grok-4.6"
VISION_MODEL = "grok-4.6"
```

Never commit:

```text
.streamlit/secrets.toml
```

to GitHub.

---

## 🚀 Streamlit Cloud

Upload the project to GitHub.

Then create a Streamlit Cloud application using:

```text
app.py
```

Set Python to:

```text
3.12
```

Add the following to Streamlit Cloud Secrets:

```toml
XAI_API_KEY = "YOUR_XAI_API_KEY"
TEXT_MODEL = "grok-4.6"
VISION_MODEL = "grok-4.6"
```

---

## 💳 Payment Demo

The application includes:

```text
Day 1
FREE
```

and:

```text
Day 2 + Day 3
Rs. 199
```

The user uploads a payment screenshot.

The Vision Agent extracts:

```text
recipient
amount
status
confidence
```

Python then checks:

```text
recipient == expected recipient
amount == 199
status == Sent / Successful / Completed
```

Only if these demo rules pass can the session be unlocked.

### Important

This is an **AI Screenshot Verification Demo**.

A screenshot alone does not prove that a real JazzCash transaction occurred.

Production payment verification should use an official payment-provider/backend verification mechanism rather than relying on a screenshot.

---

## 🛡️ Hallucination-Control Strategy

TrekTales does not intentionally fill missing tourism information with model knowledge.

The agents are instructed to:

* use supplied evidence
* preserve source names
* preserve page numbers
* avoid invented prices
* avoid invented hotel information
* avoid invented transport fares
* avoid invented addresses
* avoid invented emergency numbers
* avoid invented opening hours
* explicitly report missing information

If relevant information is absent, the expected response is:

```text
Information not found in the tourism knowledge base.
```

This provides grounded generation rather than claiming that an LLM can guarantee zero hallucinations.

---

## 🎨 UI

The TrekTales interface includes:

* modern tourism dashboard
* 8-agent activity panel
* travel planner
* language selection
* trip-duration selection
* traveler type
* knowledge-base citations
* Day 1 free access
* Day 2/3 payment gate
* JazzCash QR
* screenshot upload
* Grok Vision extraction
* deterministic demo payment validation
* unlocked extended itinerary

---

## 🔐 API Provider

TrekTales uses:

```text
xAI / Grok
```

Only.

No Groq API is required.

No OpenAI API key is required.

No Gemini API key is required.

No Serper API key is required.

---

## ⚠️ Information Disclaimer

TrekTales is a tourism information and planning application.

Knowledge-base information may not represent current prices, schedules, availability, road conditions, or other real-time circumstances.

Users should independently confirm time-sensitive travel information before making real-world decisions.

---

## 📄 License

This project is intended as an educational and hackathon-style AI tourism application.
