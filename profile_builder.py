import sqlite3
import json
from datetime import datetime
from rag import get_groq_client

def build_profile(user_id):
    """
    Builds the user profile by querying recent memories and summaries,
    sending them to Groq to extract details with confidence scores,
    and saving/updating the result in the user_profiles table.
    """
    conn = sqlite3.connect("memories.db")
    cursor = conn.cursor()
    
    # 1. Fetch recent memories (last 20)
    cursor.execute(
        "SELECT content, timestamp FROM memories WHERE user_id = ? ORDER BY timestamp DESC LIMIT 20",
        (user_id,)
    )
    mem_rows = cursor.fetchall()
    
    # Get total memory count
    cursor.execute(
        "SELECT COUNT(*) FROM memories WHERE user_id = ?",
        (user_id,)
    )
    current_mem_count = cursor.fetchone()[0]
    
    # 2. Fetch recent summaries (weekly and monthly, limit to last 10)
    cursor.execute(
        "SELECT summary, period, created_at FROM summaries WHERE user_id = ? AND period IN ('weekly', 'monthly') ORDER BY created_at DESC LIMIT 10",
        (user_id,)
    )
    summary_rows = cursor.fetchall()
    conn.close()
    
    # If no memories at all, return empty profile structure
    if not mem_rows and not summary_rows:
        return None
        
    # Format context
    memories_str = "\n".join([f"[{ts}] {content}" for content, ts in mem_rows])
    summaries_str = "\n".join([f"[{created_at}] ({period}): {summary}" for summary, period, created_at in summary_rows])
    
    client = get_groq_client()
    prompt = f"""You are a structured data extraction AI. Your goal is to build a structured user profile based on the user's memories and activity summaries.
Here are the memories and summaries for user "{user_id}":

=== Recent Memories (last 20) ===
{memories_str if memories_str else "No recent memories."}

=== Recent Weekly/Monthly Summaries ===
{summaries_str if summaries_str else "No summaries."}

Extract the following fields from the data:
1. name (the user's full name if mentioned, otherwise default to "{user_id}")
2. main_projects (list of projects the user is working on or has built)
3. interests (list of hobbies, fields of interest, topics they care about)
4. hackathons (list of hackathons participated in or discussed)
5. team_members (list of collaborators, teammates, or friends mentioned working with them)
6. skills (list of technologies, programming languages, or expertise areas)
7. goals (list of goals they want to achieve or are working towards)
8. frequent_topics (list of terms, concepts, or topics they mention frequently)
9. learning_areas (list of topics they want to learn or are studying)

For all list fields (except "name"), you MUST output elements as objects containing the "name" of the entity and a "confidence" score (between 0.0 and 1.0) indicating how strongly the entity is supported by the user's memories/summaries.

You MUST respond with a valid JSON object and ONLY a valid JSON object. Do not include markdown formatting or explanation outside the JSON. Use the following structure exactly:
{{
    "name": "string",
    "main_projects": [{{"name": "string", "confidence": 0.95}}],
    "interests": [{{"name": "string", "confidence": 0.85}}],
    "hackathons": [{{"name": "string", "confidence": 0.90}}],
    "team_members": [{{"name": "string", "confidence": 0.80}}],
    "skills": [{{"name": "string", "confidence": 0.95}}],
    "goals": [{{"name": "string", "confidence": 0.90}}],
    "frequent_topics": [{{"name": "string", "confidence": 0.85}}],
    "learning_areas": [{{"name": "string", "confidence": 0.80}}]
}}
"""
    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=800,
            temperature=0.1
        )
        text = response.choices[0].message.content.strip()
        # Strip markdown code blocks if any
        if text.startswith("```"):
            lines = text.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines[-1].startswith("```"):
                lines = lines[:-1]
            text = "\n".join(lines).strip()
            
        profile_data = json.loads(text)
    except Exception as e:
        raise RuntimeError(f"Failed to generate structured profile JSON: {str(e)}")
        
    # Store inside user_profiles table
    conn = sqlite3.connect("memories.db")
    cursor = conn.cursor()
    
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        """
        INSERT OR REPLACE INTO user_profiles (user_id, profile_json, memory_count, last_rebuild_at, updated_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (user_id, json.dumps(profile_data), current_mem_count, now_str, now_str)
    )
    conn.commit()
    conn.close()
    return profile_data

def update_profile(user_id):
    """Rebuilds the profile."""
    return build_profile(user_id)

def get_profile(user_id):
    """
    Retrieves the user profile as a parsed dictionary.
    """
    conn = sqlite3.connect("memories.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT profile_json FROM user_profiles WHERE user_id = ?",
        (user_id,)
    )
    row = cursor.fetchone()
    conn.close()
    
    if row:
        try:
            return json.loads(row[0])
        except Exception:
            return None
    return None

def delete_profile(user_id):
    """Deletes the user profile."""
    conn = sqlite3.connect("memories.db")
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM user_profiles WHERE user_id = ?",
        (user_id,)
    )
    conn.commit()
    conn.close()

def check_and_trigger_profile_update(user_id):
    """
    Asynchronously checks if the difference in memory count triggers a profile update,
    and runs it in a background thread if so.
    """
    conn = sqlite3.connect("memories.db")
    cursor = conn.cursor()
    
    # 1. Fetch current memory count
    cursor.execute("SELECT COUNT(*) FROM memories WHERE user_id = ?", (user_id,))
    current_count = cursor.fetchone()[0]
    
    # 2. Fetch last built count from user_profiles table
    cursor.execute("SELECT memory_count FROM user_profiles WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    
    last_count = 0
    profile_exists = False
    if row:
        last_count = row[0]
        profile_exists = True
        
    # 3. Rebuild profile every 20 memories, or if the profile doesn't exist yet and we have memories.
    if not profile_exists or (current_count - last_count >= 20):
        import threading
        thread = threading.Thread(target=update_profile, args=(user_id,))
        thread.start()
