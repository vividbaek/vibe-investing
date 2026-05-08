"""§3 — Deterministic daily fortune-stock match.

Per work-priority-and-prompts-v1.0-ko.md §3.4. Given (birth_date, birth_time,
today_kst), produce:
  - lucky_number (0-9)
  - 1 free stock + 2 locked stocks across 3 risk tiers (low/medium/high)
  - fortune_seed (16-hex prefix of SHA-256)

Pure function — no IO, no side effects. Same input → same output, always.
This sits *parallel* to the 五行-based saju_engine: that one uses 일주 + 일진
to pick 5 stocks; this one uses birth seed + risk tiers to pick 3 with hard
determinism for daily-free / locked gating.
"""

from __future__ import annotations

import hashlib
from typing import TypedDict


class StockPick(TypedDict):
    ticker: str
    risk: str          # "low" | "medium" | "high"


class FortuneResult(TypedDict):
    lucky_number: int          # 0–9
    free: StockPick
    locked: list[StockPick]    # always 2 entries (the 2 non-free risk tiers)
    fortune_seed: str          # 16-hex prefix


# ─────────────────────────────────────────────────────────────────────────────
# Risk classification
# ─────────────────────────────────────────────────────────────────────────────
def classify_risk(beta: float | None) -> str:
    """yfinance .info["beta"] → low / medium / high.

    None or beta < 1.0  → "low"
    1.0 ≤ beta < 1.5    → "medium"
    1.5 ≤ beta          → "high"
    """
    if beta is None or beta < 1.0:
        return "low"
    if beta < 1.5:
        return "medium"
    return "high"


def build_risk_pool(hot_tickers: list[dict]) -> dict[str, list[str]]:
    """Group hot-ticker entries by risk tier. Caller passes:
       [{"ticker": "AAPL", "beta": 1.2}, ...]

    Returns {"low": [tickers...], "medium": [...], "high": [...]}.
    Raises ValueError if any tier has fewer than 5 tickers — protects the
    selection RNG from mod-by-tiny-N collapsing variety.
    """
    pool: dict[str, list[str]] = {"low": [], "medium": [], "high": []}
    for entry in hot_tickers:
        ticker = entry.get("ticker", "").strip().upper()
        if not ticker:
            continue
        tier = classify_risk(entry.get("beta"))
        pool[tier].append(ticker)
    for tier, tickers in pool.items():
        if len(tickers) < 5:
            raise ValueError(
                f"insufficient pool for {tier} risk tier "
                f"(have {len(tickers)}, need ≥5)"
            )
    return pool


# ─────────────────────────────────────────────────────────────────────────────
# Deterministic selection
# ─────────────────────────────────────────────────────────────────────────────
def _seed(birth_date: str, birth_time: str, today_kst: str) -> str:
    """SHA-256 seed from user × today. Returns full hex digest."""
    h = hashlib.sha256(f"{birth_date}{birth_time}{today_kst}".encode("utf-8"))
    return h.hexdigest()


def select_daily_free_stock(
    birth_date: str,
    birth_time: str,
    today_kst: str,
    risk_pool: dict[str, list[str]],
) -> FortuneResult:
    """Deterministic daily fortune selection.

    Args:
      birth_date: YYYYMMDD (8 digits)
      birth_time: HHMM (4 digits) or "9999" if unknown
      today_kst:  YYYYMMDD KST date
      risk_pool:  output of build_risk_pool()

    Returns:
      FortuneResult with lucky_number, 1 free pick, 2 locked picks, seed prefix.
    """
    seed = _seed(birth_date, birth_time, today_kst)

    lucky_number = int(seed[0:2], 16) % 10
    free_risk = ["low", "medium", "high"][int(seed[2:4], 16) % 3]
    free_idx = int(seed[4:8], 16) % len(risk_pool[free_risk])
    free_ticker = risk_pool[free_risk][free_idx]

    locked_risks = [r for r in ("low", "medium", "high") if r != free_risk]
    locked: list[StockPick] = []
    for i, r in enumerate(locked_risks):
        offset = 8 + i * 4
        idx = int(seed[offset: offset + 4], 16) % len(risk_pool[r])
        locked.append({"ticker": risk_pool[r][idx], "risk": r})

    return {
        "lucky_number": lucky_number,
        "free": {"ticker": free_ticker, "risk": free_risk},
        "locked": locked,
        "fortune_seed": seed[:16],
    }
