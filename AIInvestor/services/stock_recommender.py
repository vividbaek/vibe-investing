"""사주 → 오행 → 종목 5선 추천기.

Loads `data/stock_elements.csv`, picks stocks whose primary element matches
the user's favored elements for today, with sector diversification.
"""

from __future__ import annotations

import csv
import logging
import random
from dataclasses import dataclass, field
from pathlib import Path

from .saju_engine import SajuProfile, TodaySaju, favored_elements

logger = logging.getLogger(__name__)

_CSV_PATH = Path(__file__).resolve().parent.parent / "data" / "stock_elements.csv"


@dataclass(frozen=True)
class StockEntry:
    ticker: str
    name: str
    sector: str
    industry: str
    business_summary: str
    brand_color: str
    primary_element: str
    secondary_element: str | None
    source: str


@dataclass
class _Cache:
    rows: list[StockEntry] = field(default_factory=list)
    by_element: dict[str, list[StockEntry]] = field(default_factory=dict)
    loaded: bool = False


_cache = _Cache()


def _load_if_needed() -> None:
    if _cache.loaded:
        return
    if not _CSV_PATH.exists():
        logger.warning("stock_elements.csv not found at %s", _CSV_PATH)
        _cache.loaded = True
        return

    rows: list[StockEntry] = []
    with _CSV_PATH.open(encoding="utf-8") as f:
        # Strip comment + blank lines (CSV doesn't natively support them).
        cleaned = (ln for ln in f if ln.strip() and not ln.lstrip().startswith("#"))
        reader = csv.DictReader(cleaned)
        for r in reader:
            try:
                rows.append(StockEntry(
                    ticker=r["ticker"].strip().upper(),
                    name=r.get("name", "").strip(),
                    sector=r.get("sector", "").strip(),
                    industry=r.get("industry", "").strip(),
                    business_summary=r.get("business_summary", "").strip(),
                    brand_color=r.get("brand_color", "").strip(),
                    primary_element=r["primary_element"].strip().lower(),
                    secondary_element=(r.get("secondary_element") or "").strip().lower() or None,
                    source=r.get("source", "").strip(),
                ))
            except KeyError as e:
                logger.warning("stock_elements.csv row missing column %s: %s", e, r)

    _cache.rows = rows
    _cache.by_element = {}
    for entry in rows:
        _cache.by_element.setdefault(entry.primary_element, []).append(entry)
    _cache.loaded = True
    logger.info("Loaded %d stock-element entries", len(rows))


def all_entries() -> list[StockEntry]:
    _load_if_needed()
    return list(_cache.rows)


def by_element(element: str) -> list[StockEntry]:
    _load_if_needed()
    return list(_cache.by_element.get(element, []))


def recommend_for_today(
    profile: SajuProfile,
    today: TodaySaju,
    *,
    n: int = 5,
    seed: int | None = None,
    diversify_sectors: bool = True,
) -> list[StockEntry]:
    """Pick `n` stocks aligned with today's favored elements.

    Determinism: when `seed` is provided we shuffle deterministically so that
    the same (profile, today, seed) returns the same picks (cacheable).
    """
    _load_if_needed()
    favored = favored_elements(profile.my_element, today.relation)
    # Build a pool weighted by the order of favored_elements
    rng = random.Random(seed)

    picks: list[StockEntry] = []
    seen_tickers: set[str] = set()
    seen_sectors: set[str] = set()

    for elem in favored:
        if elem is None:
            continue
        candidates = list(_cache.by_element.get(elem, []))
        rng.shuffle(candidates)
        for c in candidates:
            if c.ticker in seen_tickers:
                continue
            if diversify_sectors and c.sector and c.sector in seen_sectors:
                # Allow re-pick from same sector only after we've exhausted unique ones
                continue
            picks.append(c)
            seen_tickers.add(c.ticker)
            if c.sector:
                seen_sectors.add(c.sector)
            if len(picks) >= n:
                return picks

    # Relaxed pass — drop sector constraint
    if len(picks) < n:
        for elem in favored:
            if elem is None:
                continue
            for c in _cache.by_element.get(elem, []):
                if c.ticker in seen_tickers:
                    continue
                picks.append(c)
                seen_tickers.add(c.ticker)
                if len(picks) >= n:
                    return picks

    # Final fallback — fill from any element
    if len(picks) < n:
        pool = [c for c in _cache.rows if c.ticker not in seen_tickers]
        rng.shuffle(pool)
        for c in pool:
            picks.append(c)
            seen_tickers.add(c.ticker)
            if len(picks) >= n:
                break

    return picks


# ─────────────────────────────────────────────────────────────────────────────
# Reasoning / recommendation rationale (human-readable)
# ─────────────────────────────────────────────────────────────────────────────
_ELEMENT_RATIONALE_KO = {
    "wood": "성장·생명력 (헬스케어·바이오·농업)",
    "fire": "에너지·변화 (AI·SW·에너지·EV)",
    "earth": "안정·기반 (REIT·소비재·인프라)",
    "metal": "정밀·결단 (금융·반도체·방산)",
    "water": "흐름·정보 (인터넷·통신·미디어)",
}


def explain_pick(entry: StockEntry, profile: SajuProfile, today: TodaySaju) -> str:
    """One-line rationale for a stock pick."""
    elem_kr = _ELEMENT_RATIONALE_KO.get(entry.primary_element, entry.primary_element)
    return (
        f"{entry.ticker} · {entry.name} — {elem_kr}. "
        f"오늘 일진({today.today_element})과 일간({profile.my_element})의 "
        f"{today.relation_label} 흐름에 부합."
    )
