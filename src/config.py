import os
import sqlite3
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
# Model API details
api_key = os.getenv("API_KEY")

# Eleven Labs API details
labs_key = os.getenv("LABS_API_KEY")

# ElevenLabs Voice IDs
voice_a = "EXAVITQu4vr4xnSDxMaL"  # Host A (Female, confident, energetic main host - Bella)
voice_b = "IKne3meq5aSn9XLyUdCD"  # Host B (Male, young, enthusiastic, witty banter - Charlie)
voice_c = "JBFqnCBsd6RMkjVDRZzb"  # Host C (Male, older, grounded, seasoned depth - George)


# Speaker Mapping
VOICE_MAP = {
    "Host A":voice_a,
    "Host B":voice_b,
    "Host C":voice_c,
}

# Anchor DB path to project root
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = str(BASE_DIR / "podcast_memory.db")
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS episodes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic TEXT NOT NULL,
            created_at TEXT NOT NULL,
            research TEXT,
            output_audio_path TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS episode_dialogue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            episode_id INTEGER,
            turn_index INTEGER,
            speaker TEXT,
            line_text TEXT,
            FOREIGN KEY (episode_id) REFERENCES episodes (id)
        )
    """)
    conn.commit()
    conn.close()

init_db()