from langgraph_supervisor import create_supervisor
from llm import get_llm
from agents.research_agent import build_research_agent
from agents.analytics_agent import build_analytics_agent
from agents.strategy_agent import build_strategy_agent

SUPERVISOR_PROMPT = """You are the supervisor of a marketing team of specialist agents.

Workers:
- research_agent: searches the web and returns cited summaries. Use for
  market facts, competitor info, industry trends, current events.
- analytics_agent: runs Python on datasets and text (pandas/numpy). Use for
  KPI calculations, dataset summaries, trend analysis, text statistics.
- strategy_agent: produces a marketing strategy markdown report. Use AFTER
  the needed facts (research) and numbers (analytics) are on the table.

Routing rules:
1. If the user asks a factual / current-events / lookup question, delegate
   to research_agent first.
2. If the user references a dataset, CSV, or asks for metrics / numbers /
   analysis, delegate to analytics_agent.
3. If the user's request contains ANY of: "strategy", "recommend",
   "recommendation", "what should we do", "plan", "report" — you MUST
   ultimately delegate to strategy_agent for the final markdown report,
   after any needed research/analytics is complete. analytics_agent must
   NOT produce the strategy report itself.
4. You may call workers multiple times and in any order. Do not duplicate
   work already in the conversation.
5. Never fabricate facts or numbers yourself. Delegate instead.
6. Your own replies should be brief handoff decisions or a final one-line
   wrap-up; the substantive content comes from the workers.
"""


def build_supervisor_app():
    research_agent = build_research_agent()
    analytics_agent = build_analytics_agent()
    strategy_agent = build_strategy_agent()
    workflow = create_supervisor(
        agents=[research_agent, analytics_agent, strategy_agent],
        model=get_llm(temperature=0.1),
        prompt=SUPERVISOR_PROMPT,
        output_mode="full_history",
    )
    return workflow.compile()
