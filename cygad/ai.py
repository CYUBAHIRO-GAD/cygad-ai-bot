
import os
import io
from google import genai
from google.genai import types

from .prompts import SYSTEM_PROMPT, IMAGE_PROMPT_PREFIX
from .database import get_history, save_message

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
GEMINI_IMAGE_MODEL = os.getenv(
    "GEMINI_IMAGE_MODEL", "gemini-2.5-flash-image"
)
ENABLE_WEB_SEARCH = os.getenv("ENABLE_WEB_SEARCH", "false").lower() == "true"


def client():
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY is missing.")
    return genai.Client(api_key=GEMINI_API_KEY)


def ask(user_id: int, question: str, language: str = "en") -> str:
    history = get_history(user_id)

    contents = []
    for item in history:
        role = "model" if item["role"] == "assistant" else "user"
        contents.append(
            types.Content(
                role=role,
                parts=[types.Part.from_text(text=item["content"])]
            )
        )

    contents.append(
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=question)]
        )
    )

    config = types.GenerateContentConfig(
        system_instruction=(
            SYSTEM_PROMPT
            + f"\n\nPreferred response language: {language}."
        )
    )

    if ENABLE_WEB_SEARCH:
        config.tools = [{"google_search": {}}]

    response = client().models.generate_content(
        model=GEMINI_MODEL,
        contents=contents,
        config=config
    )

    answer = response.text or "I couldn't generate an answer. Please try again."

    save_message(user_id, "user", question)
    save_message(user_id, "assistant", answer)

    return answer


def ask_photo(
    question: str,
    image_bytes: bytes,
    mime_type: str = "image/jpeg"
) -> str:

    prompt = question or (
        "Inspect this IoT/electronics project photo. "
        "Identify visible parts, explain the likely circuit "
        "and point out possible issues. State uncertainty."
    )

    response = client().models.generate_content(
        model=GEMINI_MODEL,
        contents=[
            prompt,
            types.Part.from_bytes(
                data=image_bytes,
                mime_type=mime_type
            )
        ],
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT
        )
    )

    return response.text or "I couldn't analyze that photo."


def generate_image(prompt: str) -> bytes:
    response = client().models.generate_content(
        model=GEMINI_IMAGE_MODEL,
        contents=IMAGE_PROMPT_PREFIX + prompt,
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE"]
        )
    )

    for part in response.parts:
        if part.inline_data:
            return part.inline_data.data

    raise RuntimeError("The image service did not return image data.")
