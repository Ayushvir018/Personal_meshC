import os
import streamlit as st
from dotenv import load_dotenv
import sqlite3

# Import the centralized client getter from rag
from rag import get_groq_client

MODEL = "llama-3.1-8b-instant"


def get_recent_memories(user_id, limit=3):
    """Fetch the last N memories from SQLite for a user."""
    try:
        conn = sqlite3.connect("memories.db")
        cursor = conn.cursor()
        cursor.execute(
            "SELECT content, timestamp FROM memories WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?",
            (user_id, limit)
        )
        rows = cursor.fetchall()
        conn.close()
        return rows  # List of (content, timestamp) tuples
    except Exception:
        return []


def generate_greeting(user_name, memories, llm_client=None):
    """
    Generate a short, friendly greeting that references the user's recent memories.
    Tone: casual, warm, slightly playful (cat-like 🐾).
    """
    _client = llm_client or get_groq_client()

    # Build memory context
    if memories:
        mem_lines = "\n".join([f"- {m[0]}" for m in memories[:3]])
        memory_context = f"User's recent memories:\n{mem_lines}"
    else:
        memory_context = "User has no memories saved yet — they are new here."

    prompt = f"""You are a friendly AI companion with a warm, slightly playful cat-like personality 🐾.
Generate a SHORT greeting (1-2 sentences max) for the user named "{user_name}".

{memory_context}

Rules:
- Keep it casual and warm, like a friend who remembers your life
- If memories exist, subtly reference the most recent one
- Use Hinglish naturally (mix of Hindi + English) — like how young Indians talk
- Add ONE relevant emoji max
- Do NOT be childish or cringy
- Do NOT use formal language
- Do NOT exceed 2 sentences
- Do NOT start with "Hey there!" or generic greetings — be creative

Example tone:
"Hey Ayush 👋 kal tum hackathon pe kaam kar rahe the… aaj kya scene hai?"
"Arrey {user_name}! Last time tumne health ke baare mein bataya tha, sab theek?"

Generate ONLY the greeting, nothing else."""

    try:
        response = _client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=80,
            temperature=0.9
        )
        return response.choices[0].message.content.strip()
    except Exception:
        # Fallback greeting if LLM fails
        return f"Hey {user_name} 👋 wapas aa gaye! Kya scene hai aaj?"


def companion_response(user_input, system_response, user_name, intent, llm_client=None):
    """
    Wraps the system's raw response into a friendly, conversational tone.
    Adds engagement hooks based on intent.
    """
    _client = llm_client or get_groq_client()

    # Determine engagement hook based on intent
    if intent == "SAVE" or intent == "memory":
        engagement_hint = 'End with a casual engagement hook like "Aur batao… aur kya hua aaj?" or similar.'
    elif intent == "QUERY" or intent == "question":
        engagement_hint = 'End with a casual engagement hook like "Aur kuch yaad karna hai kya?" or similar.'
    else:
        engagement_hint = 'End with a light, casual follow-up question.'

    prompt = f"""You are a friendly AI companion with a warm, slightly playful personality 🐾.

The user "{user_name}" sent: "{user_input}"
The system generated this response: "{system_response}"

Your job: Rewrite the system response in a friendly, conversational tone.

Rules:
- Core info remains intact, but NEVER say things like "Memory saved", "Information stored", "Note kar liya", "Yaad rahega", or "Dhyan mein rakha hai".
- Respond to the content of the user's message naturally, like a friend would. Acknowledge what they said by reacting to the information itself (e.g., "Achha!", "Sahi hai", or a relevant follow-up), but do NOT mention the act of saving or storing.
- Make it sound natural and friendly, like talking to a close friend
- Use Hinglish naturally (Hindi + English mix) where it feels right
- Keep it concise — NO long paragraphs
- {engagement_hint}
- Do NOT add information that wasn't in the original response
- Do NOT be childish or overly cute
- Do NOT use more than 2 emojis total
- Address the user by name naturally (not every sentence)

Generate ONLY the rewritten response, nothing else."""

    try:
        response = _client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.8
        )
        return response.choices[0].message.content.strip()
    except Exception:
        # Fallback: return the original response with a simple hook
        # Strip "User shared: " if it exists to keep it cleaner
        display_res = system_response
        if display_res.startswith("User shared: "):
            display_res = display_res.replace("User shared: ", "", 1)
            
        if intent in ("SAVE", "memory"):
            return f"{display_res}\n\nAur batao… aur kya hua aaj? 🐾"
        elif intent in ("QUERY", "question"):
            return f"{display_res}\n\nAur kuch yaad karna hai kya? 🐾"
        return display_res
