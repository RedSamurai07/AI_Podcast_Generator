from typing import TypedDict, List, Dict, Any
import time
from langgraph.graph import StateGraph, START, END
from src.researcher import research_topic
from src.scriptwriter import write_script
from src.voice_generator import generate_voice_tracks
from src.audio_mixer import mix_and_persist_podcast
from src.telemetry import TelemetryTracker

# Global telemetry tracker instance per workflow run
pipeline_telemetry = TelemetryTracker()

# Graph State
class PodcastState(TypedDict):
    topic: str
    past_memory: str
    research_summary: str
    hosts: Dict[str, dict]
    script: List[dict]
    audio_files: List[str]
    final_podcast_path: str
    telemetry_summary: Dict[str, Any]

# LangGraph Nodes
def research_node(state: PodcastState) -> dict:
    with pipeline_telemetry.trace_node("Research"):
        data = research_topic.invoke({"topic": state["topic"]})
    return {
        "past_memory": data["past_memory"],
        "research_summary": data["research_summary"],
        "telemetry_summary": pipeline_telemetry.get_summary()
    }

def script_node(state: PodcastState) -> dict:
    with pipeline_telemetry.trace_node("Scriptwriting"):
        script_data = write_script.invoke({
            "topic": state["topic"],
            "memory_summary": state["past_memory"],
            "reserach_memory": state["research_summary"]
        })
    
    # Estimate token usage heuristics based on script text length
    dialogue_list = script_data.get("dialogue", []) if isinstance(script_data, dict) else script_data
    total_words = sum(len(turn.get("text", "").split()) for turn in dialogue_list) if dialogue_list else 100
    est_prompt_tokens = 600
    est_completion_tokens = int(total_words * 1.3)
    pipeline_telemetry.log_llm_usage(est_prompt_tokens, est_completion_tokens)
    
    if isinstance(script_data, dict):
        return {
            "hosts": script_data.get("hosts", {}),
            "script": script_data.get("dialogue", []),
            "telemetry_summary": pipeline_telemetry.get_summary()
        }
    return {
        "hosts": {},
        "script": script_data,
        "telemetry_summary": pipeline_telemetry.get_summary()
    }

def voice_node(state: PodcastState) -> dict:
    start_time = time.perf_counter()
    with pipeline_telemetry.trace_node("Voice Generation"):
        audio_paths = generate_voice_tracks.invoke({"script": state["script"]})
    tts_duration = time.perf_counter() - start_time
    
    # Estimate total audio duration (approx 4 seconds per dialogue turn)
    estimated_audio_sec = len(state.get("script", [])) * 4.0
    pipeline_telemetry.log_audio_stats(tts_duration, max(estimated_audio_sec, 1.0))
    
    return {
        "audio_files": audio_paths,
        "telemetry_summary": pipeline_telemetry.get_summary()
    }

def mix_node(state: PodcastState) -> dict:
    with pipeline_telemetry.trace_node("Audio Mixing"):
        final_path = mix_and_persist_podcast.invoke({
            "topic": state["topic"],
            "research": state["research_summary"],
            "script": state["script"],
            "audio_files": state["audio_files"]
        })
    return {
        "final_podcast_path": final_path,
        "telemetry_summary": pipeline_telemetry.get_summary()
    }

# Graph Workflow Definition
workflow = StateGraph(PodcastState)

workflow.add_node("research", research_node)
workflow.add_node("scriptwriting", script_node)
workflow.add_node("voice_generation", voice_node)
workflow.add_node("audio_mixing", mix_node)

workflow.add_edge(START, "research")
workflow.add_edge("research", "scriptwriting")
workflow.add_edge("scriptwriting", "voice_generation")
workflow.add_edge("voice_generation", "audio_mixing")
workflow.add_edge("audio_mixing", END)

app = workflow.compile()

# Execution Entry Point
if __name__ == "__main__":
    topic_input = input("Enter podcast topic: ")
    initial_state: PodcastState = {
        "topic": topic_input,
        "past_memory": "",
        "research_summary": "",
        "hosts": {},
        "script": [],
        "audio_files": [],
        "final_podcast_path": "",
        "telemetry_summary": {}
    }

    print("\n--- Starting Podcast Pipeline ---")
    for output in app.stream(initial_state):
        node_name = list(output.keys())[0]
        print(f"--> Finished Node: {node_name}")

    summary = pipeline_telemetry.get_summary()
    print("\n--- System Telemetry & Performance Summary ---")
    print(f"Total Pipeline Latency: {summary['total_latency_sec']}s")
    print(f"Real-Time Factor (RTF): {summary['real_time_factor']}x")
    print(f"Total Tokens Used: {summary['total_tokens']}")
    print(f"Estimated Cost: ${summary['estimated_cost_usd']:.5f}")
    print(f"Node Latencies: {summary['node_latencies']}")
    print("\nSuccess! Output file generated at output/final_podcast.mp3")