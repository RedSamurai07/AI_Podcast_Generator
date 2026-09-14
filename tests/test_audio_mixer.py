import os
import sqlite3
import pytest
from pydub import AudioSegment
from src import audio_mixer, config

def test_mix_and_persist_podcast(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    test_db = str(tmp_path / "test_podcast.db")
    monkeypatch.setattr(config, "DB_PATH", test_db)
    monkeypatch.setattr(audio_mixer, "DB_PATH", test_db)
    
    config.init_db()
    
    # Generate temporary audio stems
    os.makedirs("temp", exist_ok=True)
    file1 = "temp/line_000_HostA.mp3"
    file2 = "temp/line_001_HostB.mp3"
    AudioSegment.silent(duration=1000).export(file1, format="mp3")
    AudioSegment.silent(duration=1000).export(file2, format="mp3")
    
    script = [
        {"speaker": "Host A", "text": "Testing line 1"},
        {"speaker": "Host B", "text": "Testing line 2"}
    ]
    
    output_path = audio_mixer.mix_and_persist_podcast.invoke({
        "topic": "UnitTest Topic",
        "research": "UnitTest Research Summary",
        "script": script,
        "audio_files": [file1, file2]
    })
    
    assert os.path.exists(output_path)
    assert os.path.getsize(output_path) > 0
    
    # Check database persistence
    conn = sqlite3.connect(test_db)
    cur = conn.cursor()
    cur.execute("SELECT id, topic, research FROM episodes WHERE topic=?", ("UnitTest Topic",))
    row = cur.fetchone()
    assert row is not None
    assert row[1] == "UnitTest Topic"
    assert row[2] == "UnitTest Research Summary"
    
    cur.execute("SELECT speaker, line_text FROM episode_dialogue WHERE episode_id=?", (row[0],))
    turns = cur.fetchall()
    assert len(turns) == 2
    assert turns[0][0] == "Host A"
    assert turns[0][1] == "Testing line 1"
    conn.close()
