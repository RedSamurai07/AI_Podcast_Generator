import os
import time
import json
import streamlit as st
from supabase import create_client, Client
from main import app as graph_app

st.set_page_config(
    page_title="AI Podcast Studio",
    page_icon="🎙️",
    layout="wide"
)

# ----------------- SUPABASE CLIENT SETUP -----------------
def get_config_val(key: str) -> str:
    """Safely extracts credentials from Streamlit secrets or OS env, stripping quotes/spaces."""
    val = ""
    if hasattr(st, "secrets") and key in st.secrets:
        val = str(st.secrets[key])
    elif os.getenv(key):
        val = str(os.getenv(key))
    return val.strip().strip('"').strip("'")

SUPABASE_URL = get_config_val("SUPABASE_URL")
SUPABASE_KEY = get_config_val("SUPABASE_KEY")

supabase: Client = None
if SUPABASE_URL.startswith("http://") or SUPABASE_URL.startswith("https://"):
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        st.error(f"Failed to initialize Supabase client: {e}")
        st.stop()
else:
    st.error(f"⚠️ Invalid or missing SUPABASE_URL. Received: '{SUPABASE_URL}'")
    st.stop()

# ----------------- AUTHENTICATION & SESSION STATE -----------------
if "user" not in st.session_state:
    st.session_state.user = None

def login_user(email, password):
    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        st.session_state.user = res.user
        st.success("Signed in successfully!")
        st.rerun()
    except Exception as e:
        st.error(f"Login failed: {e}")

def signup_user(email, password):
    try:
        res = supabase.auth.sign_up({"email": email, "password": password})
        if res.user:
            st.session_state.user = res.user
            st.success("Account created successfully! Logging you in...")
            st.rerun()
    except Exception as e:
        st.error(f"Registration failed: {e}")

def logout_user():
    try:
        supabase.auth.sign_out()
    except Exception:
        pass
    st.session_state.user = None
    st.rerun()

# ----------------- AUTH GATEWAY VIEW -----------------
if not st.session_state.user:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("🎙️ AI Live Podcast Generator")
        st.caption("Sign in or create an account to start generating studio-grade podcasts.")
        
        tab_login, tab_signup = st.tabs(["🔑 Log In", "📝 Create Account"])
        
        with tab_login:
            with st.form("login_form"):
                email = st.text_input("Email / Username", placeholder="recruiter@company.com")
                password = st.text_input("Password", type="password")
                submit_login = st.form_submit_button("Sign In", use_container_width=True)
                if submit_login:
                    if email and password:
                        login_user(email.strip(), password)
                    else:
                        st.warning("Please enter both email and password.")

        with tab_signup:
            with st.form("signup_form"):
                new_email = st.text_input("Email", placeholder="name@domain.com")
                new_password = st.text_input("Choose Password (min 6 characters)", type="password")
                submit_signup = st.form_submit_button("Create Account", use_container_width=True)
                if submit_signup:
                    if len(new_password) < 6:
                        st.error("Password must be at least 6 characters.")
                    elif new_email and new_password:
                        signup_user(new_email.strip(), new_password)
                    else:
                        st.warning("Please fill in all fields.")
    st.stop()  # Halt execution until authenticated

# =========================================================
# THE STUDIO UI BELOW ONLY RUNS FOR LOGGED-IN USERS
# =========================================================

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

# ----------------- SUPABASE DATA HELPERS -----------------
def get_recorded_episodes():
    """Fetches user-specific podcast episodes from Supabase."""
    if not supabase or not st.session_state.user:
        return []
    try:
        response = (
            supabase.table("podcast_history")
            .select("id, topic, created_at, audio_url")
            .eq("user_id", st.session_state.user.id)
            .order("created_at", desc=True)
            .execute()
        )
        return response.data or []
    except Exception as e:
        st.sidebar.error(f"Error fetching archives: {e}")
        return []

def upload_to_supabase_storage(local_path: str, bucket_name: str = "podcast-audio") -> str:
    """Uploads the final audio to Supabase Storage and returns a public URL."""
    if not supabase or not os.path.exists(local_path):
        return ""
    
    file_name = f"{st.session_state.user.id}_{int(time.time())}_{os.path.basename(local_path)}"
    
    with open(local_path, "rb") as f:
        supabase.storage.from_(bucket_name).upload(
            path=file_name,
            file=f,
            file_options={"content-type": "audio/mpeg", "upsert": "true"}
        )
        
    return supabase.storage.from_(bucket_name).get_public_url(file_name)

def save_episode_to_db(topic: str, audio_url: str, script: list):
    """Saves generated episode metadata to the database."""
    if not supabase or not st.session_state.user:
        return
    try:
        supabase.table("podcast_history").insert({
            "user_id": st.session_state.user.id,
            "topic": topic,
            "audio_url": audio_url,
            "script": json.dumps(script)
        }).execute()
    except Exception as e:
        st.error(f"Failed to record episode to archive: {e}")

# ----------------- SIDEBAR: USER INFO & MEMORY ARCHIVE -----------------
with st.sidebar:
    st.write(f"Logged in as:\n**{st.session_state.user.email}**")
    if st.button("🚪 Log Out", use_container_width=True):
        logout_user()
    st.divider()

    st.header("🗄️ Studio Memory Archive")
    st.caption("Persistent show memory stored in Supabase")
    past_eps = get_recorded_episodes()
    
    if past_eps:
        for ep in past_eps:
            ep_title = ep.get("topic", "Untitled Episode")
            created_at = ep.get("created_at", "")[:10]
            audio_url = ep.get("audio_url", "")
            
            with st.expander(f"🎙️ {ep_title}"):
                st.write(f"**Recorded:** {created_at}")
                if audio_url:
                    st.audio(audio_url, format="audio/mp3")
    else:
        st.info("No recorded episodes yet.")

# ----------------- MAIN STUDIO DASHBOARD -----------------
st.title("🎙️ AI Live Podcast Generator")
st.caption("Multi-host conversational engine powered by OpenAI, OpenRouter, and ElevenLabs")

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

    # Final Output Audio Handling & Upload
    st.subheader("🎧 Final Produced Episode (Master Mix)")
    final_audio = pipeline_state.get("final_podcast_path", "output/final_podcast.mp3")
    
    public_audio_url = ""
    if os.path.exists(final_audio):
        with st.spinner("Archiving master track to cloud storage..."):
            public_audio_url = upload_to_supabase_storage(final_audio)
            save_episode_to_db(topic.strip(), public_audio_url, pipeline_state.get("script", []))
        
        # Stream master audio
        st.audio(public_audio_url if public_audio_url else final_audio, format="audio/mp3")
    st.divider()

    # Live Turn-by-Turn Studio Conversation
    st.subheader("💬 Live Studio Dialogue & Individual Audio Turns")
    
    script = pipeline_state.get("script", [])
    audio_files = pipeline_state.get("audio_files", [])
    hosts = pipeline_state.get("hosts", {})

    for i, turn in enumerate(script):
        speaker_key = turn.get("speaker", "Host A")
        avatar = HOST_AVATARS.get(speaker_key, "🎙️")
        
        host_info = hosts.get(speaker_key, {})
        display_name = host_info.get("name", speaker_key)
        
        with st.chat_message(name=display_name, avatar=avatar):
            st.markdown(f"**{display_name}**")
            st.write(turn.get("text", ""))
            
            # Line-by-line audio turn
            if i < len(audio_files) and os.path.exists(audio_files[i]):
                st.audio(audio_files[i], format="audio/mp3")