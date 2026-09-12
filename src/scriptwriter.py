import os
import re
import json
from openai import OpenAI
from langchain_core.tools import tool
from src.config import api_key

@tool
def write_script(topic: str, memory_summary: str, reserach_memory: str) -> dict:
    """Generates dynamic topic-appropriate host personas and structured long-form dialogue."""
    print("[*] Generating dynamic hosts and script via OpenRouter...")
    client = OpenAI(api_key=api_key, base_url="https://openrouter.ai/api/v1")

    prompt = f"""
Create an in-depth, multi-turn podcast discussion about: "{topic}".

Prior Episodes Context:
{memory_summary}

Live Research Context:
{reserach_memory}

Host Personas:
- Host A: Engaging lead anchor / moderator (Female profile). Sets the agenda, frames insightful questions, and guides transitions.
- Host B: Energetic, curious tech analyst (Younger male profile). Provides practical analogies, real-world examples, and optimistic perspectives.
- Host C: Seasoned veteran / domain specialist (Older male profile). Offers architectural depth, historical precedents, and pragmatic critiques.

Requirements:
1. Invent 3 context-aware names fitting the topic (no generic names like Host A/B/C).
2. Generate 12 to 16 dialogue turns total, alternating naturally between the hosts.
3. Every turn MUST be substantive (3 to 5 detailed sentences). Never output single-sentence one-liners.
4. Hosts must address and reference each other using their invented names.
5. Return ONLY a valid JSON object matching the exact schema below.

JSON Format:
{{
  "hosts": {{
    "Host A": {{"name": "<Dynamic Name>", "role": "<Short Role>"}},
    "Host B": {{"name": "<Dynamic Name>", "role": "<Short Role>"}},
    "Host C": {{"name": "<Dynamic Name>", "role": "<Short Role>"}}
  }},
  "dialogue": [
    {{"speaker": "Host A", "text": "Welcome to the show..."}},
    {{"speaker": "Host B", "text": "Excited to break this down..."}},
    {{"speaker": "Host C", "text": "Looking back historically..."}}
  ]
}}
"""
    content = ""
    try:
        response = client.chat.completions.create(
            model="nvidia/nemotron-3-ultra-550b-a55b:free",
            extra_body={
                "models": [
                    "mistralai/mistral-small-24b-instruct-2501:free",
                    "qwen/qwen-2.5-72b-instruct:free"
                ]
            },
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=4000,
            response_format={"type": "json_object"}
        )

        if response and getattr(response, "choices", None) and len(response.choices) > 0:
            choice = response.choices[0]
            if hasattr(choice, "message") and choice.message:
                content = choice.message.content or ""
    except Exception as api_err:
        print(f"[!] OpenRouter API call failed: {api_err}")

    print(f"[*] Raw LLM output length: {len(content)} characters")

    # Clean out potential markdown fences
    cleaned = re.sub(r"^```(?:json)?\s*", "", content.strip(), flags=re.MULTILINE)
    cleaned = re.sub(r"\s*```$", "", cleaned.strip(), flags=re.MULTILINE)

    json_match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    clean_json = json_match.group(0) if json_match else cleaned

    try:
        data = json.loads(clean_json)
        if "hosts" not in data or "dialogue" not in data or len(data["dialogue"]) < 5:
            raise ValueError("Parsed JSON missing required keys or generated dialogue was truncated.")
        print(f"[*] Successfully generated {len(data['dialogue'])} script turns.")
    except Exception as e:
        print(f"[!] JSON parsing failed ({e}). Using substantive fallback script.")
        data = {
            "hosts": {
                "Host A": {"name": "Maya", "role": "Lead Moderator"},
                "Host B": {"name": "Liam", "role": "Applied AI Engineer"},
                "Host C": {"name": "Julian", "role": "Systems Architect"}
            },
            "dialogue": [
                {
                    "speaker": "Host A",
                    "text": f"Welcome back everyone. Today we are digging into an essential subject: {topic}. There is a lot of buzz surrounding how this shifts the landscape, but understanding where the practical applications meet the engineering bottlenecks is critical."
                },
                {
                    "speaker": "Host B",
                    "text": "Completely agree, Maya. From an implementation standpoint, people often assume adopting these patterns is just about writing a few prompt templates or orchestrating tools. In reality, handling state persistence, execution latency, and deterministic output is where all the actual engineering hours go."
                },
                {
                    "speaker": "Host C",
                    "text": "Spot on, Liam. Over the last two decades, every major architectural pivot from monolithic service layers to microservices and distributed event streams had the exact same learning curve. If your fundamental domain boundaries are ambiguous, automating or delegating tasks to autonomous agents just scales the confusion."
                },
                {
                    "speaker": "Host A",
                    "text": "Julian, you raise an interesting perspective regarding architecture. Where are teams currently facing the steepest roadblocks when moving from a proof of concept to a high-throughput production environment?"
                },
                {
                    "speaker": "Host B",
                    "text": "Monitoring and observability without question. When an LLM decides to trigger tools conditionally, failure isn't a traditional 500 error code—it's silent drift or recursive hallucination that can drain rate limits in minutes."
                },
                {
                    "speaker": "Host C",
                    "text": "Which brings us back to reliable guardrails and explicit schema verification. Technology evolves, but deterministic system design principles remain unchanged."
                }
            ]
        }

    os.makedirs("temp", exist_ok=True)
    with open("temp/script.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    return data
