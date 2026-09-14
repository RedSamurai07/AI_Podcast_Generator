import json
import os
import pytest
from unittest.mock import patch, MagicMock
from src import scriptwriter

@patch("src.scriptwriter.OpenAI")
def test_write_script_success(mock_openai, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    
    mock_client = MagicMock()
    mock_openai.return_value = mock_client
    
    mock_json = {
        "hosts": {
            "Host A": {"name": "Alice", "role": "Anchor"},
            "Host B": {"name": "Bob", "role": "Analyst"},
            "Host C": {"name": "Charlie", "role": "Specialist"}
        },
        "dialogue": [
            {"speaker": "Host A", "text": "Turn 1 line content here."},
            {"speaker": "Host B", "text": "Turn 2 line content here."},
            {"speaker": "Host C", "text": "Turn 3 line content here."},
            {"speaker": "Host A", "text": "Turn 4 line content here."},
            {"speaker": "Host B", "text": "Turn 5 line content here."},
            {"speaker": "Host C", "text": "Turn 6 line content here."}
        ]
    }
    
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content=json.dumps(mock_json)))]
    mock_client.chat.completions.create.return_value = mock_response
    
    result = scriptwriter.write_script.invoke({
        "topic": "Autonomous AI Systems",
        "memory_summary": "Prior Episode 1",
        "reserach_memory": "Research context details"
    })
    
    assert "hosts" in result
    assert "dialogue" in result
    assert len(result["dialogue"]) == 6
    assert os.path.exists("temp/script.json")

@patch("src.scriptwriter.OpenAI")
def test_write_script_fallback(mock_openai, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    
    mock_client = MagicMock()
    mock_openai.return_value = mock_client
    mock_client.chat.completions.create.side_effect = Exception("API rate limited")
    
    result = scriptwriter.write_script.invoke({
        "topic": "Fallback Topic",
        "memory_summary": "None",
        "reserach_memory": "None"
    })
    
    assert "hosts" in result
    assert "dialogue" in result
    assert len(result["dialogue"]) > 0
    assert result["hosts"]["Host A"]["name"] == "Maya"
