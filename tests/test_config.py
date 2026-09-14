import os
import sqlite3
import pytest
from src import config

def test_voice_map_configuration():
    assert "Host A" in config.VOICE_MAP
    assert "Host B" in config.VOICE_MAP
    assert "Host C" in config.VOICE_MAP
    assert config.VOICE_MAP["Host A"] == config.voice_a
    assert config.VOICE_MAP["Host B"] == config.voice_b
    assert config.VOICE_MAP["Host C"] == config.voice_c

def test_database_initialization(tmp_path, monkeypatch):
    test_db = str(tmp_path / "test_podcast.db")
    monkeypatch.setattr(config, "DB_PATH", test_db)
    
    config.init_db()
    assert os.path.exists(test_db)
    
    conn = sqlite3.connect(test_db)
    cur = conn.cursor()
    
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='episodes';")
    assert cur.fetchone() is not None
    
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='episode_dialogue';")
    assert cur.fetchone() is not None
    
    conn.close()
