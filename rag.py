import os
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI
from embedding import search_similar
import sqlite3
from memory_operations import add_memory

# Load environment variables
load_dotenv()

@st.cache_resource
def get_groq_client():
    """
    Returns a cached Groq client initialized with the API key from environment variables.
    Using @st.cache_resource ensures the client is not re-initialized on every run.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not found in environment variables. Please check your .env file.")
    
    return OpenAI(
        base_url="https://api.groq.com/openai/v1",
        api_key=api_key
    )

def ask_personal_mesh(question, user_id="ayush"):
    client = get_groq_client()
    # Step 1: Semantic search
    results = search_similar(question, n_results=5, user_id=user_id)
    memories = results['documents'][0]
    
    # Step 2: Fetch user-specific memories from SQLite
    conn = sqlite3.connect("memories.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT content FROM memories WHERE user_id = ?",
        (user_id,)
    )
    user_rows = cursor.fetchall()
    conn.close()
    
    user_memories = [row[0] for row in user_rows]
    
    # Step 3: Combine both
    all_memories = list(set(memories + user_memories))
    
    # Step 4: Build context
    context = "\n".join([f"- {mem}" for mem in all_memories])
    
    # Step 5: Ask Groq
    prompt = f"""You are a highly empathetic, emotionally intelligent, and supportive close friend-like AI companion for {user_id}.
You speak in a very natural, casual Hinglish (a mix of realistic Hindi and English, like young urban Indians text).

{user_id}'s personal memories:
{context if context.strip() else "No personal memories saved yet for this user."}

HOW TO RESPOND:
1. EMOTIONAL INTELLIGENCE: Always analyze the user's emotional state. If they sound sad, depressed, or heartbroken, be extremely sympathetic, comforting, and gentle. Match their mood.
2. If the query asks about {user_id} personally (their life, past, plans, etc.) → answer ONLY using the memories above. If you don't know, say so naturally without being robotic.
3. If it is a general knowledge question or sharing feelings → answer helpfully and supportively. Offer comfort if they are hurting.
4. NEVER invent personal details about {user_id}.
5. Talk like a real, caring friend. Do NOT use fake, cringy, or robotic phrases. NEVER use patronizing words like "beta" or "bhaiya". Ensure perfectly natural Hinglish grammar.
6. Keep your answer concise, empathetic, and human-like. Do NOT ask too many follow-up questions. Maximum one gentle follow-up question if it genuinely makes sense.
7. Use emojis carefully to match the emotional tone (e.g., 🫂 or ❤️ if they are sad, no playful emojis).

Question: {question}"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=300,
        temperature=0.7
    )
    
    return response.choices[0].message.content

def process_input(user_input, user_id):
    client = get_groq_client()
    from companion import companion_response
    
    # Step 1 — Classify karo
    classify_prompt = f"""Classify this input as either 'memory' or 'question'.

Input: "{user_input}"

Rules:
- If user is sharing information about themselves → 'memory'
- If user is asking something → 'question'

Reply with ONLY one word: memory OR question"""

    classify_response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": classify_prompt}],
        max_tokens=5,
        temperature=0
    )
    
    intent = classify_response.choices[0].message.content.strip().lower()
    
    # Step 2 — Act accordingly
    if "memory" in intent:
        # Save as memory using the existing add_memory function
        add_memory(user_input, user_id, "personal", "medium")
        # Just pass the user input to companion_response to generate a conversational acknowledgment
        final_response = companion_response(user_input, "", user_id, "memory")
        return "memory", final_response
    
    else:
        # For questions, ask_personal_mesh already returns a highly conversational and context-aware answer
        final_response = ask_personal_mesh(user_input, user_id)
        return "question", final_response