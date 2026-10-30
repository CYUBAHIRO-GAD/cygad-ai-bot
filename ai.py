import base64
from openai import OpenAI
from .config import OPENAI_API_KEY, OPENAI_MODEL, OPENAI_IMAGE_MODEL, ENABLE_WEB_SEARCH
from .prompts import SYSTEM_PROMPT, IMAGE_PROMPT_PREFIX
from .database import get_history, save_message

def client():
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is missing. Add it to your .env file.")
    return OpenAI(api_key=OPENAI_API_KEY, timeout=90, max_retries=2)

def ask(user_id: int, question: str, language: str = "en") -> str:
    history = get_history(user_id)
    instructions = SYSTEM_PROMPT + f"\n\nPreferred response language: {language}."
    # Responses API input accepts a list of role/content messages.
    input_items = [{"role": item["role"], "content": item["content"]} for item in history]
    input_items.append({"role": "user", "content": question})
    kwargs = {"model": OPENAI_MODEL, "instructions": instructions, "input": input_items}
    if ENABLE_WEB_SEARCH:
        kwargs["tools"] = [{"type": "web_search"}]
    response = client().responses.create(**kwargs)
    answer = response.output_text or "I couldn't generate an answer. Please try again."
    save_message(user_id, "user", question)
    save_message(user_id, "assistant", answer)
    return answer

def ask_photo(question: str, image_bytes: bytes, mime_type: str = "image/jpeg") -> str:
    data_url = f"data:{mime_type};base64,{base64.b64encode(image_bytes).decode('ascii')}"
    response = client().responses.create(
        model=OPENAI_MODEL,
        instructions=SYSTEM_PROMPT,
        input=[{"role": "user", "content": [
            {"type": "input_text", "text": question or
             "Inspect this IoT/electronics project photo. Identify visible parts, explain the likely circuit and point out possible issues. State uncertainty."},
            {"type": "input_image", "image_url": data_url}
        ]}]
    )
    return response.output_text or "I couldn't analyze that photo."

def generate_image(prompt: str) -> bytes:
    response = client().images.generate(
        model=OPENAI_IMAGE_MODEL,
        prompt=IMAGE_PROMPT_PREFIX + prompt,
        size="1536x1024",
        n=1
    )
    encoded = response.data[0].b64_json
    if not encoded:
        raise RuntimeError("The image service did not return image data.")
    return base64.b64decode(encoded)
