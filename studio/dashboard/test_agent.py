"""Tests for agent.py's tool loop, with the OpenAI call stubbed out.

What is worth pinning here is the loop's behaviour under model misbehaviour:
malformed tool arguments, a model that never stops calling tools, and a
model that returns only tool calls and no prose. All three have to end in a
usable turn rather than a 500 or a hang.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import agent  # noqa: E402
import repo  # noqa: E402
import studio_db  # noqa: E402


@pytest.fixture
def conn():
    with studio_db.connect(":memory:") as c:
        yield c


def fake_openai(scripted, calls=None):
    """Replay a list of canned API responses, recording each request."""
    queue = list(scripted)

    def call(payload):
        if calls is not None:
            calls.append(payload)
        return queue.pop(0) if queue else _say("(ran out of script)")

    return call


def _say(text):
    return {"choices": [{"message": {"role": "assistant", "content": text}}]}


def _tool(name, args, call_id="call-1"):
    return {"choices": [{"message": {
        "role": "assistant", "content": None,
        "tool_calls": [{"id": call_id, "type": "function",
                        "function": {"name": name,
                                     "arguments": json.dumps(args)}}]}}]}


def test_a_plain_answer_is_stored_and_returned(conn, monkeypatch):
    monkeypatch.setattr(agent, "_call_openai", fake_openai([_say("Hello.")]))
    out = agent.chat(conn, "hi")
    assert out["reply"] == "Hello."
    thread = agent.history(conn)
    assert [m["role"] for m in thread] == ["user", "assistant"]
    assert thread[0]["content"] == "hi"


def test_a_tool_call_runs_and_its_result_feeds_the_next_round(conn, monkeypatch):
    sent = []
    monkeypatch.setattr(agent, "_call_openai", fake_openai([
        _tool("create_concept", {"name": "Rounded shoulders", "cta": "posture"}),
        _say("Added it."),
    ], sent))

    out = agent.chat(conn, "add a concept about rounded shoulders")

    assert out["reply"] == "Added it."
    assert repo.find_concept_by_name(conn, "Rounded shoulders") is not None
    # the second request carried the assistant's tool_calls AND the result
    roles = [m["role"] for m in sent[1]["messages"]]
    assert "tool" in roles
    tool_msg = next(m for m in sent[1]["messages"] if m["role"] == "tool")
    assert "Rounded shoulders" in tool_msg["content"]


def test_write_actions_are_summarised_for_the_ui(conn, monkeypatch):
    monkeypatch.setattr(agent, "_call_openai", fake_openai([
        _tool("create_concept", {"name": "Sleep points"}),
        _say("Done."),
    ]))
    out = agent.chat(conn, "new idea: sleep points")
    created = [a for a in out["actions"] if a["kind"] == "created"]
    assert created and "Sleep points" in created[0]["text"]
    assert created[0]["concept_id"]


def test_a_read_only_turn_is_not_reported_as_a_change(conn, monkeypatch):
    monkeypatch.setattr(agent, "_call_openai", fake_openai([
        _tool("board_summary", {}), _say("Nothing pending."),
    ]))
    out = agent.chat(conn, "how's the board?")
    assert all(a["kind"] == "read" for a in out["actions"])


def test_malformed_tool_arguments_go_back_to_the_model_not_up_as_a_500(conn, monkeypatch):
    broken = {"choices": [{"message": {
        "role": "assistant", "content": None,
        "tool_calls": [{"id": "c1", "type": "function",
                        "function": {"name": "create_concept",
                                     "arguments": "{not json"}}]}}]}
    monkeypatch.setattr(agent, "_call_openai",
                        fake_openai([broken, _say("Sorry, retrying.")]))
    out = agent.chat(conn, "add something")
    assert out["reply"] == "Sorry, retrying."
    assert any(a["kind"] == "error" for a in out["actions"])


def test_a_tool_error_is_surfaced_as_an_action_chip(conn, monkeypatch):
    monkeypatch.setattr(agent, "_call_openai", fake_openai([
        _tool("get_concept", {"name_or_id": "does not exist"}),
        _say("I couldn't find that."),
    ]))
    out = agent.chat(conn, "show me the missing one")
    assert any(a["kind"] == "error" for a in out["actions"])


def test_a_model_stuck_in_a_tool_loop_is_cut_off_with_a_usable_reply(conn, monkeypatch):
    """Without the round cap this would call the API forever."""
    calls = []
    monkeypatch.setattr(agent, "_call_openai",
                        fake_openai([_tool("board_summary", {})] * 50, calls))
    out = agent.chat(conn, "go")
    assert len(calls) == agent.MAX_TOOL_ROUNDS
    assert "tool budget" in out["reply"]


def test_the_user_message_is_stored_even_when_the_model_call_fails(conn, monkeypatch):
    """A turn that dies mid-flight must still appear in the thread — a
    message that silently vanishes leaves you unsure whether it was sent."""
    def boom(_payload):
        raise agent.AgentUnavailable("OpenAI 500: nope")

    monkeypatch.setattr(agent, "_call_openai", boom)
    with pytest.raises(agent.AgentUnavailable):
        agent.chat(conn, "this should still be recorded")
    assert agent.history(conn)[-1]["content"] == "this should still be recorded"


def test_an_empty_message_is_rejected(conn):
    with pytest.raises(ValueError):
        agent.chat(conn, "   ")


def test_history_is_replayed_but_capped(conn, monkeypatch):
    sent = []
    for n in range(40):
        agent._remember(conn, "user", f"message {n}")
    monkeypatch.setattr(agent, "_call_openai", fake_openai([_say("ok")], sent))
    agent.chat(conn, "latest")
    replayed = [m for m in sent[0]["messages"] if m["role"] == "user"]
    assert len(replayed) <= agent.HISTORY_TURNS
    assert replayed[-1]["content"] == "latest"   # the newest turn is always there


def test_clear_history_empties_the_thread(conn, monkeypatch):
    monkeypatch.setattr(agent, "_call_openai", fake_openai([_say("ok")]))
    agent.chat(conn, "hi")
    agent.clear_history(conn)
    assert agent.history(conn) == []


def test_a_missing_api_key_gives_an_actionable_message(conn, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    assert agent.is_configured() is False
    with pytest.raises(agent.AgentUnavailable) as exc:
        agent._call_openai({})
    assert "studio/.env" in str(exc.value)


def test_tools_are_offered_to_the_model_on_every_request(conn, monkeypatch):
    sent = []
    monkeypatch.setattr(agent, "_call_openai", fake_openai([_say("ok")], sent))
    agent.chat(conn, "hi")
    names = {t["function"]["name"] for t in sent[0]["tools"]}
    assert "create_concept" in names
    assert sent[0]["messages"][0]["role"] == "system"
