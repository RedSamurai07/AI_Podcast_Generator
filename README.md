# AI_Podcast_Generator

## End-to-End Build Flow

This pipeline is designed to run autonomously from a single text prompt to a finished MP3 file:

Topic Input & Live Research: Accept a topic input from the user and research it live using the Perplexity API to fetch accurate answers, context, and citations.

Script Generation: Pass the resulting research summary to an LLM (such as Claude or GPT-4). Prompt the model to write a structured, natural-sounding two-host script featuring alternating conversational turns between Host A and Host B.

Voice Generation (Host A): Send Host A's lines to ElevenLabs (Voice 1) to generate the audio. This voice should be assigned a specific personality, such as calm and analytical.

Voice Generation (Host B): Send Host B's lines to ElevenLabs (Voice 2) to generate the audio using a contrasting voice profile, such as energetic and curious.

Audio Mixing: Use the Python library pydub to merge the alternating voice clips sequentially. Then, layer in background music (e.g., from the YouTube Audio Library) at a low volume to create a professional podcast feel.

Final Export: Export the fully mixed audio sequence as a final MP3 file with properly balanced audio levels, ready to be uploaded directly to Spotify, YouTube, or Apple Podcasts.

## Required Tech Stack:

To execute these steps, the project relies on the following tools:

- Core Language: Python

- Research Engine: Perplexity API(n o free api) or some other reasoning model

- Scriptwriting: Claude or GPT-4

- Audio/TTS Generation: ElevenLabs (Two distinct voices)

- Audio Engineering/Mixing: pydub

- Assets: YouTube Audio Library (for free background music)

## File Structure
ai_podcast_generator/
│
├── main.py                  # The entry point that orchestrates the end-to-end pipeline
├── requirements.txt         # Python dependencies (pydub, openai, anthropic, elevenlabs, etc.)
├── .env                     # Environment variables (API keys for Perplexity, LLM, ElevenLabs)
│
├── src/                     # Core module directory
│   ├── __init__.py
│   ├── config.py            # Loads API keys and configurations from .env
│   ├── researcher.py        # Handles the Perplexity API call to fetch topic context
│   ├── scriptwriter.py      # Passes research to Claude/GPT-4 and parses the 2-host script
│   ├── voice_generator.py   # Sends script lines to ElevenLabs and downloads individual audio clips
│   └── audio_mixer.py       # Uses pydub to stitch voice clips together and overlay background music
│
├── assets/                  # Static files needed for production
│   └── bg_music.mp3         # Background music track (e.g., from YouTube Audio Library)
│
├── temp/                    # Temporary storage during generation (can be gitignored)
│   ├── script.json          # The structured JSON output of the script from the LLM
│   ├── host_a_line_1.mp3    # Individual TTS output files
│   └── host_b_line_1.mp3    
│
└── output/                  # The final generated artifacts
    └── final_podcast.mp3    # The completed, fully mixed episode ready for upload.

    

