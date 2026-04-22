# Multi-Agent System (LangGraph + Ollama Gemma)

Supervisor agent orchestrating a research agent. Built with `langgraph-supervisor` and local Gemma 3 4B via Ollama.

## Architecture

```
User -> Supervisor -> Research Agent -> web_search (DuckDuckGo)
                   <-      results     <-
        Final answer
```

- `llm.py` — ChatOllama factory
- `tools/search.py` — DuckDuckGo web search tool
- `agents/research_agent.py` — ReAct agent with search tool
- `agents/supervisor.py` — supervisor built via `langgraph-supervisor`
- `main.py` — CLI entry point

## Setup

1. Install Ollama and pull Gemma 3 4B:
   ```bash
   ollama pull gemma3:4b
   ollama serve
   ```
2. Create venv and install deps:
   ```bash
   python -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   ```
3. Copy env file:
   ```bash
   cp .env.example .env
   ```

## Run

```bash
python main.py "Who won the 2024 Nobel Prize in Physics?"
```

## Adding new workers

1. Create `agents/<name>_agent.py` using `create_react_agent`.
2. Import and add it to the `agents=[...]` list in `agents/supervisor.py`.
3. Mention it in `SUPERVISOR_PROMPT`.

## Swapping the search provider

Replace `tools/search.py` with a Tavily / SerpAPI / Google tool — keep the `@tool` decorator and signature, and update the import in `research_agent.py`.

## Notes

- Tool calling requires a recent Ollama (>=0.3) and a Gemma variant that supports tools. Gemma 3 4B supports tool calling via Ollama's function-calling interface.
- If tool calls are unreliable on 4B, try `gemma4:e4b` by editing `.env`.
