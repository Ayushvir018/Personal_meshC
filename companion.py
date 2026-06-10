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
    Generates a friendly, conversational acknowledgment when the user shares a memory.
    Produces natural Hinglish so it feels like texting a real Indian friend.
    """
    _client = llm_client or get_groq_client()

    prompt = f"""You are a highly empathetic, emotionally intelligent, and supportive AI companion.
The user "{user_name}" just shared this with you: "{user_input}"

Your job: Respond to the user naturally, like a close, caring friend getting a text message.

Rules for your response:
1. MATCH THE USER'S MOOD: Analyze the emotional tone of their message (e.g., sad, happy, depressed, excited).
   - If they are sad, heartbroken, or depressed: Be extremely gentle, comforting, and sympathetic. NEVER be playful or use happy emojis. Offer emotional support.
   - If they are happy or casual: Be warm and match their energy.
2. NEVER use weird, robotic, or patronizing words like "beta", "Information stored", "Note kar liya".
3. Use natural conversational Hinglish (Hindi + English) — like how young urban Indians text realistically. Maintain perfect grammar.
4. Provide a natural, emotionally appropriate reaction depending on the context.
5. Keep it concise (1-2 sentences maximum).
6. Ask ONE gentle follow-up question ONLY if it feels naturally caring and appropriate. Don't be pushy.
7. Use ONE relevant emoji maximum, strictly matching the mood (e.g., 🫂, ❤️ for sad moods). Do not use playful emojis if they are sad.
8. Do NOT repeat what the user said. Directly address how they are feeling right now.

Generate ONLY the response, nothing else."""

    try:
        response = _client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
            temperature=0.8
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return f"Got it! Thanks for sharing, {user_name}. 🐾"

