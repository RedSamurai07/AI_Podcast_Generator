import os
from elevenlabs.client import ElevenLabs
from langchain_core.tools import tool
from src.config import labs_key, voice_a, voice_b, voice_c

@tool
def generate_voice_tracks(script: list[dict]) -> list[str]:
    """Synthesizes speech using voice profiles matched to Host keys."""
    client = ElevenLabs(api_key=labs_key)
    os.makedirs("temp", exist_ok=True)

    audio_files = []
    has_labs_key = bool(labs_key and labs_key.strip())

    if has_labs_key:
        try:
            client = ElevenLabs(api_key=labs_key)
        except Exception as e:
            print(f"[!] ElevenLabs client init error: {e}")
            has_labs_key = False

    for i, turn in enumerate(script):
        speaker_key = turn.get("speaker", "Host A")
        text = turn.get("text", "")

        if "B" in speaker_key:
            voice_id = voice_b
        elif "C" in speaker_key:
            voice_id = voice_c
        else:
            voice_id = voice_a

        filepath = os.path.join("temp", f"line_{i:03d}_{speaker_key.replace(' ', '')}.mp3")

        generated = False
        if has_labs_key:
            try:
                stream = client.text_to_speech.convert(
                    voice_id=voice_id,
                    text=text,
                    model_id="eleven_multilingual_v2"
                )
                with open(filepath, "wb") as f:
                    for chunk in stream:
                        if chunk:
                            f.write(chunk)
                generated = True
            except Exception as err:
                print(f"[!] ElevenLabs TTS failed for turn {i} ({err}). Creating placeholder track.")

        if not generated:
            # Generate a 2-second silent placeholder track using pydub so pipeline succeeds
            from pydub import AudioSegment
            placeholder = AudioSegment.silent(duration=2000)
            placeholder.export(filepath, format="mp3")

        audio_files.append(filepath)

    return audio_files