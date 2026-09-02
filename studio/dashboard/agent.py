"""agent.py — the Database tab's chat agent.

A plain function-calling loop over OpenAI's chat-completions API, using
`urllib` rather than the `openai` package: every other script in studio/ is
stdlib-only (see notion_image.py), the dashboard has no requirements file of
its own, and adding a dependency to run one chat box would break `python3
dashboard/...` on a machine that has not pip-installed anything.

What is here and what is not
----------------------------
Here: conversation persistence (in the mirror, so a browser refresh does not
lose the thread), the tool loop, and a hard cap on tool rounds.

Not here: the tools themselves (agent_tools.py) or any Notion knowledge. This
module never touches the board directly — it can only do what a tool lets it
do, which is the whole reason the tool list is short and read-mostly.
"""
from __future__ import annotations

import json
import os
import sqlite3
import urllib.error
import urllib.request
from typing import Any

import agent_tools
import studio_db

__all__ = ["chat", "history", "clear_history", "AgentUnavailable", "is_configured"]

OPENAI_URL = "https://api.openai.com/v1/chat/completions"

# Same model family the rest of this codebase standardised on (see the repo
# CLAUDE.md §Stack). Overridable because a local tool should not need a code
# change to try a different model.
DEFAULT_MODEL = os.environ.get("STUDIO_AGENT_MODEL", "gpt-5.4-mini")

# How many times the model may call tools before it must answer. Six is
# generous for "look it up, then write it" and low enough that a model stuck
# in a retry loop costs seconds, not a spend alert.
MAX_TOOL_ROUNDS = 6

# How much of the thread to replay. The agent is for short working exchanges
# ("add this idea", "what's ready to publish") — an unbounded history would
# grow the cost of every turn for no benefit.
HISTORY_TURNS = 24

REQUEST_TIMEOUT_S = 120


class AgentUnavailable(RuntimeError):
    """The agent cannot run — almost always a missing API key."""


def is_configured() -> bool:
    return bool(os.environ.get("OPENAI_API_KEY"))


