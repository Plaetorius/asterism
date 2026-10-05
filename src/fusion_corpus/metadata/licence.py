"""The licence rule (PLAN §4, D5) as pure functions.

A stored copy is `shareable_fulltext` only if:
  1. a Creative Commons licence is deposited for *the same content version* as the copy (VoR licence for a
     VoR copy, AM licence for an AM copy; `unspecified`, `tdm` and `stm-asf` never match a copy),
  2. that licence's start date is known and ≤ today, and
  3. no non-CC licence is deposited for that same version (any start date: a conflicting deposit is a
     contradiction we don't resolve automatically).
Otherwise the copy is `shareable_quotes` when the work carries an active CC licence on some version or the copy
is an open-repository (B) or government (G) copy, and `private_only` in every other case.

An abstract inherits the VoR flag when the VoR carries an active CC licence, else it is `private_only`.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import date

SHAREABLE_FULLTEXT = "shareable_fulltext"
SHAREABLE_QUOTES = "shareable_quotes"
PRIVATE_ONLY = "private_only"

COPY_VERSIONS = frozenset({"vor", "am", "preprint", "report"})
OPEN_COPY_CLASSES = frozenset({"B", "G"})
CC_URL = re.compile(r"^https?://(www\.)?creativecommons\.org/(licenses|publicdomain)/", re.IGNORECASE)


@dataclass(frozen=True)
class Licence:
    url: str
    content_version: str  # crossref: vor | am | tdm | unspecified | stm-asf
    start: date | None

    @property
    def is_cc(self) -> bool:
        return is_cc(self.url)

    def to_json(self) -> dict:
        return {"url": self.url, "content_version": self.content_version,
                "start": self.start.isoformat() if self.start else None}


@dataclass(frozen=True)
class LicenceDecision:
    sharing: str
    reason: str
    licence_url: str | None = None


def is_cc(url: str | None) -> bool:
    return bool(url) and bool(CC_URL.match(url.strip()))


def _date_from_parts(parts: Sequence[int] | None) -> date | None:
    if not parts:
        return None
    y, m, d = (list(parts) + [1, 1])[:3]
    try:
        return date(int(y), int(m), int(d))
    except (TypeError, ValueError):
        return None


def from_crossref(raw: Iterable[dict] | None) -> tuple[Licence, ...]:
    """Crossref `license` array → Licences. The start is `start.date-parts` (falling back to `start.date-time`)."""
    out = []
    for item in raw or ():
        url = (item.get("URL") or "").strip()
        if not url:
            continue
        start_obj = item.get("start") or {}
        parts = (start_obj.get("date-parts") or [None])[0]
        start = _date_from_parts(parts)
        if start is None and start_obj.get("date-time"):
            start = date.fromisoformat(start_obj["date-time"][:10])
        out.append(Licence(url, (item.get("content-version") or "unspecified").lower(), start))
    return tuple(out)


def from_json(raw: Iterable[dict] | None) -> tuple[Licence, ...]:
    """Inverse of Licence.to_json (the `works.licences_json` column)."""
    return tuple(
        Licence(d["url"], d["content_version"], date.fromisoformat(d["start"]) if d.get("start") else None)
        for d in raw or ()
    )


def _active(lic: Licence, today: date) -> bool:
    return lic.start is not None and lic.start <= today


def cc_on_version(licences: Iterable[Licence], version: str, today: date) -> Licence | None:
    """The first active CC licence deposited for exactly this content version, if any."""
    for lic in licences:
        if lic.content_version == version and lic.is_cc and _active(lic, today):
            return lic
    return None


def conflicting_on_version(licences: Iterable[Licence], version: str) -> tuple[Licence, ...]:
    return tuple(lic for lic in licences if lic.content_version == version and not lic.is_cc)


def decide(licences: Sequence[Licence], copy_version: str, today: date,
           copy_class: str | None = None) -> LicenceDecision:
    """Sharing flag for a stored copy of `copy_version` ('vor' | 'am' | 'preprint' | 'report')."""
    if copy_version not in COPY_VERSIONS:
        raise ValueError(f"unknown copy version {copy_version!r}")
    cc = cc_on_version(licences, copy_version, today)
    conflicts = conflicting_on_version(licences, copy_version)
    if cc is not None and not conflicts:
        return LicenceDecision(SHAREABLE_FULLTEXT, f"cc_on_{copy_version}", cc.url)
    any_cc = next((lic for lic in licences if lic.is_cc and _active(lic, today)), None)
    if cc is not None:
        reason = f"cc_on_{copy_version}_conflicts_with:{conflicts[0].url}"
        return LicenceDecision(SHAREABLE_QUOTES, reason, cc.url)
    if any_cc is not None:
        return LicenceDecision(SHAREABLE_QUOTES, f"cc_only_on_{any_cc.content_version}", any_cc.url)
    if copy_class in OPEN_COPY_CLASSES:
        return LicenceDecision(SHAREABLE_QUOTES, f"open_copy_class_{copy_class}")
    future_cc = next((lic for lic in licences if lic.is_cc and lic.content_version == copy_version), None)
    if future_cc is not None:
        return LicenceDecision(PRIVATE_ONLY, f"cc_on_{copy_version}_not_yet_active", future_cc.url)
    return LicenceDecision(PRIVATE_ONLY, "no_cc_licence")


def abstract_licence(licences: Sequence[Licence], today: date) -> str:
    """An abstract inherits the VoR flag when the VoR carries an active CC licence, else private_only."""
    if cc_on_version(licences, "vor", today) is None:
        return PRIVATE_ONLY
    return decide(licences, "vor", today).sharing


@dataclass(frozen=True)
class LicenceSummary:
    """Work-level licence facts used for counts (PLAN §2: CC-VoR, CC-AM-only, conflicts)."""

    cc_vor: bool
    cc_vor_conflict: bool
    cc_am_only: bool


def summarise(licences: Sequence[Licence], today: date) -> LicenceSummary:
    cc_vor = cc_on_version(licences, "vor", today) is not None
    cc_am = cc_on_version(licences, "am", today) is not None
    return LicenceSummary(
        cc_vor=cc_vor,
        cc_vor_conflict=cc_vor and bool(conflicting_on_version(licences, "vor")),
        cc_am_only=cc_am and not cc_vor,
    )
