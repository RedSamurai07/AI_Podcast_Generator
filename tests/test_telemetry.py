import time
import pytest
from src.telemetry import TelemetryTracker

def test_telemetry_tracker_node_latency():
    tracker = TelemetryTracker()
    with tracker.trace_node("TestNode"):
        time.sleep(0.05)
        
    summary = tracker.get_summary()
    assert "TestNode" in summary["node_latencies"]
    assert summary["node_latencies"]["TestNode"] >= 0.04
    assert summary["total_latency_sec"] >= 0.04

def test_telemetry_llm_token_logging():
    tracker = TelemetryTracker()
    tracker.log_llm_usage(prompt_tokens=500, completion_tokens=300)
    
    summary = tracker.get_summary()
    assert summary["prompt_tokens"] == 500
    assert summary["completion_tokens"] == 300
    assert summary["total_tokens"] == 800
    assert summary["estimated_cost_usd"] > 0.0

def test_telemetry_audio_rtf_logging():
    tracker = TelemetryTracker()
    # 2 seconds to generate 10 seconds of audio -> RTF = 0.2
    tracker.log_audio_stats(tts_time_sec=2.0, total_audio_sec=10.0)
    
    summary = tracker.get_summary()
    assert summary["tts_latency_sec"] == 2.0
    assert summary["audio_duration_sec"] == 10.0
    assert summary["real_time_factor"] == 0.2

def test_telemetry_fallback_logging():
    tracker = TelemetryTracker()
    tracker.log_fallback()
    tracker.log_fallback()
    
    summary = tracker.get_summary()
    assert summary["fallbacks_triggered"] == 2
