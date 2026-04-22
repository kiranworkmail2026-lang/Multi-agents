from langgraph.prebuilt import create_react_agent
from llm import get_llm
from tools.search import web_search

RESEARCH_PROMPT = (
    "You are a research agent. Use the web_search tool to gather facts, "
    "then produce a concise, source-cited summary. Always cite URLs. "
    "If the search results do not contain the answer, say so explicitly."
)


def build_research_agent():
    return create_react_agent(
        model=get_llm(temperature=0.2),
        tools=[web_search],
        name="research_agent",
        prompt=RESEARCH_PROMPT,
    )
