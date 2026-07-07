"""Tests for the pure/dependency-free parts of pipeline_common.py.

`run_step`, `resolve_rows`, `production_rows_for_content`, and
`find_content` all need real Notion/subprocess I/O and aren't unit-tested
here — consistent with add_karaoke_captions.py's own test file (this
folder has no mocking infra for Notion calls; those functions are thin,
directly-observable wrappers, not logic worth mocking around).
`_title_of` and `print_batch_summary` ARE pure, so they're tested here.
"""
from __future__ import annotations

from pipeline_common import _title_of, print_batch_summary


def test_title_of_extracts_the_title_property():
    page = {"properties": {"Name": {"type": "title", "title": [{"plain_text": "Detox x Jackie"}]}}}
    assert _title_of(page) == "Detox x Jackie"


def test_title_of_falls_back_when_no_title_property():
    page = {"properties": {"Notes": {"type": "rich_text", "rich_text": []}}}
    assert _title_of(page) == "(untitled)"


def test_title_of_concatenates_multiple_title_fragments():
    page = {"properties": {"Name": {"type": "title", "title": [
        {"plain_text": "Detox "}, {"plain_text": "x Jackie"},
    ]}}}
    assert _title_of(page) == "Detox x Jackie"


def test_print_batch_summary_all_ok_returns_true(capsys):
    results = [("row-a", "image", True), ("row-a", "voice", True)]
    assert print_batch_summary(results) is True


def test_print_batch_summary_any_failure_returns_false(capsys):
    results = [("row-a", "image", True), ("row-b", "voice", False)]
    assert print_batch_summary(results) is False


def test_print_batch_summary_empty_results_is_vacuously_ok(capsys):
    assert print_batch_summary([]) is True
