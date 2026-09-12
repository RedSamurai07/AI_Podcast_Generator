import os
import sqlite3
from datetime import datetime
from pydub import AudioSegment
from langchain_core.tools import tool
from src.config import DB_PATH

@tool
def mix_and_persist_podcast(topic: str, research: str, script: list[dict], audio_files: list[str]) -> str:
    """Stitches audio turns, ducks background music, exports final MP3, and saves record to SQLite."""
# Audio Setup & Dialogue Stitching
    print("[*] Mixing audio tracks with pydub...")
    os.makedirs("output", exist_ok=True)
    output_path = "output/final_podcast.mp3"
    bg_music_path = "assets/bg_music.mp3"

    combined = AudioSegment.empty()
    pause = AudioSegment.silent(duration=300)

    for file in audio_files:
        combined += AudioSegment.from_mp3(file) + pause

# Background Music Mixing
    if os.path.exists(bg_music_path):
        bg = AudioSegment.from_mp3(bg_music_path)
        while len(bg) < len(combined):
            bg += bg
        bg = bg[:len(combined)] - 15
        final_mix = combined.overlay(bg)
    else:
        final_mix = combined

    final_mix.export(output_path, format="mp3")

    # Stores episode to database memory
    print("Saving episode session to SQLite memory...")
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cur.execute(
        "INSERT INTO episodes (topic, created_at, research, output_audio_path) VALUES (?, ?, ?, ?)",
        (topic, now, research, output_path)
    )
    episode_id = cur.lastrowid
    for i, turn in enumerate(script):
        cur.execute(
            "INSERT INTO episode_dialogue (episode_id, turn_index, speaker, line_text) VALUES (?, ?, ?, ?)",
            (episode_id, i, turn.get("speaker"), turn.get("text"))
        )
    conn.commit()
    conn.close()
    print(f"[*] Episode {episode_id} saved to memory.")
    return output_path