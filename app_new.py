import streamlit as st
from dotenv import load_dotenv
import os

# Load environment variables at the very beginning
load_dotenv()

import time
from memory_operations import *
from datetime import date
from companion import generate_greeting, get_recent_memories
import base64

# ── Level 3 Companion Imports ────────────────────────────────────────────────
try:
    from voice_engine import text_to_speech_bytes
    VOICE_ENGINE_OK = True
except Exception:
    VOICE_ENGINE_OK = False

try:
    from companion_ui import render_billaa, inject_avatar_css
    AVATAR_OK = True
except Exception:
    AVATAR_OK = False

def get_base64_of_bin_file(bin_file):
    with open(bin_file, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

# Initialize database on first run
if not os.path.exists("memories.db"):
    conn = sqlite3.connect("memories.db")
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Create memories table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS memories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        content TEXT NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        user_id TEXT DEFAULT 'ayush',
        type TEXT DEFAULT 'personal',
        priority TEXT DEFAULT 'medium',
        tags TEXT DEFAULT ''
    )
    """)
    
    conn.commit()
    conn.close()

# Ensure summaries table exists
conn = sqlite3.connect("memories.db")
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS summaries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT,
    period TEXT,
    summary TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")
conn.commit()
conn.close()


st.set_page_config(
    page_title="Personal Mesh",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

from auth import login_user, register_user

# ── Authentication ──────────────────────────────────────────────────────────
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.current_user = None
    st.session_state.companion_greeting = None
    st.session_state.greeting_shown = False

# ── Avatar & Voice State ─────────────────────────────────────────────────────
if "avatar_state" not in st.session_state:
    st.session_state.avatar_state = "idle"
if "voice_muted" not in st.session_state:
    st.session_state.voice_muted = False
if "pending_audio" not in st.session_state:
    st.session_state.pending_audio = None

if not st.session_state.logged_in:
    st.markdown("""
    <div style="max-width:400px; margin: 5rem auto; text-align:center;">
        <h1 style="font-family:'Syne',sans-serif; background:linear-gradient(135deg,#00d4aa,#0088ff);
        -webkit-background-clip:text; -webkit-text-fill-color:transparent; font-size:1.8rem; white-space:nowrap;">
        ⬡ PERSONAL MESH</h1>
        <p style="color:#4a6080; font-size:0.75rem; letter-spacing:0.15em;">YOUR AI MEMORY LAYER</p>
    </div>
    """, unsafe_allow_html=True)

    tab_login, tab_register = st.tabs(["Login", "Register"])

    with tab_login:
        username = st.text_input("Username", key="login_user")
        password = st.text_input("Password", type="password", key="login_pass")
        if st.button("Login"):
            success, msg = login_user(username, password)
            if success:
                st.session_state.logged_in = True
                st.session_state.current_user = username
                # Generate companion greeting on login
                try:
                    recent_mems = get_recent_memories(username, limit=3)
                    st.session_state.companion_greeting = generate_greeting(username, recent_mems)
                except Exception:
                    st.session_state.companion_greeting = f"Hey {username} 👋 wapas aa gaye! Kya scene hai aaj?"
                st.session_state.greeting_shown = False
                st.rerun()
            else:
                st.error(msg)

    with tab_register:
        new_user = st.text_input("Username", key="reg_user")
        new_pass = st.text_input("Password", type="password", key="reg_pass")
        if st.button("Register"):
            success, msg = register_user(new_user, new_pass)
            if success:
                st.success(msg)
                st.info("Ab login karo.")
            else:
                st.error(msg)

    st.stop()

# ── Custom CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=JetBrains+Mono:wght@300;400;500&display=swap');

:root {
    --bg:        #090d12;
    --surface:   #0f1520;
    --border:    #1a2535;
    --accent:    #00d4aa;
    --accent2:   #0088ff;
    --text:      #e0eaf5;
    --muted:     #4a6080;
    --danger:    #ff4466;
}

/* Base */
html, body, [data-testid="stAppViewContainer"] {
    background: var(--bg) !important;
    color: var(--text) !important;
    font-family: 'JetBrains Mono', monospace !important;
}

/* Hide default Streamlit elements, but KEEP header for sidebar toggle */
#MainMenu, footer { visibility: hidden; }
header { background: transparent !important; }
[data-testid="stHeader"] { background: transparent !important; }
[data-testid="stDecoration"] { display: none; }

/* Sidebar */
[data-testid="stSidebar"] {
    background: var(--surface) !important;
    border-right: 1px solid var(--border) !important;
}

[data-testid="stSidebar"] * {
    font-family: 'Syne', sans-serif !important;
}

/* Logo area */
.mesh-logo {
    padding: 2rem 1rem 1rem;
    text-align: center;
}

.mesh-logo h1 {
    font-family: 'Syne', sans-serif !important;
    font-weight: 800;
    font-size: 1.3rem; /* Reduced further to ensure no wrapping */
    white-space: nowrap; /* Forces text to stay in one line */
    letter-spacing: -0.01em;
    background: linear-gradient(135deg, var(--accent), var(--accent2));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0;
}

.mesh-logo p {
    font-size: 0.65rem;
    color: var(--muted);
    letter-spacing: 0.15em;
    text-transform: uppercase;
    margin: 0.3rem 0 0;
}

/* Nav buttons */
.stRadio > div {
    gap: 0.3rem !important;
}

.stRadio label {
    background: transparent !important;
    border: 1px solid transparent !important;
    border-radius: 8px !important;
    padding: 0.6rem 1rem !important;
    cursor: pointer !important;
    transition: all 0.2s !important;
    font-size: 0.85rem !important;
}

.stRadio label:hover {
    background: var(--border) !important;
    border-color: var(--border) !important;
}

/* Page title */
.page-title {
    font-family: 'Syne', sans-serif;
    font-weight: 700;
    font-size: 1.8rem;
    color: var(--text);
    margin-bottom: 0.2rem;
    letter-spacing: -0.02em;
}

.page-subtitle {
    font-size: 0.75rem;
    color: var(--muted);
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-bottom: 2rem;
}

/* Chat messages */
.chat-user {
    display: flex;
    justify-content: flex-end;
    margin: 0.8rem 0;
}

.chat-user .bubble {
    background: linear-gradient(135deg, #003d80, #0055aa);
    border: 1px solid var(--accent2);
    border-radius: 16px 16px 4px 16px;
    padding: 0.8rem 1.2rem;
    max-width: 70%;
    font-size: 0.9rem;
    line-height: 1.5;
}

.chat-ai {
    display: flex;
    justify-content: flex-start;
    margin: 0.8rem 0;
}

.chat-ai .bubble {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 16px 16px 16px 4px;
    padding: 0.8rem 1.2rem;
    max-width: 75%;
    font-size: 0.9rem;
    line-height: 1.6;
}

.chat-ai .avatar {
    width: 32px;
    height: 32px;
    background: linear-gradient(135deg, var(--accent), var(--accent2));
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.9rem;
    margin-right: 0.6rem;
    flex-shrink: 0;
    margin-top: 0.2rem;
}

/* Memory cards */
.memory-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1rem 1.2rem;
    margin-bottom: 0.8rem;
    transition: border-color 0.2s;
}

.memory-card:hover {
    border-color: var(--accent);
}

.memory-card .meta {
    font-size: 0.7rem;
    color: var(--muted);
    margin-bottom: 0.4rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}

.memory-card .content {
    font-size: 0.88rem;
    color: var(--text);
    line-height: 1.5;
}

.tag {
    display: inline-block;
    background: rgba(0, 212, 170, 0.1);
    border: 1px solid rgba(0, 212, 170, 0.3);
    color: var(--accent);
    border-radius: 20px;
    padding: 0.15rem 0.6rem;
    font-size: 0.65rem;
    margin-right: 0.3rem;
    letter-spacing: 0.05em;
}

.badge {
    display: inline-block;
    border-radius: 4px;
    padding: 0.1rem 0.5rem;
    font-size: 0.65rem;
    font-weight: 600;
    letter-spacing: 0.05em;
    text-transform: uppercase;
}

.badge-high   { background: rgba(255,68,102,0.15); color: #ff4466; border: 1px solid rgba(255,68,102,0.3); }
.badge-medium { background: rgba(255,165,0,0.15);  color: #ffaa00; border: 1px solid rgba(255,165,0,0.3); }
.badge-low    { background: rgba(0,212,170,0.15);  color: #00d4aa; border: 1px solid rgba(0,212,170,0.3); }

/* Stat cards */
.stat-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1.2rem;
    text-align: center;
}

.stat-card .number {
    font-family: 'Syne', sans-serif;
    font-size: 2rem;
    font-weight: 800;
    background: linear-gradient(135deg, var(--accent), var(--accent2));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.stat-card .label {
    font-size: 0.7rem;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-top: 0.2rem;
}

/* Input styling */
.stTextInput input, .stTextArea textarea, .stSelectbox select {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    color: var(--text) !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.88rem !important;
}

.stTextInput input:focus, .stTextArea textarea:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 2px rgba(0,212,170,0.15) !important;
}

/* Buttons */
.stButton button {
    background: linear-gradient(135deg, var(--accent), var(--accent2)) !important;
    color: #000 !important;
    border: none !important;
    border-radius: 8px !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important;
    font-size: 0.85rem !important;
    letter-spacing: 0.05em !important;
    padding: 0.5rem 1.5rem !important;
    transition: opacity 0.2s !important;
}

.stButton button:hover {
    opacity: 0.85 !important;
}

/* Chat input */
.stChatInput textarea {
    background: var(--surface) !important;
    border: 1px solid var(--accent) !important;
    border-radius: 12px !important;
    color: var(--text) !important;
    font-family: 'JetBrains Mono', monospace !important;
}

/* Divider */
hr { border-color: var(--border) !important; }

/* Scrollbar */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: var(--muted); }

/* Companion greeting */
.companion-greeting {
    background: linear-gradient(135deg, rgba(0,212,170,0.08), rgba(0,136,255,0.08));
    border: 1px solid rgba(0,212,170,0.2);
    border-radius: 16px;
    padding: 1.2rem 1.5rem;
    margin-bottom: 1.5rem;
    display: flex;
    align-items: center;
    gap: 1rem;
    animation: fadeInGreeting 0.6s ease-out;
}

.companion-greeting img {
    border-radius: 50%;
    border: 2px solid rgba(0,212,170,0.4);
}

.companion-greeting .greeting-text {
    font-family: 'Syne', sans-serif;
    font-size: 1.05rem;
    color: var(--text);
    line-height: 1.5;
}

@keyframes fadeInGreeting {
    from { opacity: 0; transform: translateY(-10px); }
    to { opacity: 1; transform: translateY(0); }
}

/* Typing animation for responses */
@keyframes blink {
    0%, 100% { opacity: 1; }
    50% { opacity: 0; }
}

.typing-cursor {
    display: inline-block;
    width: 2px;
    height: 1em;
    background: var(--accent);
    animation: blink 0.7s infinite;
    margin-left: 2px;
    vertical-align: text-bottom;
}

</style>
""", unsafe_allow_html=True)

