# 🌿 TrekTales AI

### AI-Powered Grounded Tourism Planner for Rawalpindi

TrekTales AI is an intelligent tourism planning application built with **Streamlit, Groq, FAISS, and Sentence Transformers**.

The application generates personalized travel itineraries for **Rawalpindi** by combining user preferences with information retrieved from a local tourism knowledge base.

Unlike a general-purpose chatbot, TrekTales is designed with a **Retrieval-Augmented Generation (RAG)** approach so that tourism recommendations are grounded in the application's indexed knowledge rather than relying entirely on the language model's general knowledge.

---

## ✨ Overview

TrekTales allows travelers to provide information such as:

- Starting location
- Trip duration
- Number of travelers
- Daily budget
- Travel style
- Interests
- Preferred response language

The system then retrieves relevant information from the Rawalpindi tourism knowledge base and uses Groq-powered AI agents to organize that information into a structured itinerary.

The application is designed to provide:

> **Personalized → Knowledge-Grounded → Source-Aware → Tourist-Friendly**

travel planning.

---

# 🚀 Key Features

## 🧭 Personalized Itinerary Generation

TrekTales creates travel plans based on the user's:

- Travel duration
- Group size
- Budget preference
- Travel style
- Starting location
- Interests

The generated itinerary can organize activities into:

- Morning
- Afternoon
- Evening
- Meal/rest breaks
- Daily highlights
- Known-cost summaries
- Final trip summary

---

## 📚 Retrieval-Augmented Generation

TrekTales uses a local tourism knowledge base rather than allowing the language model to freely invent tourism information.

The general pipeline is:

```text
Tourism PDFs
     ↓
Document Processing
     ↓
Text Chunks
     ↓
Sentence Transformer Embeddings
     ↓
FAISS Index
     ↓
Hybrid Retrieval
     ↓
Relevant Tourism Evidence
     ↓
Groq AI
     ↓
Personalized Itinerary
