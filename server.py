"""FastAPI HTTP wrapper around the multi-agent supervisor.

Exposes:
  GET  /health     → liveness probe for Render.
  POST /query      → SSE stream of agent updates + final markdown answer.
                     Body: {"question": "..."}
                     Auth: X-API-Key header must match SERVICE_API_KEY env.
"""
from __future__ import annotations
import asyncio
import json
import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncIterator

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from agent_runtime import stream_events
from ingest import ingest_all
from vectordb import get_collection

load_dotenv()

logger = logging.getLogger("server")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

SERVICE_API_KEY = os.getenv("SERVICE_API_KEY", "")
# 15s SSE keep-alive comments so Render's proxy doesn't idle-close the connection.
SSE_PING_SECONDS = 15


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Boot-time lazy ingest.

    On every container start: if Chroma is empty (fresh deploy or silent
    restart on Render's ephemeral disk), populate it from docs/knowledge/.
    Tolerant of Ollama being unreachable — logs a warning and lets the
    service start anyway so /health stays green.
    """
    try:
        col = get_collection()
        n = col.count()
        if n == 0:
            logger.info("vectordb empty — running lazy ingest from docs/knowledge/")
            ingest_all(col)
            logger.info("lazy ingest complete; collection size=%d", col.count())
        else:
            logger.info("vectordb already populated (count=%d) — skipping ingest", n)
    except Exception as e:
        logger.warning("lazy ingest skipped due to error: %s: %s", type(e).__name__, e)
    yield
    # nothing to clean up on shutdown


app = FastAPI(title="multi-agent-svc", version="0.1.0", lifespan=lifespan)


def require_api_key(x_api_key: str | None = Header(default=None)):
    if not SERVICE_API_KEY:
        # Fail closed in prod: missing key on the server is a misconfig.
        raise HTTPException(status_code=500, detail="SERVICE_API_KEY not configured")
    if x_api_key != SERVICE_API_KEY:
        raise HTTPException(status_code=401, detail="invalid or missing X-API-Key")


class QueryBody(BaseModel):
    question: str = Field(..., min_length=1, max_length=4000)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/query", dependencies=[Depends(require_api_key)])
async def query(body: QueryBody) -> EventSourceResponse:
    async def gen() -> AsyncIterator[dict]:
        loop = asyncio.get_running_loop()
        # stream_events is a sync generator (LangGraph .stream is sync).
        # Run it in a thread and pull items off a queue so we don't block the loop.
        queue: asyncio.Queue = asyncio.Queue()
        SENTINEL = object()

        def producer():
            try:
                for ev in stream_events(body.question):
                    asyncio.run_coroutine_threadsafe(queue.put(ev), loop)
            except Exception as e:  # pragma: no cover
                asyncio.run_coroutine_threadsafe(
                    queue.put({"type": "error", "message": f"{type(e).__name__}: {e}"}),
                    loop,
                )
            finally:
                asyncio.run_coroutine_threadsafe(queue.put(SENTINEL), loop)

        loop.run_in_executor(None, producer)

        while True:
            ev = await queue.get()
            if ev is SENTINEL:
                yield {"event": "done", "data": "{}"}
                return
            event_name = {
                "agent_update": "agent_update",
                "final": "final",
                "error": "error",
            }.get(ev.get("type", ""), "message")
            yield {"event": event_name, "data": json.dumps(ev, default=str)}

    return EventSourceResponse(gen(), ping=SSE_PING_SECONDS)
