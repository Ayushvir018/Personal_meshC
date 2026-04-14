import sqlite3
from datetime import datetime
from embedding import add_embedding

def add_memory(content, user_id="ayush", mem_type="personal", priority="medium", date=None, tags=""):
    conn = sqlite3.connect("memories.db")
    cursor = conn.cursor()
    
    if date:
        cursor.execute(
            "INSERT INTO memories (content, timestamp, user_id, type, priority, tags) VALUES (?, ?, ?, ?, ?, ?)",
            (content, date, user_id, mem_type, priority, tags)
        )
    else:
        cursor.execute(
            "INSERT INTO memories (content, user_id, type, priority, tags) VALUES (?, ?, ?, ?, ?)",
            (content, user_id, mem_type, priority, tags)
        )
    memory_id = cursor.lastrowid
    add_embedding(memory_id, content, user_id)
    
    conn.commit()
    conn.close()
    return "✅ Memory saved successfully!"


def get_all_memories(user_id="ayush"):
    conn = sqlite3.connect("memories.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM memories WHERE user_id = ? ORDER BY timestamp DESC",
        (user_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    return rows


def filter_by_type(mem_type, user_id="ayush"):
    conn = sqlite3.connect("memories.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM memories WHERE type = ? AND user_id = ? ORDER BY timestamp DESC",
        (mem_type, user_id)
    )
    rows = cursor.fetchall()
    conn.close()
    return rows


def search_memory(keyword, user_id="ayush"):
    conn = sqlite3.connect("memories.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM memories WHERE content LIKE ? AND user_id = ? ORDER BY timestamp DESC",
        ('%' + keyword + '%', user_id)
    )
    rows = cursor.fetchall()
    conn.close()
    return rows


def filter_by_date(date, user_id="ayush"):
    conn = sqlite3.connect("memories.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM memories WHERE DATE(timestamp) = ? AND user_id = ? ORDER BY timestamp DESC",
        (date, user_id)
    )
    rows = cursor.fetchall()
    conn.close()
    return rows


def delete_memory(memory_id):
    try:
        conn = sqlite3.connect("memories.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM memories WHERE id = ?", (int(memory_id),))
        conn.commit()
        conn.close()
        return "✅ Memory deleted successfully!"
    except:
        return "❌ Error: Invalid ID"


def edit_memory(memory_id, new_content):
    try:
        conn = sqlite3.connect("memories.db")
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE memories SET content = ? WHERE id = ?",
            (new_content, int(memory_id))
        )
        conn.commit()
        conn.close()
        return "✅ Memory updated successfully!"
    except:
        return "❌ Error: Invalid ID"
def get_stats(user_id="ayush"):
    conn = sqlite3.connect("memories.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM memories WHERE user_id = ?", (user_id,))
    total = cursor.fetchone()[0]
    
    cursor.execute(
        "SELECT type, COUNT(*) FROM memories WHERE user_id = ? GROUP BY type",
        (user_id,)
    )
    by_type = cursor.fetchall()
    
    cursor.execute(
        "SELECT priority, COUNT(*) FROM memories WHERE user_id = ? GROUP BY priority",
        (user_id,)
    )
    by_priority = cursor.fetchall()
    
    cursor.execute("""
        SELECT DATE(timestamp), COUNT(*) 
        FROM memories 
        WHERE user_id = ? AND DATE(timestamp) >= DATE('now', '-7 days')
        GROUP BY DATE(timestamp)
        ORDER BY DATE(timestamp)
    """, (user_id,))
    recent = cursor.fetchall()
    
    conn.close()
    
    return {
        'total': total,
        'by_type': by_type,
        'by_priority': by_priority,
        'recent': recent
    }
def smart_search(query, user_id):
    """
    Search memories intelligently using multiple strategies for a specific user
    """
    conn = sqlite3.connect("memories.db")
    cursor = conn.cursor()
    
    # Strategy 1: Keyword search in content
    cursor.execute(
        "SELECT * FROM memories WHERE content LIKE ? AND user_id = ? ORDER BY timestamp DESC LIMIT 10",
        ('%' + query + '%', user_id)
    )
    keyword_results = cursor.fetchall()
    
    # Strategy 2: Search in tags
    cursor.execute(
        "SELECT * FROM memories WHERE tags LIKE ? AND user_id = ? ORDER BY timestamp DESC LIMIT 10",
        ('%' + query + '%', user_id)
    )
    tag_results = cursor.fetchall()
    
    conn.close()
    
    # Combine and deduplicate
    all_results = list(keyword_results) + list(tag_results)
    seen_ids = set()
    unique_results = []
    
    for mem in all_results:
        if mem[0] not in seen_ids:
            seen_ids.add(mem[0])
            unique_results.append(mem)
            
    # Provide fallback if no unique results found
    if not unique_results:
        # We need a new connection since the previous one was closed
        conn = sqlite3.connect("memories.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM memories WHERE user_id = ? ORDER BY timestamp DESC LIMIT 20", (user_id,))
        fallback_results = cursor.fetchall()
        conn.close()
        return fallback_results
    
    return unique_results[:20]  # Return top 20 instead of 10 for better context


def search_by_tag(tag, user_id):
    """Search memories by tag for a specific user"""
    conn = sqlite3.connect("memories.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM memories WHERE tags LIKE ? AND user_id = ? ORDER BY timestamp DESC",
        ('%' + tag + '%', user_id)
    )
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_all_tags(user_id):
    """Get all unique tags for a specific user"""
    conn = sqlite3.connect("memories.db")
    cursor = conn.cursor()
    cursor.execute("SELECT tags FROM memories WHERE user_id = ? AND tags != ''", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    
    # Extract unique tags
    all_tags = []
    for row in rows:
        if row[0]:
            tags = [t.strip() for t in row[0].split(',')]
            all_tags.extend(tags)
    
    return list(set(all_tags))  # unique tags only