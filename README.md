# UZAZI ASSISTANT

An intelligent AI assistant designed to provide accurate, reliable, and conversational responses about infertility and reproductive health. This full-stack web application combines a **React** frontend with a **Python RAG (Retrieval-Augmented Generation)** backend powered by **Google Gemini**. Users can register, log in, and ask questions that are answered using a **PDF knowledge base**, with built-in **misinformation correction** and balanced **traditional medicine guidance**.

> **Medical disclaimer:** This application provides educational information only. It is not a substitute for professional medical advice, diagnosis, or treatment. Always consult a qualified fertility specialist or healthcare provider.

---

## Features

| Feature | Description |
|---------|-------------|
| **User authentication** | Secure registration and login with JWT tokens |
| **PDF knowledge base** | Curated infertility documents ingested into a vector store |
| **RAG pipeline** | Retrieves relevant excerpts before generating answers |
| **Gemini AI** | Natural, conversational responses via Google Gemini API |
| **Intent detection** | Recognizes greetings, farewells, and help requests |
| **Misinformation correction** | Detects and gently corrects common fertility myths |
| **Traditional medicine** | Balanced context for TCM, Ayurveda, acupuncture, and herbs |
| **Source citations** | Shows which knowledge base documents informed each answer |
| **Conversation history** | Saves chat sessions per authenticated user |

---

## Architecture

```
┌─────────────────┐     REST API      ┌──────────────────────────────┐
│  React (Vite)   │ ◄──────────────► │  FastAPI (Python)             │
│  - Auth UI      │   /api/register   │  - JWT authentication        │
│  - Chat UI      │   /api/login      │  - SQLite user/conversations │
│                 │   /api/chat       │  - RAG engine                │
└─────────────────┘                   └──────────┬───────────────────┘
                                                 │
                    ┌────────────────────────────┼────────────────────────┐
                    ▼                            ▼                        ▼
            ┌──────────────┐            ┌─────────────────┐      ┌─────────────┐
            │ Vector Store │            │  PDF Knowledge  │      │ Gemini API  │
            │ (NumPy/file) │ ◄─ ingest ─│  Base (PDFs)    │      │ (generation)│
            └──────────────┘            └─────────────────┘      └─────────────┘
```

### RAG flow

1. User submits a question via the chat interface.
2. The question is embedded and matched against PDF chunks in the vector store.
3. Top-k relevant excerpts are injected into a structured system prompt.
4. Gemini generates a response grounded in those excerpts.
5. The prompt includes rules for myth correction and traditional medicine balance.
6. Sources are returned alongside the answer for transparency.

---

## Project structure

```
UZAZI_AI/
├── README.md
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entry point
│   │   ├── config.py            # Environment settings
│   │   ├── database.py          # SQLAlchemy setup
│   │   ├── models.py            # User, Conversation, Message
│   │   ├── schemas.py           # Pydantic request/response models
│   │   ├── auth/                # Password hashing, JWT
│   │   ├── rag/engine.py        # PDF ingest, retrieval, Gemini, intent detection
│   │   └── api/routes.py        # REST endpoints
│   ├── knowledge_base/          # Place PDF documents here
│   ├── scripts/
│   │   └── seed_knowledge_base.py  # Generate sample PDFs
│   ├── requirements.txt
│   └── .env
└── frontend/
    ├── src/
    │   ├── pages/               # Landing, Login, Register, Chat
    │   ├── components/          # Auth layout, route guards
    │   ├── context/             # Auth state
    │   └── api/client.ts        # API client
    ├── package.json
    └── vite.config.ts
```

---

## Prerequisites