def _call_openai(payload: dict) -> dict:
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        raise AgentUnavailable(
            "OPENAI_API_KEY is not set — add it to studio/.env and restart the "
            "dashboard. (The rest of the Database tab works without it; only "
            "chat needs a key.)")
    request = urllib.request.Request(
        OPENAI_URL, method="POST",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {key}",
                 "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_S) as response:
            return json.loads(response.read())
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:500]
        raise AgentUnavailable(f"OpenAI {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise AgentUnavailable(f"could not reach OpenAI: {exc.reason}") from exc


# ---------- conversation storage ----------

def history(conn: sqlite3.Connection, limit: int = HISTORY_TURNS) -> list[dict]:
    """The visible thread, oldest first — what the browser renders and what
    gets replayed to the model. Tool traffic is stored as `meta` on the
    assistant turn it belongs to rather than as separate messages, so the
    transcript reads the way the user experienced it."""
    rows = conn.execute(
        "SELECT id, at, role, content, meta FROM chat_messages "
        "ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    out = []
    for row in reversed(rows):
        try:
            meta = json.loads(row["meta"]) if row["meta"] else {}
        except json.JSONDecodeError:
            meta = {}
        out.append({"id": row["id"], "at": row["at"], "role": row["role"],
                    "content": row["content"], **meta})
    return out


def _remember(conn: sqlite3.Connection, role: str, content: str,
              meta: dict | None = None) -> None:
    conn.execute(
        "INSERT INTO chat_messages (at, role, content, meta) VALUES (?, ?, ?, ?)",
        (studio_db.now_iso(), role, content,
         json.dumps(meta or {}, ensure_ascii=False)))


def clear_history(conn: sqlite3.Connection) -> None:
    conn.execute("DELETE FROM chat_messages")


# ---------- the loop ----------

def _wire_messages(conn: sqlite3.Connection) -> list[dict]:
    """The stored thread in OpenAI's message shape. Only role + content — the
    tool call/result pairs from PREVIOUS turns are deliberately not replayed:
    they are large, and the assistant's own summary of what it did is the
    part that actually matters for continuity."""
    return [{"role": m["role"], "content": m["content"]}
            for m in history(conn)
            if m["role"] in ("user", "assistant") and m["content"]]


def chat(conn: sqlite3.Connection, message: str,
         push: Any = None, model: str | None = None) -> dict:
    """One user turn. Returns {reply, actions, tool_calls, model}.

    `push` is the Notion write-back callable handed to the tools; pass None
    to keep the agent's writes local-only.

    The user's message is persisted BEFORE the model is called, so a turn
    that fails mid-flight still shows up in the thread rather than vanishing
    and leaving the user unsure whether it was sent.
    """
    if not message.strip():
        raise ValueError("message is empty")

    _remember(conn, "user", message.strip())
    ctx = agent_tools.ToolContext(conn, push=push)
    model_name = model or DEFAULT_MODEL

    wire: list[dict] = [{"role": "system", "content": agent_tools.SYSTEM_PROMPT}]
    wire += _wire_messages(conn)

    performed: list[dict] = []
    reply = ""

    for _round in range(MAX_TOOL_ROUNDS):
        response = _call_openai({
            "model": model_name,
            "messages": wire,
            "tools": agent_tools.TOOL_SCHEMAS,
            "tool_choice": "auto",
        })
        choice = (response.get("choices") or [{}])[0]
        assistant = choice.get("message") or {}
        tool_calls = assistant.get("tool_calls") or []

        if not tool_calls:
            reply = (assistant.get("content") or "").strip()
            break

        # The assistant turn that REQUESTED the tools must be replayed
        # verbatim; OpenAI rejects a tool result whose call it cannot see.
        wire.append({"role": "assistant",
                     "content": assistant.get("content") or None,
                     "tool_calls": tool_calls})

        for call in tool_calls:
            function = call.get("function") or {}
            name = function.get("name", "")
            try:
                args = json.loads(function.get("arguments") or "{}")
            except json.JSONDecodeError as exc:
                # Malformed arguments are the model's mistake to fix, so they
                # go back as a tool result rather than aborting the turn.
                args, result = {}, {"error": f"arguments were not valid JSON: {exc}"}
            else:
                result = agent_tools.dispatch(name, args, ctx)

            performed.append({"tool": name, "args": args, "result": result})
            wire.append({"role": "tool", "tool_call_id": call.get("id", ""),
                         "content": agent_tools.result_json(result)})
    else:
        reply = ("I used up my tool budget for this turn without finishing. "
                 "Here is what I did manage to do — ask me to continue if "
                 "something is missing.")

    if not reply:
        reply = ("(no reply text — the model returned only tool calls)"
                 if performed else "(no reply)")

    _remember(conn, "assistant", reply,
              {"actions": [_action_summary(p) for p in performed]})
    return {"reply": reply,
            "actions": [_action_summary(p) for p in performed],
            "tool_calls": performed,
            "model": model_name}


def _action_summary(performed: dict) -> dict:
    """One line per tool call for the chat UI's activity chips. Only WRITES
    and FAILURES are worth surfacing — a chat that narrates every lookup is
    noise, but an edit the user did not notice is a problem."""
    tool, result = performed["tool"], performed["result"]
    if "error" in result:
        return {"tool": tool, "kind": "error", "text": result["error"]}
    if tool == "create_concept" and "created" in result:
        return {"tool": tool, "kind": "created",
                "text": f"Created concept “{result['created']['name']}”",
                "concept_id": result["created"]["id"],
                "sync": result.get("sync", {})}
    if tool == "update_concept" and "updated" in result:
        fields = ", ".join(result.get("changed_fields", []))
        return {"tool": tool, "kind": "updated",
                "text": f"Updated “{result['updated']['name']}” ({fields})",
                "concept_id": result["updated"]["id"],
                "sync": result.get("sync", {})}
    return {"tool": tool, "kind": "read", "text": tool.replace("_", " ")}