# ── Background Watermark (Billa) ──
st.markdown("""
<style>
[data-testid="stAppViewContainer"]::before {
    content: "";
    position: fixed;
    top: 50%%;
    left: 50%%;
    width: 500px;
    height: 500px;
    background-image: url("data:image/png;base64,%s");
    background-size: contain;
    background-repeat: no-repeat;
    background-position: center;
    opacity: 0.06;
    transform: translate(-50%%, -50%%);
    pointer-events: none;
    z-index: 0;
}
</style>
""" % (get_base64_of_bin_file("cat_avatar.png")), unsafe_allow_html=True)


# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="mesh-logo">
        <h1>⬡ PERSONAL MESH</h1>
        <p>Your AI Memory Layer</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    if "page" not in st.session_state:
        st.session_state.page = "💬  Chat"

    page = st.radio(
        "",
        ["💬  Chat", "🧠  Memory"],
        index=0 if st.session_state.page == "💬  Chat" else 1,
        label_visibility="collapsed",
        key="nav_radio"
    )
    st.session_state.page = page

    st.markdown("---")

    # ── Voice Mute Toggle ────────────────────────────────────────────────────
    voice_label = "🔇 Muted" if st.session_state.voice_muted else "🔊 Voice"
    if st.button(voice_label, key="mute_btn", use_container_width=True):
        st.session_state.voice_muted = not st.session_state.voice_muted
        st.rerun()

    st.markdown("---")

    # Quick stats in sidebar
    try:
        stats = get_stats(st.session_state.current_user)
        total = stats['total']
        st.markdown(f"""
        <div style="padding: 0.5rem 0; font-size: 0.75rem; color: var(--muted);">
            <div style="display:flex; justify-content:space-between; margin-bottom:0.4rem;">
                <span>MEMORIES</span>
                <span style="color: var(--accent); font-weight:600;">{total}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    except:
        pass

    st.markdown("---")
    st.markdown(f'<div style="font-size:0.75rem; color:var(--muted);">👤 {st.session_state.current_user}</div>', unsafe_allow_html=True)
    if st.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.current_user = None
        st.session_state.chat_history = []
        st.rerun()


# ── CHAT PAGE ─────────────────────────────────────────────────────────────────
if "Chat" in st.session_state.page:

    # Inject avatar CSS globally (MUST be before columns — inside a column it renders as raw text)
    if AVATAR_OK and not st.session_state.get("_avatar_css_done"):
        inject_avatar_css()
        st.session_state._avatar_css_done = True

    # Hide the audio player widget (we only want to HEAR it, not see it)
    st.markdown("""
    <style>
    [data-testid="stAudio"] { display: none !important; }
    </style>
    """, unsafe_allow_html=True)

    # ── Two-column Layout: Avatar (left) | Chat (right) ──────────────────────
    avatar_col, chat_col = st.columns([1, 4], gap="medium")

    # ── LEFT: Animated Avatar ────────────────────────────────────────────────
    with avatar_col:
        st.markdown('<div style="height:1.5rem"></div>', unsafe_allow_html=True)
        if AVATAR_OK:
            avatar_placeholder = st.empty()
            with avatar_placeholder.container():
                render_billaa(st.session_state.avatar_state, key="base")
        else:
            st.markdown('<div style="text-align:center;font-size:4rem">🐱</div>', unsafe_allow_html=True)

    # ── RIGHT: Chat Area ─────────────────────────────────────────────────────
    with chat_col:
        st.markdown('<div class="page-title">Ask Personal Mesh</div>', unsafe_allow_html=True)
        st.markdown('<div class="page-subtitle">Your AI — powered by your memories</div>', unsafe_allow_html=True)

        # ── Companion Greeting (once per session) ─────────────────────────────
        if st.session_state.get("companion_greeting") and not st.session_state.get("greeting_shown", False):
            st.markdown(f"""
            <div class="companion-greeting">
                <div class="greeting-text">🐾 {st.session_state.companion_greeting}</div>
            </div>
            """, unsafe_allow_html=True)
            st.session_state.greeting_shown = True

        # Init chat history
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []

        # ── Render Chat History ───────────────────────────────────────────────
        for idx, msg in enumerate(st.session_state.chat_history):
            if msg["role"] == "user":
                st.markdown(f"""
                <div class="chat-user">
                    <div class="bubble">{msg["content"]}</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                is_new = msg.get("new", False)
                if is_new:
                    # ── TALKING STATE: typing effect + voice playback ─────────
                    # Update avatar to TALKING
                    if AVATAR_OK:
                        with avatar_placeholder:
                            render_billaa("talking", key="active")

                    # Generate and play voice via st.audio (reliable autoplay)
                    if VOICE_ENGINE_OK and not st.session_state.voice_muted:
                        try:
                            audio_bytes = text_to_speech_bytes(msg["content"])
                            if audio_bytes:
                                st.audio(audio_bytes, format="audio/mp3", autoplay=True)
                        except Exception:
                            pass

                    # Word-by-word typing effect
                    placeholder = st.empty()
                    words = msg["content"].split()
                    displayed = ""
                    for word in words:
                        displayed += (" " if displayed else "") + word
                        placeholder.markdown(f"""
                        <div class="chat-ai">
                            <div class="avatar">🐾</div>
                            <div class="bubble">{displayed}<span class="typing-cursor"></span></div>
                        </div>
                        """, unsafe_allow_html=True)
                        time.sleep(0.04)

                    # Final render without cursor
                    placeholder.markdown(f"""
                    <div class="chat-ai">
                        <div class="avatar">🐾</div>
                        <div class="bubble">{msg["content"]}</div>
                    </div>
                    """, unsafe_allow_html=True)

                    # Back to IDLE after typing
                    st.session_state.chat_history[idx]["new"] = False
                    st.session_state.avatar_state = "idle"
                    if AVATAR_OK:
                        with avatar_placeholder:
                            render_billaa("idle", key="active")

                else:
                    st.markdown(f"""
                    <div class="chat-ai">
                        <div class="avatar">🐾</div>
                        <div class="bubble">{msg["content"]}</div>
                    </div>
                    """, unsafe_allow_html=True)

        # ── Empty State ───────────────────────────────────────────────────────
        if not st.session_state.chat_history:
            st.markdown("""
            <div style="text-align:center; padding: 3rem 2rem; color: var(--muted);">
                <div style="font-size: 3rem; margin-bottom: 1rem;">⬡</div>
                <div style="font-family: 'Syne', sans-serif; font-size: 1.1rem; color: var(--text); margin-bottom: 0.5rem;">
                    Ask me anything about your life
                </div>
                <div style="font-size: 0.8rem; line-height: 1.8; margin-bottom: 2rem;">
                    "What projects have I built?"<br>
                    "Tell me about my hackathon performance"<br>
                    "What are my skills?"
                </div>
            </div>
            """, unsafe_allow_html=True)

        # ── Input Row: Chat + Voice Mic ───────────────────────────────────────
        col_chat_input, col_voice = st.columns([6, 1])
        with col_voice:
            voice_chat_btn = st.button("🎙️", use_container_width=True)
        with col_chat_input:
            question = st.chat_input("Ask anything or share a memory...")

    # ── Handle Voice Input ────────────────────────────────────────────────────
    if voice_chat_btn:
        # → THINKING
        st.session_state.avatar_state = "thinking"
        with st.spinner("Recording 5s... please speak!"):
            try:
                from voice_input import voice_to_text
                spoken = voice_to_text(duration=5)
            except ImportError as e:
                st.error(f"Voice dependencies missing: {str(e)}")
                spoken = None
            except Exception as e:
                st.error(f"Microphone error: {str(e)}")
                spoken = None
        
        if spoken:

            st.session_state.chat_history.append({"role": "user", "content": spoken})
            # → Show THINKING state immediately
            if AVATAR_OK:
                with avatar_placeholder:
                    render_billaa("thinking", key="active")
            try:
                from rag import process_input
                intent, response = process_input(spoken, st.session_state.current_user)
            except Exception as e:
                response = f"Error: {str(e)}"
            # → Set TALKING for next render
            st.session_state.avatar_state = "talking"
            st.session_state.chat_history.append({"role": "assistant", "content": response, "new": True})
        else:
            st.session_state.avatar_state = "idle"
        st.rerun()

    # ── Handle Text Input ─────────────────────────────────────────────────────
    if question:
        st.session_state.chat_history.append({"role": "user", "content": question})
        # → Show THINKING state immediately
        st.session_state.avatar_state = "thinking"
        if AVATAR_OK:
            with avatar_placeholder:
                render_billaa("thinking", key="active")
        
        try:
            from rag import process_input
            intent, response = process_input(question, st.session_state.current_user)
        except Exception as e:
            response = f"Error: {str(e)}"
        # → TALKING (typing effect + voice will run on next render)
        st.session_state.avatar_state = "talking"
        st.session_state.chat_history.append({"role": "assistant", "content": response, "new": True})
        st.rerun()


# ── MEMORY PAGE ───────────────────────────────────────────────────────────────
elif "Memory" in st.session_state.page:

    tab1, tab2, tab3, tab4 = st.tabs(["＋  Add", "  Browse", "  Stats", "📊  Summaries"])

    # ── ADD TAB
    with tab1:
        st.markdown('<div style="height:1rem"></div>', unsafe_allow_html=True)
        st.markdown('<div class="page-title" style="font-size:1.3rem">New Memory</div>', unsafe_allow_html=True)
        st.markdown('<div style="height:1rem"></div>', unsafe_allow_html=True)

        # Voice input at top
        col_mic, col_dur = st.columns([2, 1])
        with col_mic:
            record_btn = st.button("🎙️ Record Voice Memory")
        with col_dur:
            duration = st.selectbox("Duration", [5, 10, 15, 30], index=1, label_visibility="collapsed")

        if record_btn:
            with st.spinner(f"Recording {duration}s... speak now!"):
                from voice_input import voice_to_text
                transcript = voice_to_text(duration=duration)
            if transcript:
                st.session_state.voice_transcript = transcript
            else:
                st.warning("Could not hear anything. Check your mic.")

        # Pre-fill content from voice if available
        default_content = st.session_state.get("voice_transcript", "")

        content = st.text_area("What happened?", value=default_content, height=120, placeholder="Describe your memory or record voice above...")

        col1, col2 = st.columns(2)
        with col1:
            mem_type = st.selectbox("Type", ["project", "personal", "health", "work"])
            priority = st.selectbox("Priority", ["medium", "high", "low"])
        with col2:
            mem_date = st.date_input("Date", value=date.today())

        tags = st.text_input("Tags", placeholder="ai, project, health ...")

        if st.button("Save Memory"):
            if content.strip():
                result = add_memory(content, st.session_state.current_user, mem_type, priority, str(mem_date), tags)

                st.success(result)
                st.session_state.voice_transcript = ""
            else:
                st.error("Please enter some content.")


    # ── BROWSE TAB
    with tab2:
        st.markdown('<div style="height:1rem"></div>', unsafe_allow_html=True)

        col1, col2 = st.columns([3, 1])
        with col1:
            search_q = st.text_input("", placeholder="Search memories...", label_visibility="collapsed")
        with col2:
            type_filter = st.selectbox("", ["all", "project", "personal", "health", "work"], label_visibility="collapsed")

        memories = get_all_memories(st.session_state.current_user)

        if search_q:
            memories = [m for m in memories if search_q.lower() in m[1].lower()]
        if type_filter != "all":
            memories = [m for m in memories if m[4] == type_filter]

        st.markdown(f'<div style="font-size:0.75rem; color:var(--muted); margin-bottom:1rem;">{len(memories)} memories</div>', unsafe_allow_html=True)

        for mem in memories:
            tags_html = ""
            if len(mem) > 6 and mem[6]:
                for tag in mem[6].split(","):
                    if tag.strip():
                        tags_html += f'<span class="tag">#{tag.strip()}</span>'

            priority_badge = f'<span class="badge badge-{mem[5]}">{mem[5]}</span>' if mem[5] else ""
            type_badge = f'<span class="badge" style="background:rgba(0,136,255,0.1);color:#0088ff;border:1px solid rgba(0,136,255,0.3)">{mem[4]}</span>'

            st.markdown(f"""
            <div class="memory-card">
                <div class="meta">#{mem[0]} · {mem[2][:10]} · {type_badge} {priority_badge}</div>
                <div class="content">{mem[1]}</div>
                {'<div style="margin-top:0.6rem">' + tags_html + '</div>' if tags_html else ''}
            </div>
            """, unsafe_allow_html=True)

    # ── STATS TAB
    with tab3:
        st.markdown('<div style="height:1rem"></div>', unsafe_allow_html=True)
        try:
            stats = get_stats(st.session_state.current_user)

            total = stats['total']
            project_count = sum([c for t, c in stats['by_type'] if t == 'project'])
            high_count = sum([c for p, c in stats['by_priority'] if p == 'high'])
            personal_count = sum([c for t, c in stats['by_type'] if t == 'personal'])

            c1, c2, c3, c4 = st.columns(4)
            for col, num, label in [
                (c1, total, "Total"),
                (c2, project_count, "Projects"),
                (c3, personal_count, "Personal"),
                (c4, high_count, "High Priority")
            ]:
                with col:
                    st.markdown(f"""
                    <div class="stat-card">
                        <div class="number">{num}</div>
                        <div class="label">{label}</div>
                    </div>
                    """, unsafe_allow_html=True)

            st.markdown('<div style="height:1.5rem"></div>', unsafe_allow_html=True)

            if stats['by_type']:
                import plotly.graph_objects as go
                col1, col2 = st.columns(2)

                with col1:
                    labels = [i[0] for i in stats['by_type']]
                    values = [i[1] for i in stats['by_type']]
                    fig = go.Figure(data=[go.Pie(
                        labels=labels, values=values, hole=0.6,
                        marker=dict(colors=['#00d4aa','#0088ff','#ff4466','#ffaa00'])
                    )])
                    fig.update_layout(
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        font=dict(color='#e0eaf5', family='JetBrains Mono'),
                        showlegend=True,
                        height=280,
                        margin=dict(t=20, b=20, l=20, r=20)
                    )
                    st.plotly_chart(fig, use_container_width=True)

                with col2:
                    if stats['by_priority']:
                        priorities = [i[0] for i in stats['by_priority']]
                        counts = [i[1] for i in stats['by_priority']]
                        colors = {'high': '#ff4466', 'medium': '#ffaa00', 'low': '#00d4aa'}
                        fig2 = go.Figure(data=[go.Bar(
                            x=priorities, y=counts,
                            marker_color=[colors.get(p, '#4a6080') for p in priorities],
                            marker_line_width=0
                        )])
                        fig2.update_layout(
                            paper_bgcolor='rgba(0,0,0,0)',
                            plot_bgcolor='rgba(0,0,0,0)',
                            font=dict(color='#e0eaf5', family='JetBrains Mono'),
                            height=280,
                            showlegend=False,
                            margin=dict(t=20, b=20, l=20, r=20),
                            xaxis=dict(gridcolor='#1a2535'),
                            yaxis=dict(gridcolor='#1a2535')
                        )
                        st.plotly_chart(fig2, use_container_width=True)
        except Exception as e:
            st.error(f"Stats error: {e}")

    # ── SUMMARIES TAB
    with tab4:
        st.markdown('<div style="height:1rem"></div>', unsafe_allow_html=True)
        st.markdown('<div class="page-title" style="font-size:1.3rem">📊 Memory Summaries</div>', unsafe_allow_html=True)
        st.markdown('<div style="height:1.2rem"></div>', unsafe_allow_html=True)

        from summarizer import (
            generate_daily_summary,
            generate_weekly_summary,
            generate_monthly_summary
        )
        from memory_operations import (
            get_latest_daily_summary,
            get_latest_weekly_summary,
            get_latest_monthly_summary
        )

        daily_summary = get_latest_daily_summary(st.session_state.current_user)
        weekly_summary = get_latest_weekly_summary(st.session_state.current_user)
        monthly_summary = get_latest_monthly_summary(st.session_state.current_user)

        col1, col2, col3 = st.columns(3, gap="medium")

        with col1:
            st.markdown("### 📅 Daily Summary")
            if st.button("Generate Daily Summary", key="btn_daily_sum", use_container_width=True):
                with st.spinner("Analyzing and summarizing last 24h..."):
                    res = generate_daily_summary(st.session_state.current_user)
                    st.success("Daily summary generated!")
                    st.rerun()

            st.markdown('<div style="height:0.5rem"></div>', unsafe_allow_html=True)
            if daily_summary:
                st.markdown(f'<div class="memory-card"><div class="content">{daily_summary}</div></div>', unsafe_allow_html=True)
            else:
                st.info("No daily summary generated yet. Click generate above.")

        with col2:
            st.markdown("### 🗓️ Weekly Summary")
            if st.button("Generate Weekly Summary", key="btn_weekly_sum", use_container_width=True):
                with st.spinner("Analyzing and summarizing last 7 days..."):
                    res = generate_weekly_summary(st.session_state.current_user)
                    st.success("Weekly summary generated!")
                    st.rerun()

            st.markdown('<div style="height:0.5rem"></div>', unsafe_allow_html=True)
            if weekly_summary:
                st.markdown(f'<div class="memory-card"><div class="content">{weekly_summary}</div></div>', unsafe_allow_html=True)
            else:
                st.info("No weekly summary generated yet. Click generate above.")

        with col3:
            st.markdown("### 🗓️ Monthly Summary")
            if st.button("Generate Monthly Summary", key="btn_monthly_sum", use_container_width=True):
                with st.spinner("Analyzing and summarizing last 30 days..."):
                    res = generate_monthly_summary(st.session_state.current_user)
                    st.success("Monthly summary generated!")
                    st.rerun()

            st.markdown('<div style="height:0.5rem"></div>', unsafe_allow_html=True)
            if monthly_summary:
                st.markdown(f'<div class="memory-card"><div class="content">{monthly_summary}</div></div>', unsafe_allow_html=True)
            else:
                st.info("No monthly summary generated yet. Click generate above.")