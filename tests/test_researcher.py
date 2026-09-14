import sqlite3
import pytest
from unittest.mock import patch, MagicMock
from src import researcher, config

def test_fetch_past_episodes_empty(tmp_path, monkeypatch):
    test_db = str(tmp_path / "test_podcast.db")
    monkeypatch.setattr(config, "DB_PATH", test_db)
    monkeypatch.setattr(researcher, "DB_PATH", test_db)
    
    config.init_db()
    result = researcher.fetch_past_episodes()
    assert "No prior episodes. This is Episode 1." in result

def test_fetch_past_episodes_populated(tmp_path, monkeypatch):
    test_db = str(tmp_path / "test_podcast.db")
    monkeypatch.setattr(config, "DB_PATH", test_db)
    monkeypatch.setattr(researcher, "DB_PATH", test_db)
    
    config.init_db()
    conn = sqlite3.connect(test_db)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO episodes (topic, created_at, research, output_audio_path) VALUES (?, ?, ?, ?)",
        ("AI Agents", "2026-09-14 12:00:00", "Summary...", "output/test.mp3")
    )
    conn.commit()
    conn.close()
    
    result = researcher.fetch_past_episodes()
    assert "Past recorded episodes:" in result
    assert "AI Agents" in result

@patch("src.researcher.OpenAI")
def test_research_topic_tool(mock_openai, tmp_path, monkeypatch):
    test_db = str(tmp_path / "test_podcast.db")
    monkeypatch.setattr(config, "DB_PATH", test_db)
    monkeypatch.setattr(researcher, "DB_PATH", test_db)
    
    mock_client = MagicMock()
    mock_openai.return_value = mock_client
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="Synthetic research output for test topic"))]
    mock_client.chat.completions.create.return_value = mock_response
    
    output = researcher.research_topic.invoke({"topic": "Quantum Computing"})
    assert "past_memory" in output
    assert "research_summary" in output
    assert output["research_summary"] == "Synthetic research output for test topic"
