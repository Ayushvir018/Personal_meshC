# Personal Mesh — AI Personal Memory Assistant

Personal Mesh is a conversational AI companion that remembers your life. Save thoughts, experiences, and notes in natural language, then query them semantically — your AI friend recalls context you forgot you stored.

Built with Streamlit, it combines a local vector database, a relational database, and a fast cloud LLM to deliver a private, always-available memory layer.

---

## Features

- **Natural language memory saving** — say "I had a great run this morning" and it saves automatically
- **Semantic search** — ask "what did I do for fitness?" and it retrieves relevant memories even without exact keyword matches
- **AI companion responses** — answers wrapped in a warm Hinglish personality (Billaa the cat 🐾)
- **Voice input** — speak your memories using on-device Whisper STT
- **Voice output** — responses read aloud via Microsoft Edge Neural TTS (Indian English)
- **Memory tagging** — auto-categorizes memories by type (health, work, personal, etc.) and priority
- **User authentication** — multi-user support with per-user memory isolation
- **Animated avatar** — Lottie-powered avatar with idle/thinking/talking states

---

## Tech Stack

| Layer | Technology |
|---|---|
| UI | Streamlit + Custom CSS (dark glassmorphism theme) |
| LLM | Groq API — Llama 3.1 8B Instant |
| Vector DB | ChromaDB (persistent, local) |
| Relational DB | SQLite (`memories.db`) |
| Embeddings | sentence-transformers `all-MiniLM-L6-v2` (384-dim) |
| STT | faster-whisper (Whisper small, CPU, int8) |
| TTS | edge-tts — `en-IN-NeerjaNeural` |
| Auth | SHA-256 password hashing via hashlib |
| Animation | streamlit-lottie |

---

## Project Structure

```
Personal_meshC-main/
├── app_new.py            # Main Streamlit app (UI, routing, chat loop)
├── companion_ui.py       # Animated avatar controller (idle/thinking/talking)
├── companion.py          # AI personality layer (greeting + response wrapping)
├── rag.py                # RAG pipeline (classify → retrieve → generate)
├── embedding.py          # Vector embedding store (ChromaDB interface)
├── memory_operations.py  # SQLite CRUD for memories
├── auth.py               # User registration and login
├── voice_engine.py       # Text-to-speech (edge-tts)
├── voice_input.py        # Speech-to-text (faster-whisper)
├── chroma_db/            # Persistent ChromaDB vector store
├── memories.db           # SQLite database (auto-created on first run)
├── .env                  # API keys (not committed)
└── requirements.txt      # Python dependencies
```

---

## How It Works — Architecture

### RAG Pipeline

Personal Mesh uses a **Retrieval-Augmented Generation** architecture with dual storage:

```
User Input
    │
    ▼
┌─────────────────────────────────┐
│  Intent Classification (Groq)   │  "memory" or "question"
└─────────────────────────────────┘
    │
    ├── If "memory" ──────────────────────────────────────────┐
    │                                                          ▼
    │                                               ┌──────────────────────┐
    │                                               │  SQLite INSERT        │
    │                                               │  ChromaDB ADD         │
    │                                               │  (dual write)         │
    │                                               └──────────────────────┘
    │
    └── If "question" ─────────────────────────────────────────┐
                                                               ▼
                                                    ┌──────────────────────┐
                                                    │ ChromaDB semantic     │
                                                    │ search (top 5)        │
                                                    └──────────┬───────────┘
                                                               │
                                                    ┌──────────▼───────────┐
                                                    │ SQLite full fetch +   │
                                                    │ deduplication         │
                                                    └──────────┬───────────┘
                                                               │
                                                    ┌──────────▼───────────┐
                                                    │ Context-augmented     │
                                                    │ Groq LLM generation   │
                                                    └──────────┬───────────┘
                                                               │
                                                    ┌──────────▼───────────┐
                                                    │ Companion personality │
                                                    │ wrapper (Hinglish)    │
                                                    └──────────────────────┘
```

### Dual Database Design

- **ChromaDB** stores 384-dimensional vector embeddings for semantic similarity search
- **SQLite** stores raw memory text with metadata (type, priority, timestamp, user_id) for exact filtering and CRUD
- Both are written simultaneously when saving a memory, combining structured queries with fuzzy semantic retrieval

---

## Setup & Installation

### 1. Clone the repository

```bash
git clone <repo-url>
cd Personal_meshC-main
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

Key packages needed:
```
streamlit
groq
chromadb
sentence-transformers
faster-whisper
sounddevice
edge-tts
streamlit-lottie
python-dotenv
numpy
```

### 3. Configure API keys

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key_here
```

Get a free Groq API key at [console.groq.com](https://console.groq.com).

### 4. Run the app

```bash
streamlit run app_new.py
```

The app will open at `http://localhost:8501`. The SQLite database and ChromaDB vector store are created automatically on first run.

---

## Usage

### Saving a Memory
Type naturally — the AI detects intent automatically:
- "I finished my ML assignment today"
- "Had biryani with Rahul, it was amazing"
- "Feeling stressed about the exam next week"

### Querying Memories
Ask questions in natural language:
- "What have I been eating lately?"
- "What did I study this week?"
- "How have I been feeling recently?"

### Voice Mode
Click the microphone button in the sidebar to speak your input. The AI will respond with both text and audio.

### Memory Page
Navigate to **Memories** in the sidebar to browse all saved memories with filters by type and priority.

---

## Models Used

| Task | Model | Details |
|---|---|---|
| Intent classification | Llama 3.1 8B Instant | Via Groq API, max_tokens=5 |
| Answer generation | Llama 3.1 8B Instant | Via Groq API, max_tokens=300 |
| Personality wrapping | Llama 3.1 8B Instant | Via Groq API, max_tokens=300 |
| Greeting generation | Llama 3.1 8B Instant | Via Groq API, max_tokens=80 |
| Text embeddings | all-MiniLM-L6-v2 | Local, 384 dimensions |
| Speech-to-text | Whisper small | Local, CPU int8 via faster-whisper |
| Text-to-speech | en-IN-NeerjaNeural | Microsoft Edge Neural TTS |

---

## Privacy

All memories are stored **locally** on your machine:
- `memories.db` — SQLite file in the project directory
- `chroma_db/` — ChromaDB vector store in the project directory

Only LLM inference calls are sent to the Groq API (the memory text used as context in prompts). No data is stored on external servers.
