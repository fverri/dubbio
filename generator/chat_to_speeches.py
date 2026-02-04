import json
from pathlib import Path
from openai import OpenAI
from dotenv import find_dotenv, dotenv_values

env_path = find_dotenv(usecwd=True)
values = dotenv_values(env_path)

client = OpenAI(api_key=values.get("OPENAI_API_KEY"))

OUTPUT_DIR = Path("speeches")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def _text_to_speech(speech_number: int, text: str, voice: str) -> None:
    audio_path = OUTPUT_DIR / f"speech_{speech_number}.wav"

    with client.audio.speech.with_streaming_response.create(
        model="gpt-4o-mini-tts-2025-12-15",
        voice=voice,
        input=text,
        speed=4 / 3,
        response_format="wav",
    ) as resp:
        resp.stream_to_file(str(audio_path))


def chat_to_speeches() -> None:
    with open("configuration.json", "r", encoding="utf-8") as file:
        data = json.load(file)

    speech_number = 1
    for message in data.get("messages", []):
        who = message.get("from")
        voice = data.get("voices", {}).get(who)
        if voice:
            _text_to_speech(speech_number, message.get("text", "") or "", voice)
        speech_number += 1