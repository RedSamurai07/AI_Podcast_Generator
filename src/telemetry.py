import time
from contextlib import contextmanager
from typing import Dict, Any

class TelemetryTracker:
    """Tracks latency, token usage, audio RTF, and fallbacks across multi-agent executions."""
    
    def __init__(self):
        self.metrics: Dict[str, Any] = {
            "node_latencies": {},
            "total_latency_sec": 0.0,
            "total_tokens": 0,
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "estimated_cost_usd": 0.0,
            "audio_duration_sec": 0.0,
            "tts_latency_sec": 0.0,
            "real_time_factor": 0.0,
            "fallbacks_triggered": 0,
        }

    @contextmanager
    def trace_node(self, node_name: str):
        """Context manager to measure high-precision execution time of a pipeline node."""
        start_time = time.perf_counter()
        try:
            yield
        finally:
            elapsed = time.perf_counter() - start_time
            self.metrics["node_latencies"][node_name] = round(elapsed, 3)

    def log_llm_usage(self, prompt_tokens: int, completion_tokens: int, cost_per_1k_input: float = 0.0015, cost_per_1k_output: float = 0.002):
        """Logs LLM token counts and estimates API cost in USD."""
        self.metrics["prompt_tokens"] += prompt_tokens
        self.metrics["completion_tokens"] += completion_tokens
        self.metrics["total_tokens"] += (prompt_tokens + completion_tokens)
        cost = (prompt_tokens / 1000 * cost_per_1k_input) + (completion_tokens / 1000 * cost_per_1k_output)
        self.metrics["estimated_cost_usd"] = round(self.metrics["estimated_cost_usd"] + cost, 5)

    def log_audio_stats(self, tts_time_sec: float, total_audio_sec: float):
        """Logs TTS generation duration, total audio length, and calculates Real-Time Factor (RTF)."""
        self.metrics["tts_latency_sec"] = round(tts_time_sec, 3)
        self.metrics["audio_duration_sec"] = round(total_audio_sec, 3)
        if total_audio_sec > 0:
            self.metrics["real_time_factor"] = round(tts_time_sec / total_audio_sec, 3)

    def log_fallback(self):
        """Tracks when a safety fallback or graceful degradation is triggered."""
        self.metrics["fallbacks_triggered"] += 1

    def get_summary(self) -> Dict[str, Any]:
        """Returns a snapshot summary of all tracked metrics."""
        self.metrics["total_latency_sec"] = round(sum(self.metrics["node_latencies"].values()), 3)
        return self.metrics.copy()
