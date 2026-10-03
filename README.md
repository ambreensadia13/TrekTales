# 🧭 TrekTales AI

TrekTales AI is an AI-powered Pakistan travel planning application built with:

- Streamlit
- CrewAI
- Groq
- FAISS
- Sentence Transformers
- PyPDF
- Optional Groq vision
- JazzCash QR support

The application combines a tourism knowledge base with a multi-agent CrewAI workflow.

---

# ✨ Features

## 🗺️ AI Trip Planner

Users can provide:

- Destination
- Trip duration
- Budget
- Number of travelers
- Interests
- Custom travel request
- Response language

The application retrieves relevant tourism information before generating the final itinerary.

---

## 🤖 CrewAI Multi-Agent System

TrekTales uses four specialized agents:

### 1. Pakistan Tourism Researcher

Analyzes the tourism knowledge base.

### 2. Travel Itinerary Specialist

Creates the day-by-day itinerary.

### 3. Travel Safety Reviewer

Reviews transportation, safety and practical considerations.

### 4. Senior Travel Guide Writer

Combines everything into the final travel guide.

---

# ⚡ Groq

TrekTales uses Groq as the LLM provider.

The default model is:

```text
openai/gpt-oss-120b
