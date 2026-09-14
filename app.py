import os
import time
import json
import sqlite3
import streamlit as st
from main import app as graph_app
from src.config import DB_PATH

st.set_page_config(
    page_title="AI Podcast Studio",
    page_icon="🎙️",
    layout="wide"
)

# Avatar Mapping
HOST_AVATARS = {
    "Host A": "🎙️",
    "Host B": "⚡",
    "Host C": "📚"
}

st.markdown("""
<style>
    .host-card {
        padding: 1rem;
        border-radius: 10px;
        background-color: #1E1E24;
        border-left: 5px solid #4A90E2;
        margin-bottom: 0.8rem;
    }
    .chat-bubble {
        padding: 12px 18px;
        border-radius: 15px;
        margin-bottom: 10px;
        display: inline-block;
    }
</style>
""", unsafe_allow_html=True)

# Helper Functions
def get_recorded_episodes():
    """Fetches list of existing episodes from SQLite database."""
    if not os.path.exists(DB_PATH):
        return []
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    try:
        cur.execute("SELECT id, topic, created_at, output_audio_path FROM episodes ORDER BY id DESC")
        episodes = cur.fetchall()
    except sqlite3.OperationalError:
        episodes = []
    conn.close()
    return episodes

# Sidebar: Memory & Archive
with st.sidebar:
    st.header("🗄️ Studio Memory Archive")
    st.caption("Persistent show memory stored in SQLite")
    past_eps = get_recorded_episodes()
    
    if past_eps:
        for ep in past_eps:
            with st.expander(f"Ep {ep[0]}: {ep[1]}"):
                st.write(f"**Recorded:** {ep[2]}")
                if ep[3] and os.path.exists(ep[3]):
                    st.audio(ep[3], format="audio/mp3")
    else:
        st.info("No recorded episodes yet.")


# Main Studio Dashboard
st.title("🎙️ AI Live Podcast Generator")
st.caption("Multi-host conversational engine powered by OpenAI, OpenRouter, and ElevenLabs")

# Studio Hosts Dynamic Header Area
header_placeholder = st.container()

def display_hosts_header(hosts=None):
    if not hosts:
        hosts = {
            "Host A": {"name": "Host A", "role": "Anchor & Analytical"},
            "Host B": {"name": "Host B", "role": "Enthusiastic & Curious"},
            "Host C": {"name": "Host C", "role": "Seasoned & Grounded"}
        }
    with header_placeholder:
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            data = hosts.get("Host A", {})
            st.info(f"🎙️ **{data.get('name', 'Host A')}**\n\n{data.get('role', 'Anchor & Analytical')}")
        with col_b:
            data = hosts.get("Host B", {})
            st.warning(f"⚡ **{data.get('name', 'Host B')}**\n\n{data.get('role', 'Enthusiastic & Curious')}")
        with col_c:
            data = hosts.get("Host C", {})
            st.success(f"📚 **{data.get('name', 'Host C')}**\n\n{data.get('role', 'Seasoned & Grounded')}")

display_hosts_header()
st.divider()

# Episode Generation Form
with st.form("podcast_form"):
    topic = st.text_input("Enter a topic for the hosts to debate:", placeholder="e.g., The Future of Open-Source Foundation Models")
    submit_btn = st.form_submit_button("🚀 Record Live Episode", use_container_width=True)

if submit_btn and topic.strip():
    status_box = st.status("Initializing studio pipeline...", expanded=True)
    
    initial_state = {
        "topic": topic.strip(),
        "past_memory": "",
        "research_summary": "",
        "hosts": {},
        "script": [],
        "audio_files": [],
        "final_podcast_path": ""
    }

    # Graph Execution
    pipeline_state = initial_state
    for step_output in graph_app.stream(initial_state):
        node_name = list(step_output.keys())[0]
        node_data = step_output[node_name]
        pipeline_state.update(node_data)

        if node_name == "research":
            status_box.write("✅ Retrieved live facts and past memory context.")
        elif node_name == "scriptwriting":
            status_box.write("✅ Generated dynamic host personas and dialogue.")
            if pipeline_state.get("hosts"):
                display_hosts_header(pipeline_state["hosts"])
        elif node_name == "voice_generation":
            status_box.write("✅ Synthesized audio turns for all 3 hosts.")
        elif node_name == "audio_mixing":
            status_box.write("✅ Mixed voice stems with background track.")

    status_box.update(label="🎙️ Recording session complete!", state="complete", expanded=False)

    # Final Output Audio Player
    st.subheader("🎧 Final Produced Episode (Master Mix)")
    final_audio = pipeline_state.get("final_podcast_path", "output/final_podcast.mp3")
    if os.path.exists(final_audio):
        st.audio(final_audio, format="audio/mp3")
    st.divider()

    # Live Turn-by-Turn Studio Conversation
    st.subheader("💬 Live Studio Dialogue & Individual Audio Turns")
    
    script = pipeline_state.get("script", [])
    audio_files = pipeline_state.get("audio_files", [])
    hosts = pipeline_state.get("hosts", {})

    for i, turn in enumerate(script):
        speaker_key = turn.get("speaker", "Host A")
        avatar = HOST_AVATARS.get(speaker_key, "🎙️")
        
        # Pulls dynamic name directly, with no bracketed defaults
        host_info = hosts.get(speaker_key, {})
        display_name = host_info.get("name", speaker_key)
        
        with st.chat_message(name=display_name, avatar=avatar):
            st.markdown(f"**{display_name}**")
            st.write(turn.get("text", ""))
            
            # Line-by-line audio player
            if i < len(audio_files) and os.path.exists(audio_files[i]):
                st.audio(audio_files[i], format="audio/mp3")