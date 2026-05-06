"""Multilingual company-name → ticker lookup.

Loads aliases from data/ticker_aliases.csv at process start. The CSV is
case-insensitive and supports Korean / Japanese / Chinese / English. Unknown
queries fall through to upper-case (the existing yfinance path).
"""

from __future__ import annotations

import csv
import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)

_DEFAULT_PATH = Path(__file__).resolve().parent.parent / "data" / "ticker_aliases.csv"

_TICKER_RE = re.compile(r"^[A-Z]{1,5}(?:[.\-][A-Z]{1,3})?$")

# Words to strip when the user types natural-language phrases like
# '아마존 주가', '테슬라 어때', "what's the AAPL price", etc.
# Sorted longest-first so multi-word phrases peel off before single words.
_NOISE_WORDS = sorted([
    # Korean
    "주가", "가격", "시세", "주식", "정보", "분석", "어때", "어때요", "어떄",
    "어떻게", "어떤가", "알려줘", "알려주세요", "보여줘", "괜찮아", "어떨까",
    # English
    "what is", "what's", "tell me about", "info on", "info",
    "price", "stock", "shares", "share", "current", "today",
    "how is", "how's", "right now", "now",
    # Japanese
    "株価", "価格", "情報", "教えて", "どう",
    # Chinese
    "股价", "价格", "怎么样", "信息", "如何",
], key=len, reverse=True)


class TickerLookup:
    def __init__(self, csv_path: Path | str | None = None) -> None:
        path = Path(csv_path) if csv_path else _DEFAULT_PATH
        self._aliases: dict[str, str] = {}
        if path.exists():
            self._load(path)
        else:
            logger.warning("ticker alias CSV not found at %s — lookup will fall back to upper-case only", path)

    def _load(self, path: Path) -> None:
        with path.open(newline="", encoding="utf-8") as f:
            # Skip blank lines and comment lines (starting with '#')
            cleaned = (line for line in f if line.strip() and not line.lstrip().startswith("#"))
            reader = csv.DictReader(cleaned)
            for row in reader:
                alias = (row.get("alias") or "").strip().lower()
                ticker = (row.get("ticker") or "").strip().upper()
                if alias and ticker:
                    self._aliases[alias] = ticker
        unique_tickers = len(set(self._aliases.values()))
        logger.info("loaded %d ticker aliases covering %d unique tickers", len(self._aliases), unique_tickers)

    def resolve(self, query: str) -> str:
        """Return a ticker symbol for the query, or the upper-cased query if no match.

        Resolution order (most-specific first):
          1. Whole-string alias match  ('테슬라' → TSLA)
          2. Whitespace-collapsed alias ('  apple  ' → AAPL)
          3. Strip noise words like '주가/가격/어때/price/stock' then re-try alias
             ('아마존 주가' → '아마존' → AMZN)
          4. Word-by-word alias scan, first hit wins
             ('what is NVDA price' → 'NVDA' → NVDA)
          5. Already-uppercase ticker pattern → trust as-is
          6. Fallback: upper-cased first token (yfinance will fail if unknown)
        """
        cleaned = query.strip()
        if not cleaned:
            return ""

        key = cleaned.lower()

        # 1. Whole-string alias
        if key in self._aliases:
            return self._aliases[key]

        # 2. Collapse whitespace
        compact = re.sub(r"\s+", " ", key)
        if compact in self._aliases:
            return self._aliases[compact]

        # 3. Strip noise words then retry — handles '아마존 주가', '테슬라 어때'
        stripped = compact
        for w in _NOISE_WORDS:
            if w in stripped:
                stripped = stripped.replace(w, " ")
        stripped = re.sub(r"\s+", " ", stripped).strip(" ?!.,~")
        if stripped and stripped != compact:
            if stripped in self._aliases:
                return self._aliases[stripped]

        # 4. Word-by-word alias scan
        # Splits on whitespace AND CJK punctuation. First match wins.
        for token in re.split(r"[\s,/·]+", stripped or compact):
            token = token.strip(" ?!.,~()[]")
            if not token:
                continue
            # Strip trailing Korean topic markers / object particles attached to
            # a Latin-letter root: "AMD는?" → "AMD", "TSLA가" → "TSLA".
            stripped_kr = re.sub(r"^([a-zA-Z\-.]+)(는|은|이|가|을|를|도|만)$", r"\1", token)
            if stripped_kr in self._aliases:
                return self._aliases[stripped_kr]
            if token in self._aliases:
                return self._aliases[token]
            # bare uppercase ticker pattern inside the token
            up = stripped_kr.upper() if stripped_kr != token else token.upper()
            if _TICKER_RE.match(up):
                return up

        # 5. Already-uppercase ticker (user typed in caps)
        first_token = cleaned.split()[0]
        first_token_kr = re.sub(r"^([a-zA-Z\-.]+)(는|은|이|가|을|를|도|만)\??$", r"\1", first_token)
        if _TICKER_RE.match(first_token_kr.upper()):
            return first_token_kr.upper()

        # 6. Fallback
        return first_token.upper()
