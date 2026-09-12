import sqlite3
from openai import OpenAI
from langchain_core.tools import tool
from src.config import api_key, DB_PATH, init_db


def fetch_past_episodes(limit: int = 5) -> str:
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT id, topic, created_at FROM episodes ORDER BY id DESC LIMIT ?", (limit,))
    rows = cur.fetchall()
    conn.close()

    if not rows:
        return "No prior episodes. This is Episode 1."
    return "Past recorded episodes:\n" + "\n".join(
        [f"- Episode {r[0]}: '{r[1]}' (Recorded: {r[2]})" for r in rows]
    )

@tool
def research_topic(topic: str) -> dict:
    """Fetches past episode memory from DB and conducts live web research."""
    print(f"[*] Researching '{topic}'.")
    memory_summary = fetch_past_episodes()

    client = OpenAI(api_key=api_key, base_url = "https://openrouter.ai/api/v1")
    prompt = f"Search and summarize essential facts, context, and key debate angles about: {topic}."

    try:
        response = client.chat.completions.create(
            model="nvidia/nemotron-3-ultra-550b-a55b:free",
            messages=[{"role": "user", "content": prompt}],
        )
        research = response.choices[0].message.content
    except Exception as e:
        research = f"Fallback research context (error: {e})"

    return {
        "past_memory": memory_summary,
        "research_summary": research
    }