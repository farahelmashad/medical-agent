#  Cairo Medical Center - AI Receptionist Agent

A conversational AI agent that handles end-to-end medical appointment management for a clinic. Patients can book, cancel, and update appointments, ask about doctors, and get clinic information.

Live demo → [Cairo Medical Center on HF Spaces](https://huggingface.co/spaces/farahelmashad/medical-agent)

---

[![Demo Video](https://img.shields.io/badge/Watch%20Demo-YouTube-red?style=for-the-badge&logo=youtube)](your-youtube-link-here)


---

## What it does

- **Book appointments** : finds available slots, collects patient details, confirms booking
- **Cancel appointments** : retrieves existing booking, confirms with patient, frees the slot
- **Update appointments** : change doctor, date, time, or contact info 
- **Answer questions** : doctor specializations, availability, fees, clinic location, hours, insurance
- **Send emails** : confirmation, cancellation, and update emails via Gmail API

---

## How it works

```
Patient message
      ↓
LangGraph Agent (ReAct loop)
      ↓
   /      \
RAG       Tools
(Qdrant)  (Sheets + Gmail)
      ↓
   Reply
```


---

## Stack

| Layer | Technology |
|---|---|
| Agent orchestration | LangGraph |
| LLM | Gemini 1.5 Flash |
| RAG / Vector search | Qdrant Cloud + sentence-transformers |
| Appointment database | Google Sheets API |
| Email | Gmail API (OAuth 2.0) |
| Backend | FastAPI |
| Frontend | Streamlit |
| Deployment | Hugging Face Spaces (Docker) |

