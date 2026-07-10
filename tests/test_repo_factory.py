"""Tests for src/crm/repo_factory.py — specifically the production guard
added 2026-07-10 after the expired-Postgres incident: APP_ENV=production
must REFUSE a non-postgres DATABASE_URL instead of silently falling back
to SQLite on an ephemeral disk (which wiped all CRM + webhook-dedup state
on every deploy for three weeks before anyone noticed)."""

from __future__ import annotations

import pytest

from src.crm.repo_factory import resolve_database_url


def test_production_refuses_missing_database_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("DATABASE_PATH", raising=False)
    with pytest.raises(RuntimeError, match="postgres"):
        resolve_database_url("data/jessica.db")


def test_production_refuses_sqlite_path_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///data/jessica.db")
    with pytest.raises(RuntimeError, match="ephemeral"):
        resolve_database_url("data/jessica.db")


def test_production_accepts_postgres_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@host/db")
    assert resolve_database_url("data/jessica.db") == "postgresql://u:p@host/db"


def test_development_still_falls_back_to_sqlite(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("DATABASE_PATH", raising=False)
    assert resolve_database_url("data/jessica.db") == "data/jessica.db"


def test_unset_app_env_defaults_to_development_behavior(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("APP_ENV", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("DATABASE_PATH", "custom.db")
    assert resolve_database_url("data/jessica.db") == "custom.db"
