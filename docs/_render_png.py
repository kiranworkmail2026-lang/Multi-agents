"""Render the architecture as a PNG using matplotlib."""
import os
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Ellipse

fig, ax = plt.subplots(figsize=(16, 11))
ax.set_xlim(0, 160)
ax.set_ylim(0, 110)
ax.axis("off")
ax.set_facecolor("#ffffff")

def box(x, y, w, h, label, bg="#ffffff", fs=10, ec="#1e1e1e", lw=1.6, style="round,pad=0.4"):
    p = FancyBboxPatch((x, y), w, h, boxstyle=style, linewidth=lw,
                       edgecolor=ec, facecolor=bg)
    ax.add_patch(p)
    ax.text(x + w / 2, y + h / 2, label, ha="center", va="center",
            fontsize=fs, family="monospace")

def ell(x, y, w, h, label, bg="#b2f2bb", fs=10):
    e = Ellipse((x + w / 2, y + h / 2), w, h, facecolor=bg, edgecolor="#1e1e1e", lw=1.6)
    ax.add_patch(e)
    ax.text(x + w / 2, y + h / 2, label, ha="center", va="center",
            fontsize=fs, family="monospace", fontweight="bold")

def arrow(x1, y1, x2, y2, label=None, dashed=False, color="#1e1e1e", lw=1.5):
    a = FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="->", mutation_scale=14,
                        linestyle="--" if dashed else "-", linewidth=lw, color=color)
    ax.add_patch(a)
    if label:
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        ax.text(mx, my + 0.8, label, ha="center", va="center",
                fontsize=7.5, family="monospace",
                bbox=dict(facecolor="white", edgecolor="none", pad=1.2))

# Title
ax.text(80, 105, "Marketing Multi-Agent System  ·  LangGraph supervisor + Ollama gemma4:e4b",
        ha="center", fontsize=15, fontweight="bold", family="sans-serif")
ax.text(80, 102, "router topology · native tool-calling",
        ha="center", fontsize=10, style="italic", color="#555")

# User
box(3, 75, 18, 8, "User\n(CLI)", bg="#d0ebff")
box(3, 60, 18, 8, "main.py\napp.stream(...)", bg="#e7f5ff")
arrow(12, 75, 12, 68)

# LangGraph container
box(26, 8, 82, 90, "", bg="#f8f9fa", ec="#495057", lw=2, style="round,pad=0.6")
ax.text(67, 94, "LangGraph  ·  langgraph-supervisor", ha="center",
        fontsize=12, fontweight="bold")
ax.text(67, 91, "create_supervisor(agents=[research, analytics, strategy])",
        ha="center", fontsize=9, family="monospace", color="#555")

# Supervisor
box(47, 75, 40, 12, "supervisor\n(gemma4:e4b · temp 0.1)\nrouter + handoff tool calls",
    bg="#ffec99", fs=9)

# Three workers
box(30, 44, 24, 16, "research_agent\n(ReAct)\n\nweb facts\n+ citations",
    bg="#b2f2bb", fs=8.5)
box(55, 44, 24, 16, "analytics_agent\n(ReAct)\n\npandas / numpy\non CSV + text",
    bg="#ffc9c9", fs=8.5)
box(80, 44, 24, 16, "strategy_agent\n(ReAct, no tools)\n\nmarkdown report\nrouter synthesizer",
    bg="#d0bfff", fs=8.5)

# Handoffs (bidirectional supervisor ↔ worker)
arrow(55, 75, 42, 60, "transfer_to_research")
arrow(44, 60, 57, 75, "transfer_back", dashed=True)
arrow(67, 75, 67, 60, "transfer_to_analytics")
arrow(70, 60, 70, 75, "transfer_back", dashed=True)
arrow(80, 75, 92, 60, "transfer_to_strategy")
arrow(94, 60, 82, 75, "transfer_back", dashed=True)

# Tools belt
box(28, 22, 78, 14, "", bg="#fff9db", ec="#868e96", lw=1.5, style="round,pad=0.4")
ax.text(67, 33, "Tools", ha="center", fontsize=10, fontweight="bold")
box(30, 23, 24, 8, "web_search\n(SerpAPI · Google)", bg="#ffe8cc", fs=8)
box(55, 23, 24, 8, "python_repl\n(pandas, numpy)", bg="#ffe8cc", fs=8)
box(80, 23, 24, 8, "(none)\nstrategy is\npure reasoning", bg="#f1f3f5", fs=8)

arrow(42, 44, 42, 31, dashed=True)
arrow(67, 44, 67, 31, dashed=True)

# LLM stack right
box(115, 78, 42, 10, "llm.py · ChatOllama\nget_llm(temperature, json_mode)", bg="#e7f5ff", fs=9)
box(115, 65, 42, 8, "Ollama server  localhost:11434", bg="#d3f9d8", fs=9)
box(115, 53, 42, 8, "gemma4:e4b  (8.0B · tools+vision)", bg="#b2f2bb", fs=9)
arrow(136, 78, 136, 73)
arrow(136, 65, 136, 61)

# External services right
box(115, 32, 42, 8, "SerpAPI (Google Search)", bg="#ffd8a8", fs=9)
box(115, 20, 42, 8, "Local FS  ·  sample_data/*.csv", bg="#ffec99", fs=9)

# Dashed LLM / external calls
arrow(87, 81, 115, 83, "invoke", dashed=True)
arrow(54, 27, 115, 36, "search", dashed=True)
arrow(79, 27, 115, 24, "read_csv", dashed=True)

# Legend
ax.text(3, 18, "Legend:", fontsize=10, fontweight="bold")
arrow(3, 14, 12, 14)
ax.text(13, 14, "handoff / graph edge", fontsize=9, va="center")
arrow(3, 10, 12, 10, dashed=True)
ax.text(13, 10, "LLM or external call", fontsize=9, va="center")

out = os.path.join(os.path.dirname(__file__), "architecture.png")
plt.savefig(out, dpi=180, bbox_inches="tight", facecolor="#ffffff")
print(f"wrote {out}")
