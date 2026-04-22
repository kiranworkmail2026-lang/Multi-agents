from langchain_core.tools import tool
from langchain_experimental.utilities import PythonREPL

_repl = PythonREPL()


@tool
def python_repl(code: str) -> str:
    """Execute Python code and return stdout / final expression value.

    Use this for numerical analysis, pandas operations on CSV/TSV files,
    text statistics, regex, or any computation. The session persists across
    calls within the same agent run, so you can build up state.

    Conventions:
    - To see output, use print(...) or end with an expression.
    - pandas, numpy are available (import them).
    - To load data, use absolute or project-relative paths; the working
      directory is the project root.

    Args:
        code: Python source to execute.

    Returns:
        Captured stdout (and stderr on error).
    """
    try:
        result = _repl.run(code)
    except Exception as e:  # pragma: no cover
        return f"ERROR: {type(e).__name__}: {e}"
    return result if result else "(no output)"