- **Python 3.10+**
- **Node.js 18+**
- **Google Gemini API key** — get one at [Google AI Studio](https://aistudio.google.com/apikey)

---

## Setup

### 1. Clone and enter the project

```bash
cd demo
```

### 2. Backend setup

```bash
cd backend

# Create virtual environment
python -m venv .venv

# Activate (Windows PowerShell)
.\.venv\Scripts\Activate.ps1

# Activate (macOS/Linux)
# source .venv/bin/activate

pip install -r requirements.txt

# Configure environment
copy .env.example .env   # Windows
# cp .env.example .env  # macOS/Linux

# Edit .env and set your GEMINI_API_KEY and SECRET_KEY

# Generate sample PDF knowledge base
python scripts/seed_knowledge_base.py

# Start the API server
uvicorn app.main:app --reload --port 8000
```

The API will be available at `http://127.0.0.1:8000`.  
Interactive docs: `http://127.0.0.1:8000/docs`

On first startup, PDFs in `knowledge_base/` are automatically ingested into ChromaDB.

### 3. Frontend setup

Open a new terminal:

```bash
cd frontend
npm install
npm run dev
```

The app will be available at `http://localhost:5173`.

---

## Environment variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GEMINI_API_KEY` | Yes | — | Google Gemini API key |
| `SECRET_KEY` | Yes | dev default | JWT signing secret (change in production) |
| `DATABASE_URL` | No | `sqlite:///./data/app.db` | Database connection string |
| `KNOWLEDGE_BASE_DIR` | No | `./knowledge_base` | Directory containing PDF files |
| `CHROMA_PERSIST_DIR` | No | `./data/chroma` | Vector index storage path |
| `GEMINI_MODEL` | No | `gemini-2.0-flash` | Gemini model name |

---

## API endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/api/register` | No | Create account |
| `POST` | `/api/login` | No | Sign in, receive JWT |
| `GET` | `/api/me` | Yes | Current user profile |
| `POST` | `/api/chat` | Yes | Send message, get RAG response |
| `GET` | `/api/conversations` | Yes | List conversation history |
| `POST` | `/api/knowledge-base/ingest` | Yes | Re-ingest PDFs after updates |
| `GET` | `/health` | No | Health check |

### Example: chat request

```bash
curl -X POST http://127.0.0.1:8000/api/chat \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "Does stress alone cause infertility?"}'
```

---

## Adding your own PDF documents

1. Place PDF files in `backend/knowledge_base/`.
2. Restart the backend **or** call the ingest endpoint:

```bash
curl -X POST http://127.0.0.1:8000/api/knowledge-base/ingest \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

Recommended content for the knowledge base:

- Evidence-based infertility overviews (WHO, ASRM, NHS guidelines)
- Treatment option summaries
- Misinformation fact sheets
- Traditional/complementary medicine balanced reviews

## Intent Detection

UZAZI ASSISTANT includes intelligent intent detection that recognizes:

- **Greetings**: Hello, Hi, Habari, Mambo, Shikamoo, Hujambo
- **Farewells**: Bye, Goodbye, Kwaheri, Tutaonana
- **Appreciation**: Thank you, Thanks, Asante, Nashukuru
- **Help requests**: Help, Assist, Msaada, Saidia

When these intents are detected, the assistant responds appropriately without needing to query the knowledge base, making conversations feel more natural and human-like.

---

## Misinformation correction

The RAG system prompt instructs Gemini to identify and correct common myths, including:

- "Infertility is always the woman's fault"
- "Stress alone causes infertility"
- "IVF guarantees a baby"
- "You can wait until 40 without concern"
- "Herbal cures replace medical treatment"

Corrections are delivered in supportive, non-alarmist language.

---

## Traditional medicine guidance

When users ask about TCM, Ayurveda, acupuncture, or herbal remedies, the assistant:

- Acknowledges cultural and wellness perspectives
- Distinguishes evidence-supported vs. unproven claims
- Warns against stopping prescribed medical treatment
- Recommends informing the fertility care team about all supplements

---

## Production considerations

- Use a production-grade database (PostgreSQL) instead of SQLite
- Set a strong, random `SECRET_KEY`
- Serve the frontend build behind HTTPS (e.g., Nginx + `npm run build`)
- Rate-limit the `/api/chat` endpoint
- Review and expand the PDF knowledge base with medically vetted content
- Add content moderation and logging as needed for your deployment context
- Ensure compliance with healthcare data regulations (HIPAA, GDPR, etc.) if handling real patient data

---

## Tech stack

| Layer | Technology |
|-------|------------|
| Frontend | React 18, TypeScript, Vite, React Router |
| Backend | FastAPI, SQLAlchemy, Pydantic |
| Auth | JWT (python-jose), bcrypt (passlib) |
| Vector store | NumPy + sentence-transformers (file-backed) |
| PDF parsing | pypdf |
| LLM | Google Gemini API |

---

## License

This project is provided as an educational template. Verify all medical content with qualified professionals before use in production healthcare settings.
