# 🌿 TrekTales AI

TrekTales is an AI-powered tourism planning application built with Streamlit, Groq, FAISS and Sentence Transformers.

The application creates grounded travel itineraries using a local tourism knowledge base instead of allowing the language model to freely invent tourism information.

---

## Features

- AI-powered travel itinerary generation
- Groq API integration
- FAISS semantic retrieval
- Hybrid semantic + keyword retrieval
- Tourism knowledge base
- Eight-agent architecture
- Exact trip-day enforcement
- Day 1 free access
- Rs. 199 demo unlock for Days 2–3
- Payment screenshot analysis
- Deterministic payment validation
- Source propagation
- No itinerary generation when supporting knowledge is unavailable
- English, Urdu and Roman Urdu responses
- Streamlit interface

---

## Project Structure

```text
TrekTales-AI/
│
├── app.py
├── ingest.py
├── requirements.txt
├── README.md
├── .gitignore
│
├── assets/
│   └── jazzcash_qr.jpg
│
├── faiss_db/
│   ├── index.faiss
│   ├── metadata.json
│   └── config.json
│
├── tourism_knowledge_base/
│   ├── Pindi_Activities.pdf
│   ├── Pindi_Food.pdf
│   ├── Pindi_Hotels.pdf
│   ├── Pindi_Places.pdf
│   ├── Pindi_Safety.pdf
│   └── Pindi_Transport.pdf
│
└── src/
    ├── __init__.py
    ├── config.py
    ├── retriever.py
    ├── rag.py
    ├── agents.py
    ├── tasks.py
    ├── crew.py
    ├── citations.py
    ├── payment.py
    └── vision.py
