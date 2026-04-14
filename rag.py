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
    prompt = f"""You are a friendly personal AI assistant and companion for {user_id}.
You speak in a warm, casual Hinglish style (mix of Hindi + English).

{user_id}'s personal memories:
{context if context.strip() else "No personal memories saved yet for this user."}

HOW TO RESPOND:
1. If the question is about {user_id} personally (their life, plans, habits, etc.) → answer ONLY from the memories above. If no relevant memory exists, say so naturally.
2. If the question is a general knowledge question (about a celebrity, place, fact, current events, etc.) → answer from your own knowledge freely and helpfully.
3. NEVER make up personal details about {user_id} that are not in their memories.
4. Keep answers concise and friendly.

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
        raw_response = f"User shared: {user_input}"
        # Wrap with companion personality
        final_response = companion_response(user_input, raw_response, user_id, "memory")
        return "memory", final_response
    
    else:
        # Answer the question
        raw_answer = ask_personal_mesh(user_input, user_id)
        # Wrap with companion personality
        final_response = companion_response(user_input, raw_answer, user_id, "question")
        return "question", final_response