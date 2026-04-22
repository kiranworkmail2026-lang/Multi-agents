import os
from dotenv import load_dotenv
from langchain_ollama import ChatOllama

load_dotenv()

def get_llm(temperature: float = 0.2, json_mode: bool = False) -> ChatOllama:
    kwargs = dict(
        model=os.getenv("OLLAMA_MODEL", "gemma4:e4b"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        temperature=temperature,
    )
    if json_mode:
        kwargs["format"] = "json"
    return ChatOllama(**kwargs)
