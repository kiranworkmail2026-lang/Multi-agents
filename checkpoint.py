"""LangGraph checkpointer factory — MongoDB-backed (Atlas or self-hosted).

Used to persist graph state across HTTP turns so a paused (interrupted) run
can be resumed by a later request. Falls back to an in-memory saver if
MONGO_URI is unset — that mode loses state on process restart, so it's only
useful for local dev / tests.

Singleton pattern: one MongoClient per process. Do NOT call this per-request.
"""
from __future__ import annotations
import logging
import os

logger = logging.getLogger(__name__)

_checkpointer = None


def get_checkpointer():
    """Return a process-wide checkpointer instance.

    Reads MONGO_URI / MONGO_DB_NAME from env. Falls back to MemorySaver if
    MONGO_URI is not set.
    """
    global _checkpointer
    if _checkpointer is not None:
        return _checkpointer

    uri = (os.getenv("MONGO_URI") or "").strip()
    if not uri:
        from langgraph.checkpoint.memory import MemorySaver
        logger.warning(
            "MONGO_URI not set — using in-memory checkpointer "
            "(state is lost on process restart; interrupts cannot be resumed across requests)"
        )
        _checkpointer = MemorySaver()
        return _checkpointer

    try:
        from pymongo import MongoClient
        from langgraph.checkpoint.mongodb import MongoDBSaver

        db_name = os.getenv("MONGO_DB_NAME", "multi_agents")
        client = MongoClient(uri)
        # Light ping so a bad URI fails fast at boot rather than mid-request.
        client.admin.command("ping")
        _checkpointer = MongoDBSaver(client, db_name=db_name)
        logger.info("MongoDBSaver connected (db=%s)", db_name)
    except Exception as e:
        from langgraph.checkpoint.memory import MemorySaver
        logger.warning(
            "MongoDB checkpointer init failed (%s: %s) — falling back to in-memory",
            type(e).__name__, e,
        )
        _checkpointer = MemorySaver()
    return _checkpointer
