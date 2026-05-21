"""Tests for PromotionsLoader."""

from __future__ import annotations

import pytest

from src.tools.promotions import PromotionsLoader


@pytest.fixture(scope="module")
def loader() -> PromotionsLoader:
    return PromotionsLoader()


def test_all_three_offers_loaded(loader: PromotionsLoader) -> None:
    ids = {o.id for o in loader.all_offers()}
    assert ids == {
        "free_consult_fee_v1",
        "online_consult_free_shipping_v1",
        "package_5_pct_off_v1",
    }


def test_appointment_close_offers_includes_free_fee(loader: PromotionsLoader) -> None:
    offers = loader.for_stage("appointment_close")
    ids = [o.id for o in offers]
    assert "free_consult_fee_v1" in ids


def test_mode_choice_offers_includes_online(loader: PromotionsLoader) -> None:
    offers = loader.for_stage("appointment_mode_choice")
    ids = [o.id for o in offers]
    assert "online_consult_free_shipping_v1" in ids


def test_sales_close_offers_includes_package_discount(loader: PromotionsLoader) -> None:
    offers = loader.for_stage("sales_close")
    ids = [o.id for o in offers]
    assert "package_5_pct_off_v1" in ids


def test_applies_to_filter(loader: PromotionsLoader) -> None:
    offers = loader.for_stage(
        "appointment_close", applies_to="online_consultation"
    )
    ids = [o.id for o in offers]
    assert "free_consult_fee_v1" in ids


def test_unmatched_stage_returns_empty(loader: PromotionsLoader) -> None:
    offers = loader.for_stage("does_not_exist")
    assert offers == []
