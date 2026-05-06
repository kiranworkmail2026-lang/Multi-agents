"""Chat LLM factory — Google Gemini via AI Studio.

Requires GOOGLE_API_KEY in the environment (Render dashboard or local .env).
Get a key at https://aistudio.google.com/apikey
"""
import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()


def get_llm(temperature: float = 0.2, json_mode: bool = False) -> ChatGoogleGenerativeAI:
    kwargs = dict(
        model=os.getenv("GEMINI_MODEL", "gemma-4-31b-it"),
        temperature=temperature,
        max_output_tokens=int(os.getenv("GEMINI_MAX_OUTPUT_TOKENS", "1024")),
        timeout=300,
        # google_api_key picked up from GOOGLE_API_KEY env automatically
    )
    if json_mode:
        # Gemini's structured-output flag
        kwargs["model_kwargs"] = {"response_mime_type": "application/json"}
    return ChatGoogleGenerativeAI(**kwargs)
