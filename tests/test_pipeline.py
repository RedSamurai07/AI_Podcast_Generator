import os
import json
import pytest
from unittest.mock import patch, MagicMock
from main import app as graph_app, PodcastState

@patch("src.researcher.OpenAI")
@patch("src.scriptwriter.OpenAI")
def test_full_pipeline_stream(mock_script_openai, mock_res_openai, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    
    # Mock research OpenAI response
    mock_res_client = MagicMock()
    mock_res_openai.return_value = mock_res_client
    mock_res_resp = MagicMock()
    mock_res_resp.choices = [MagicMock(message=MagicMock(content="Synthetic research context"))]
    mock_res_client.chat.completions.create.return_value = mock_res_resp
    
    # Mock script OpenAI response
    mock_script_client = MagicMock()
    mock_script_openai.return_value = mock_script_client
    mock_script_resp = MagicMock()
    mock_script_json = {
        "hosts": {
            "Host A": {"name": "Maya", "role": "Anchor"},
            "Host B": {"name": "Liam", "role": "Analyst"},
            "Host C": {"name": "Julian", "role": "Specialist"}
        },
        "dialogue": [
            {"speaker": "Host A", "text": "Turn 1 line content"},
            {"speaker": "Host B", "text": "Turn 2 line content"},
            {"speaker": "Host C", "text": "Turn 3 line content"},
            {"speaker": "Host A", "text": "Turn 4 line content"},
            {"speaker": "Host B", "text": "Turn 5 line content"},
            {"speaker": "Host C", "text": "Turn 6 line content"}
        ]
    }
    mock_script_resp.choices = [MagicMock(message=MagicMock(content=json.dumps(mock_script_json)))]
    mock_script_client.chat.completions.create.return_value = mock_script_resp

    initial_state: PodcastState = {
        "topic": "Future of AI",
        "past_memory": "",
        "research_summary": "",
        "hosts": {},
        "script": [],
        "audio_files": [],
        "final_podcast_path": ""
    }
    
    executed_nodes = []
    final_state = dict(initial_state)
    
    for step in graph_app.stream(initial_state):
        node_name = list(step.keys())[0]
        executed_nodes.append(node_name)
        final_state.update(step[node_name])
        
    assert "research" in executed_nodes
    assert "scriptwriting" in executed_nodes
    assert "voice_generation" in executed_nodes
    assert "audio_mixing" in executed_nodes
    assert os.path.exists(final_state["final_podcast_path"])
