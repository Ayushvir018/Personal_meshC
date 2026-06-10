import sqlite3
from datetime import datetime
from rag import get_groq_client

def generate_summary(user_id, period, days):
    """
    Generic function to retrieve memories for a period and generate a summary using Groq.
    Stores the result in the 'summaries' table.
    """
    conn = sqlite3.connect("memories.db")
    cursor = conn.cursor()
    
    # Query memories in range
    cursor.execute(
        f"SELECT content, type, priority, tags, timestamp FROM memories WHERE user_id = ? AND DATE(timestamp) >= DATE('now', '-{days} days') ORDER BY timestamp ASC",
        (user_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        return f"No memories found for the last {days} days to summarize."
        
    # Format memories context
    memory_lines = []
    for content, mem_type, priority, tags, timestamp in rows:
        tag_str = f", Tags: {tags}" if tags else ""
        memory_lines.append(f"[{timestamp}] (Type: {mem_type}, Priority: {priority}{tag_str}) {content}")
        
    context = "\n".join(memory_lines)
    
    client = get_groq_client()
    prompt = f"""You are a helpful AI memory assistant. Your goal is to generate a comprehensive, structured {period} summary of the user's memories.
Here are the memories from the past {days} days for user "{user_id}":

{context}

Please group and compress this information into a high-quality summary. Focus specifically on:
1. Projects worked on (mention project names and details)
2. Important achievements and progress
3. Goals discussed or planned
4. Frequently mentioned topics or themes
5. High-priority memories

Write a clean, easy-to-read summary. Format the summary using basic HTML tags (e.g., use <strong> for bolding, <ul> and <li> for lists, <p> for paragraphs). Do NOT use markdown. Make it concise but ensure no important detail is lost."""

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.3
        )
        summary_text = response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error generating summary: {str(e)}"
        
    # Store in database
    conn = sqlite3.connect("memories.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO summaries (user_id, period, summary) VALUES (?, ?, ?)",
        (user_id, period, summary_text)
    )
    conn.commit()
    conn.close()
    
    return summary_text

def generate_daily_summary(user_id):
    return generate_summary(user_id, "daily", 1)

def generate_weekly_summary(user_id):
    return generate_summary(user_id, "weekly", 7)

def generate_monthly_summary(user_id):
    return generate_summary(user_id, "monthly", 30)
