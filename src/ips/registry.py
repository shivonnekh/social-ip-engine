"""IP registry — single source of truth for per-IP configuration.

WHY THIS EXISTS
---------------
Per-IP config (IG account id, language, credential env var names, legacy
name aliases, voice/brand content settings) used to be duplicated across
four hardcoded dicts:

  * src/channels/comment_rules.py  ``_ACCOUNT_LANGUAGE``
  * src/notion_sync.py             ``_IP_ACCOUNT``
  * src/channels/meta_client.py    ``_ACCOUNT_CREDS_ENV``
  * src/web.py                     inline account id + persona wiring

Adding an IP meant touching all four (and forgetting one silently broke
routing — see the language-gate incident class in comment_rules). Now each
IP is ONE directory::

    data/ips/<id>/ip.json        # this registry's schema
    data/ips/<id>/persona.json   # DM persona (PersonaAgent / profile loaders)

Every ``ip.json`` is loaded and schema-validated at import time; a bad or
missing field fails fast with an error naming the file and field, so a
misconfigured IP can never boot into production half-wired.

All lookups are pure functions over immutable records. Inactive IPs
(``"active": false``) still load (so their config is inspectable) but are
excluded from every lookup — flipping the flag retires an IP everywhere
at once.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Final, Mapping

_REPO_ROOT: Final[Path] = Path(__file__).resolve().parent.parent.parent
IPS_DIR: Final[Path] = _REPO_ROOT / "data" / "ips"

_VALID_LANGUAGES: Final[frozenset[str]] = frozenset({"en", "yue"})
_VALID_CHANNEL_MODES: Final[frozenset[str]] = frozenset({"canned", "persona", "off"})


class IPRegistryError(RuntimeError):
    """Raised when data/ips/*/ip.json is missing, malformed, or inconsistent."""


@dataclass(frozen=True)
class ChannelConfig:
    """One platform binding for an IP (e.g. its Instagram business account).

    ``token_env`` / ``user_id_env`` are the NAMES of the environment
    variables holding the credentials — never the secrets themselves.
    They intentionally preserve the pre-registry production var names
    (e.g. ``IG_PAGE_ACCESS_TOKEN_JACKIE``) so no deployed env var ever
    needs renaming.
    """

    account_id: str
    token_env: str
    user_id_env: str
    comments: str  # "canned" | "persona" | "off"
    dms: str       # "canned" | "persona" | "off"


@dataclass(frozen=True)
class ContentConfig:
    """Content-factory settings (voice + infographic branding) for an IP."""

    voice_id: str
    speed: float
    pitch: float
    tts_language: str
    infographic_brand_slug: str


@dataclass(frozen=True)
class IPRecord:
    """Immutable, validated view of one data/ips/<id>/ip.json."""

    id: str
    display_name: str
    language: str  # "en" | "yue"
    active: bool
    aliases: tuple[str, ...]
    channels: Mapping[str, ChannelConfig]  # read-only (MappingProxyType)
    content: ContentConfig
    root_dir: Path  # data/ips/<id>

    @property
    def persona_path(self) -> Path:
        """Path to this IP's DM persona JSON (data/ips/<id>/persona.json)."""
        return self.root_dir / "persona.json"

    def matches_name(self, name: str) -> bool:
        """True when ``name`` contains this IP's id or any alias.

        Substring containment (not equality) mirrors the legacy
        notion_sync matcher: Notion IP Registry titles look like
        "Jackie Chan TCM (jackiechan.tcm)".
        """
        haystack = (name or "").strip().lower()
        if not haystack:
            return False
        return any(needle in haystack for needle in (self.id, *self.aliases))


# ---------------------------------------------------------------------------
# Loading + validation
# ---------------------------------------------------------------------------


def _fail(file: Path, message: str) -> IPRegistryError:
    return IPRegistryError(f"{file}: {message}")


def _require(spec: dict, key: str, kind: type | tuple[type, ...], file: Path) -> object:
    if key not in spec:
        raise _fail(file, f"missing required field {key!r}")
    value = spec[key]
    if not isinstance(value, kind):
        raise _fail(file, f"field {key!r} must be {kind}, got {type(value).__name__}")
    return value


def _parse_channel(name: str, spec: object, file: Path) -> ChannelConfig:
    if not isinstance(spec, dict):
        raise _fail(file, f"channels.{name} must be an object")
    for key in ("account_id", "token_env", "user_id_env", "comments", "dms"):
        if key not in spec or not isinstance(spec[key], str) or not spec[key].strip():
            raise _fail(file, f"channels.{name}.{key} must be a non-empty string")
    for mode_key in ("comments", "dms"):
        if spec[mode_key] not in _VALID_CHANNEL_MODES:
            raise _fail(
                file,
                f"channels.{name}.{mode_key} must be one of "
                f"{sorted(_VALID_CHANNEL_MODES)}, got {spec[mode_key]!r}",
            )
    return ChannelConfig(
        account_id=spec["account_id"].strip(),
        token_env=spec["token_env"].strip(),
        user_id_env=spec["user_id_env"].strip(),
        comments=spec["comments"],
        dms=spec["dms"],
    )


def _parse_content(spec: object, file: Path) -> ContentConfig:
    if not isinstance(spec, dict):
        raise _fail(file, "field 'content' must be an object")
    for key in ("voice_id", "tts_language", "infographic_brand_slug"):
        if key not in spec or not isinstance(spec[key], str) or not spec[key].strip():
            raise _fail(file, f"content.{key} must be a non-empty string")
    for key in ("speed", "pitch"):
        if key not in spec or isinstance(spec[key], bool) \
                or not isinstance(spec[key], (int, float)):
            raise _fail(file, f"content.{key} must be a number")
    return ContentConfig(
        voice_id=spec["voice_id"].strip(),
        speed=float(spec["speed"]),
        pitch=float(spec["pitch"]),
        tts_language=spec["tts_language"].strip(),
        infographic_brand_slug=spec["infographic_brand_slug"].strip(),
    )


def _parse_aliases(value: object, file: Path) -> tuple[str, ...]:
    if not isinstance(value, list) or not all(isinstance(a, str) for a in value):
        raise _fail(file, "field 'aliases' must be a list of strings")
    aliases = tuple(a.strip().lower() for a in value if a.strip())
    if len(set(aliases)) != len(aliases):
        raise _fail(file, "field 'aliases' contains duplicates")
    return aliases


def _parse_ip(ip_dir: Path) -> IPRecord:
    file = ip_dir / "ip.json"
    try:
        spec = json.loads(file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise _fail(file, f"cannot read/parse JSON: {exc}") from exc
    if not isinstance(spec, dict):
        raise _fail(file, "root must be a JSON object")

    ip_id = str(_require(spec, "id", str, file)).strip().lower()
    if ip_id != ip_dir.name:
        raise _fail(file, f"field 'id' ({ip_id!r}) must match directory name {ip_dir.name!r}")

    language = str(_require(spec, "language", str, file))
    if language not in _VALID_LANGUAGES:
        raise _fail(
            file,
            f"field 'language' must be one of {sorted(_VALID_LANGUAGES)}, got {language!r}",
        )

    channels_spec = _require(spec, "channels", dict, file)
    channels = {
        str(name): _parse_channel(str(name), chan, file)
        for name, chan in channels_spec.items()
    }
    if not channels:
        raise _fail(file, "field 'channels' must define at least one channel")

    persona = ip_dir / "persona.json"
    if not persona.is_file():
        raise _fail(file, f"companion persona.json not found at {persona}")

    return IPRecord(
        id=ip_id,
        display_name=str(_require(spec, "display_name", str, file)).strip(),
        language=language,
        active=bool(_require(spec, "active", bool, file)),
        aliases=_parse_aliases(_require(spec, "aliases", list, file), file),
        channels=MappingProxyType(channels),
        content=_parse_content(_require(spec, "content", dict, file), file),
        root_dir=ip_dir,
    )


def _check_cross_ip_uniqueness(records: tuple[IPRecord, ...], root: Path) -> None:
    seen_accounts: dict[str, str] = {}
    seen_names: dict[str, str] = {}
    for ip in records:
        for name in (ip.id, *ip.aliases):
            if name in seen_names:
                raise IPRegistryError(
                    f"{root}: name/alias {name!r} used by both "
                    f"{seen_names[name]!r} and {ip.id!r}"
                )
            seen_names[name] = ip.id
        for channel in ip.channels.values():
            if channel.account_id in seen_accounts:
                raise IPRegistryError(
                    f"{root}: account id {channel.account_id!r} claimed by both "
                    f"{seen_accounts[channel.account_id]!r} and {ip.id!r}"
                )
            seen_accounts[channel.account_id] = ip.id


def load_registry(root: Path | None = None) -> tuple[IPRecord, ...]:
    """Load + validate every ``<root>/*/ip.json``. Deterministic (sorted by id).

    Raises IPRegistryError naming the offending file/field on ANY problem —
    a partially valid registry is never returned.
    """
    base = root if root is not None else IPS_DIR
    ip_files = sorted(base.glob("*/ip.json")) if base.is_dir() else []
    if not ip_files:
        raise IPRegistryError(f"{base}: no ip.json files found — registry is empty")
    records = tuple(_parse_ip(f.parent) for f in ip_files)
    _check_cross_ip_uniqueness(records, base)
    return records


# Loaded once at import — fail fast on a bad registry before serving traffic.
_RECORDS: Final[tuple[IPRecord, ...]] = load_registry()


# ---------------------------------------------------------------------------
# Pure lookups
# ---------------------------------------------------------------------------


def all_ips(records: tuple[IPRecord, ...] | None = None) -> tuple[IPRecord, ...]:
    """Every registered IP (including inactive ones), sorted by id."""
    return records if records is not None else _RECORDS


def _active(records: tuple[IPRecord, ...] | None) -> tuple[IPRecord, ...]:
    return tuple(ip for ip in all_ips(records) if ip.active)


def get(ip_id: str, records: tuple[IPRecord, ...] | None = None) -> IPRecord:
    """The IP with this exact id. Raises KeyError for unknown ids."""
    wanted = (ip_id or "").strip().lower()
    for ip in all_ips(records):
        if ip.id == wanted:
            return ip
    raise KeyError(f"unknown IP id {ip_id!r} — known: {[i.id for i in all_ips(records)]}")


def for_account(
    account_id: str | None, records: tuple[IPRecord, ...] | None = None,
) -> IPRecord | None:
    """The active IP owning this platform account id, or None."""
    if not account_id:
        return None
    for ip in _active(records):
        if any(c.account_id == account_id for c in ip.channels.values()):
            return ip
    return None


def account_language(
    account_id: str | None, records: tuple[IPRecord, ...] | None = None,
) -> str:
    """Expected content language for an account ("" when unregistered).

    Drop-in replacement for the old ``_ACCOUNT_LANGUAGE.get(id, "")`` gate
    in comment_rules — unknown accounts return "" (no language gate).
    """
    ip = for_account(account_id, records)
    return ip.language if ip is not None else ""


def token_envs_for_account(
    account_id: str | None, records: tuple[IPRecord, ...] | None = None,
) -> tuple[str, str] | None:
    """(token_env_name, user_id_env_name) for an account id, or None.

    Returns env var NAMES, not secrets. None means the caller should fall
    back to its platform-default credentials (legacy meta_client behaviour).
    """
    if not account_id:
        return None
    for ip in _active(records):
        for channel in ip.channels.values():
            if channel.account_id == account_id:
                return (channel.token_env, channel.user_id_env)
    return None


def resolve_ip_name(
    name_or_alias: str, records: tuple[IPRecord, ...] | None = None,
) -> IPRecord | None:
    """Resolve a human/Notion IP name (or legacy alias) to an active IP.

    Case-insensitive substring containment of the id/alias in the given
    name — mirrors the legacy notion_sync matcher, so titles like
    "Jackie Chan TCM (jackiechan.tcm)" and legacy names like "jessica"
    both resolve. Returns None when nothing matches.
    """
    for ip in _active(records):
        if ip.matches_name(name_or_alias):
            return ip
    return None
