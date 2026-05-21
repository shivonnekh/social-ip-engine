"""Typed loader for configs/tcm-sales-flow.yaml.

Validates structure at startup — fails loud if required keys are missing.
All data is returned as frozen dataclasses so downstream code cannot mutate
the in-memory config after load (immutability per CLAUDE.md coding style).
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping

import yaml

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_DEFAULT_PATH = _REPO_ROOT / "configs" / "tcm-sales-flow.yaml"

_VALID_ACTIONS = frozenset({
    "send_text",
    "send_image",
    "analyze_tongue",
    "declare_constitution",
    "match_clinic",
    "propose_booking",
    "save_booking",
})


# ── Typed data structures ─────────────────────────────────────────────


@dataclass(frozen=True)
class Clinic:
    id: str
    name_zh: str
    district: str
    address: str
    phone: str
    # mon..sun → "HH:MM-HH:MM" or "HH:MM-HH:MM|HH:MM-HH:MM" (split shift)
    # or "closed". Pipe separator added 2026-04-24 for HK TCM clinics that
    # take a lunch break — handled by src/tools/sales.py::_parse_hours.
    opening_hours: Mapping[str, str]
    name_brand_en: str = ""
    email: str = ""
    booking_url: str = ""
    # Optional nearest-MTR hint ("沙田圍站A出口，步行約2分鐘") — surfaced in
    # match_clinic's response so the agent can tell the user how to get there.
    mtr_hint: str = ""


@dataclass(frozen=True)
class ConstitutionType:
    key_zh: str
    en: str
    characteristics: str
    tongue_signals: tuple[str, ...]
    q1_weight: Mapping[str, int]
    q2_weight: Mapping[str, int]
    # Q3-Q5 added 2026-04-29 (5-question constitution survey expansion).
    # Default to empty mapping so existing 2-Q-only configs still load.
    q3_weight: Mapping[str, int] = MappingProxyType({})
    q4_weight: Mapping[str, int] = MappingProxyType({})
    q5_weight: Mapping[str, int] = MappingProxyType({})
    # Recommendations added 2026-04-30. Authoritative TCM-source-of-truth
    # for the LLM-composed share_diagnosis narrative — stops Jessica from
    # inventing diet/lifestyle suggestions. Each tuple is HK Cantonese
    # 口語. Empty tuples are valid (per-constitution config decision).
    recommended_diet: tuple[str, ...] = ()
    recommended_lifestyle: tuple[str, ...] = ()
    recommended_exercise: tuple[str, ...] = ()
    avoid: tuple[str, ...] = ()
    seek_help_if: tuple[str, ...] = ()


@dataclass(frozen=True)
class Product:
    name: str
    url: str
    description: str
    photo_url: str = ""  # Optional — /static/sales/*.jpg or absolute https URL


@dataclass(frozen=True)
class FlowStep:
    id: str
    action: str
    next: str | None
    script: str | None = None
    script_template: str | None = None
    image_ref: str | None = None
    caption: str | None = None
    await_type: str | None = None
    retry_script: str | None = None


@dataclass(frozen=True)
class SalesConfig:
    default_entry: bool
    escape_keywords: tuple[str, ...]
    language: str
    doctor_name_zh: str
    doctor_photo_url: str
    steps: tuple[FlowStep, ...]
    product: Product
    constitutions: tuple[ConstitutionType, ...]
    clinics: tuple[Clinic, ...]
    district_adjacency: Mapping[str, tuple[str, ...]]
    fallback: Mapping[str, str]
    disclaimers: Mapping[str, str]
    # Optional branding — defaults cover legacy configs without these fields.
    doctor_name_full_zh: str = ""
    clinic_brand_zh: str = ""
    clinic_brand_en: str = ""
    booking_url: str = ""

    # ── Lookup helpers (frozen dataclass can't cache, so linear scan — N is small) ──

    def step_by_id(self, step_id: str) -> FlowStep | None:
        for step in self.steps:
            if step.id == step_id:
                return step
        return None

    def clinic_by_id(self, clinic_id: str) -> Clinic | None:
        for clinic in self.clinics:
            if clinic.id == clinic_id:
                return clinic
        return None

    def constitution_by_key(self, key_zh: str) -> ConstitutionType | None:
        for constitution in self.constitutions:
            if constitution.key_zh == key_zh:
                return constitution
        return None


# ── Loader ────────────────────────────────────────────────────────────


def load_sales_config(path: Path = _DEFAULT_PATH) -> SalesConfig:
    """Load and validate the sales flow YAML.

    Raises:
        FileNotFoundError: config file does not exist.
        ValueError: required keys missing or invalid action types.
    """
    if not path.exists():
        raise FileNotFoundError(f"Sales config missing: {path}")

    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}

    sf = raw.get("sales_flow") or {}
    doctor = sf.get("doctor") or {}

    if not doctor.get("name_zh"):
        raise ValueError("sales_flow.doctor.name_zh is required")
    photo_url = doctor.get("photo_url")
    if not photo_url:
        raise ValueError("sales_flow.doctor.photo_url is required")
    _validate_url_or_static(photo_url, field="doctor.photo_url")

    steps_raw = raw.get("steps") or []
    if not steps_raw:
        raise ValueError("'steps' list is required and cannot be empty")

    steps = tuple(_parse_step(s) for s in steps_raw)
    _validate_step_graph(steps)

    product_raw = raw.get("product") or {}
    if not product_raw.get("name") or not product_raw.get("url"):
        raise ValueError("product.name and product.url are required")
    _validate_https_url(product_raw["url"], field="product.url")

    product_photo = product_raw.get("photo_url") or ""
    if product_photo:
        _validate_url_or_static(product_photo, field="product.photo_url")
    product = Product(
        name=product_raw["name"],
        url=product_raw["url"],
        description=product_raw.get("description", ""),
        photo_url=product_photo,
    )

    constitutions = tuple(
        _parse_constitution(k, v)
        for k, v in (raw.get("constitution_mapping") or {}).items()
    )

    clinics = tuple(_parse_clinic(c) for c in (raw.get("clinic_list") or []))

    adjacency = MappingProxyType(
        {
            k: tuple(v or [])
            for k, v in (raw.get("district_adjacency") or {}).items()
        }
    )

    clinic_brand = sf.get("clinic_brand") or {}

    return SalesConfig(
        default_entry=bool(sf.get("default_entry", False)),
        escape_keywords=tuple(sf.get("escape_keywords") or []),
        language=sf.get("language", "cantonese"),
        doctor_name_zh=doctor["name_zh"],
        doctor_photo_url=doctor["photo_url"],
        doctor_name_full_zh=doctor.get("name_full_zh") or doctor["name_zh"],
        clinic_brand_zh=clinic_brand.get("name_zh", ""),
        clinic_brand_en=clinic_brand.get("name_en", ""),
        booking_url=clinic_brand.get("booking_url", ""),
        steps=steps,
        product=product,
        constitutions=constitutions,
        clinics=clinics,
        district_adjacency=adjacency,
        fallback=MappingProxyType(dict(raw.get("fallback") or {})),
        disclaimers=MappingProxyType(dict(raw.get("disclaimers") or {})),
    )


# ── Internal parsers ──────────────────────────────────────────────────


def _parse_step(raw: dict[str, Any]) -> FlowStep:
    step_id = raw.get("id")
    if not step_id:
        raise ValueError(f"step missing id: {raw}")
    action = raw.get("action")
    if not action:
        raise ValueError(f"step {step_id!r} missing action")
    if action not in _VALID_ACTIONS:
        raise ValueError(
            f"step {step_id!r} has invalid action {action!r}; "
            f"expected one of {sorted(_VALID_ACTIONS)}"
        )
    return FlowStep(
        id=step_id,
        action=action,
        next=raw.get("next"),
        script=raw.get("script"),
        script_template=raw.get("script_template"),
        image_ref=raw.get("image_ref"),
        caption=raw.get("caption"),
        await_type=raw.get("await"),
        retry_script=raw.get("retry_script"),
    )


def _parse_constitution(key_zh: str, raw: dict[str, Any]) -> ConstitutionType:
    rec = raw.get("recommendations") or {}
    return ConstitutionType(
        key_zh=key_zh,
        en=raw.get("en", ""),
        characteristics=raw.get("characteristics", ""),
        tongue_signals=tuple(raw.get("tongue_signals") or []),
        q1_weight=MappingProxyType(dict(raw.get("q1_weight") or {})),
        q2_weight=MappingProxyType(dict(raw.get("q2_weight") or {})),
        q3_weight=MappingProxyType(dict(raw.get("q3_weight") or {})),
        q4_weight=MappingProxyType(dict(raw.get("q4_weight") or {})),
        q5_weight=MappingProxyType(dict(raw.get("q5_weight") or {})),
        recommended_diet=tuple(rec.get("diet") or []),
        recommended_lifestyle=tuple(rec.get("lifestyle") or []),
        recommended_exercise=tuple(rec.get("exercise") or []),
        avoid=tuple(rec.get("avoid") or []),
        seek_help_if=tuple(rec.get("seek_help_if") or []),
    )


def _parse_clinic(raw: dict[str, Any]) -> Clinic:
    clinic_id = raw.get("id")
    if not clinic_id:
        raise ValueError(f"clinic missing id: {raw}")
    return Clinic(
        id=clinic_id,
        name_zh=raw.get("name_zh", ""),
        district=raw.get("district", ""),
        address=raw.get("address", ""),
        phone=raw.get("phone", ""),
        opening_hours=MappingProxyType(dict(raw.get("opening_hours") or {})),
        name_brand_en=raw.get("name_brand_en", ""),
        email=raw.get("email", ""),
        booking_url=raw.get("booking_url", ""),
        mtr_hint=raw.get("mtr_hint", ""),
    )


def _validate_step_graph(steps: tuple[FlowStep, ...]) -> None:
    """Ensure every step's `next` points to a real step id (or is null)."""
    step_ids = {s.id for s in steps}
    for step in steps:
        if step.next is not None and step.next not in step_ids:
            raise ValueError(
                f"step {step.id!r} has next={step.next!r} which is not a defined step id"
            )


def _validate_https_url(value: str, *, field: str) -> None:
    """Reject anything but an https:// URL.

    Prevents javascript:, file://, ftp://, and missing-scheme values from
    being interpolated into user-facing scripts.
    """
    if not isinstance(value, str) or not value.startswith("https://"):
        raise ValueError(
            f"{field} must be an https:// URL; got {value!r}"
        )


def _validate_url_or_static(value: str, *, field: str) -> None:
    """Accept https:// URLs OR server-relative /static/ paths.

    The WhatsApp send layer expands /static/ paths to absolute URLs at
    dispatch time (see DRBABA_BASE_URL). Reject anything else.
    """
    if not isinstance(value, str):
        raise ValueError(f"{field} must be a string; got {type(value).__name__}")
    if value.startswith("https://") or value.startswith("/static/"):
        return
    raise ValueError(
        f"{field} must be an https:// URL or a /static/ path; got {value!r}"
    )
