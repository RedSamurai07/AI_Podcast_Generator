from typing import TypedDict, List, Dict
from langgraph.graph import StateGraph, START, END
from src.researcher import research_topic
from src.scriptwriter import write_script
from src.voice_generator import generate_voice_tracks
from src.audio_mixer import mix_and_persist_podcast

# Graph State
class PodcastState(TypedDict):
    topic: str
    past_memory: str
    research_summary: str
    hosts: Dict[str, dict]
    script: List[dict]
    audio_files: List[str]
    final_podcast_path: str

# LangGraph Nodes
def research_node(state: PodcastState) -> dict:
    data = research_topic.invoke({"topic": state["topic"]})
    return {
        "past_memory": data["past_memory"],
        "research_summary": data["research_summary"]
    }

def script_node(state: PodcastState) -> dict:
    script_data = write_script.invoke({
        "topic": state["topic"],
        "memory_summary": state["past_memory"],
        "reserach_memory": state["research_summary"]
    })
    
    # Handles both dict format {"hosts": ..., "dialogue": ...} and plain list
    if isinstance(script_data, dict):
        return {
            "hosts": script_data.get("hosts", {}),
            "script": script_data.get("dialogue", [])
        }
    return {
        "hosts": {},
        "script": script_data
    }

def voice_node(state: PodcastState) -> dict:
    audio_paths = generate_voice_tracks.invoke({"script": state["script"]})
    return {"audio_files": audio_paths}

def mix_node(state: PodcastState) -> dict:
    final_path = mix_and_persist_podcast.invoke({
        "topic": state["topic"],
        "research": state["research_summary"],
        "script": state["script"],
        "audio_files": state["audio_files"]
    })
    return {"final_podcast_path": final_path}

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
        "final_podcast_path": ""
    }

    print("\n--- Starting Podcast Pipeline ---")
    for output in app.stream(initial_state):
        node_name = list(output.keys())[0]
        print(f"--> Finished Node: {node_name}")

    print("\nSuccess! Output file generated at output/final_podcast.mp3")