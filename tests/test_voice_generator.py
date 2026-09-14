import os
import pytest
from src import voice_generator

def test_generate_voice_tracks_fallback(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(voice_generator, "labs_key", "")
    
    script = [
        {"speaker": "Host A", "text": "Hello world from Host A"},
        {"speaker": "Host B", "text": "Hello world from Host B"},
        {"speaker": "Host C", "text": "Hello world from Host C"}
    ]
    
    audio_files = voice_generator.generate_voice_tracks.invoke({"script": script})
    
    assert len(audio_files) == 3
    for file_path in audio_files:
        assert os.path.exists(file_path)
        assert os.path.getsize(file_path) > 0
