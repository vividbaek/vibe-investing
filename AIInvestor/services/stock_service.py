"""Stock data lookup via yfinance."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import yfinance as yf

logger = logging.getLogger(__name__)


@dataclass
class StockSnapshot:
    ticker: str
    name: str
    sector: str | None
    industry: str | None
    summary: str | None
    currency: str | None
    price: float | None
    market_cap: float | None
    pe_ratio: float | None
    forward_pe: float | None
    pb_ratio: float | None
    dividend_yield: float | None
    profit_margin: float | None
    return_on_equity: float | None
    debt_to_equity: float | None
    earnings_growth: float | None
    revenue_growth: float | None
    fifty_two_week_low: float | None
    fifty_two_week_high: float | None
    price_change_1m_pct: float | None
    price_change_6m_pct: float | None
    price_change_1y_pct: float | None

    def to_prompt_block(self) -> str:
        def fmt(value: Any, suffix: str = "") -> str:
            if value is None:
                return "N/A"
            if isinstance(value, float):
                return f"{value:,.2f}{suffix}"
            return f"{value}{suffix}"

        return (
            f"Ticker: {self.ticker}\n"
            f"Name: {self.name}\n"
            f"Sector: {self.sector or 'N/A'} / Industry: {self.industry or 'N/A'}\n"
            f"Currency: {self.currency or 'N/A'}\n"
            f"Price: {fmt(self.price)}\n"
            f"Market Cap: {fmt(self.market_cap)}\n"
            f"PE: {fmt(self.pe_ratio)} | Forward PE: {fmt(self.forward_pe)} | PB: {fmt(self.pb_ratio)}\n"
            f"Dividend Yield: {fmt(self.dividend_yield)}\n"
            f"Profit Margin: {fmt(self.profit_margin)} | ROE: {fmt(self.return_on_equity)}\n"
            f"Debt/Equity: {fmt(self.debt_to_equity)}\n"
            f"Earnings Growth: {fmt(self.earnings_growth)} | Revenue Growth: {fmt(self.revenue_growth)}\n"
            f"52W Low/High: {fmt(self.fifty_two_week_low)} / {fmt(self.fifty_two_week_high)}\n"
            f"Price change 1M: {fmt(self.price_change_1m_pct, '%')} | "
            f"6M: {fmt(self.price_change_6m_pct, '%')} | "
            f"1Y: {fmt(self.price_change_1y_pct, '%')}\n"
            f"Business summary: {(self.summary or 'N/A')[:600]}"
        )


class StockServiceError(Exception):
    pass


class StockService:
    """Fetches a fundamental + price snapshot for a ticker."""

    def get_snapshot(self, query: str) -> StockSnapshot:
        ticker_symbol = self._normalize(query)
        logger.info("Fetching snapshot for %s", ticker_symbol)

        ticker = yf.Ticker(ticker_symbol)
        info = self._safe_info(ticker)

        if not info or not info.get("symbol"):
            raise StockServiceError(
                f"Could not find ticker '{ticker_symbol}'. Try a different symbol."
            )

        history = ticker.history(period="1y", auto_adjust=False)
        price = self._latest_price(history, info)
        changes = self._price_changes(history)

        return StockSnapshot(
            ticker=ticker_symbol,
            name=info.get("longName") or info.get("shortName") or ticker_symbol,
            sector=info.get("sector"),
            industry=info.get("industry"),
            summary=info.get("longBusinessSummary"),
            currency=info.get("currency"),
            price=price,
            market_cap=self._maybe_float(info.get("marketCap")),
            pe_ratio=self._maybe_float(info.get("trailingPE")),
            forward_pe=self._maybe_float(info.get("forwardPE")),
            pb_ratio=self._maybe_float(info.get("priceToBook")),
            dividend_yield=self._maybe_float(info.get("dividendYield")),
            profit_margin=self._maybe_float(info.get("profitMargins")),
            return_on_equity=self._maybe_float(info.get("returnOnEquity")),
            debt_to_equity=self._maybe_float(info.get("debtToEquity")),
            earnings_growth=self._maybe_float(info.get("earningsGrowth")),
            revenue_growth=self._maybe_float(info.get("revenueGrowth")),
            fifty_two_week_low=self._maybe_float(info.get("fiftyTwoWeekLow")),
            fifty_two_week_high=self._maybe_float(info.get("fiftyTwoWeekHigh")),
            price_change_1m_pct=changes.get("1m"),
            price_change_6m_pct=changes.get("6m"),
            price_change_1y_pct=changes.get("1y"),
        )

    @staticmethod
    def _normalize(query: str) -> str:
        return query.strip().upper().split()[0]

    @staticmethod
    def _safe_info(ticker: yf.Ticker) -> dict[str, Any]:
        try:
            return ticker.info or {}
        except Exception as exc:
            logger.warning("yfinance .info failed: %s", exc)
            return {}

    @staticmethod
    def _maybe_float(value: Any) -> float | None:
        try:
            if value is None:
                return None
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _latest_price(history, info: dict[str, Any]) -> float | None:
        if history is not None and not history.empty:
            return float(history["Close"].iloc[-1])
        for key in ("currentPrice", "regularMarketPrice", "previousClose"):
            value = info.get(key)
            if value is not None:
                try:
                    return float(value)
                except (TypeError, ValueError):
                    continue
        return None

    @staticmethod
    def _price_changes(history) -> dict[str, float | None]:
        if history is None or history.empty:
            return {"1m": None, "6m": None, "1y": None}

        closes = history["Close"]
        latest = float(closes.iloc[-1])
        windows = {"1m": 21, "6m": 126, "1y": 252}
        out: dict[str, float | None] = {}
        for label, days in windows.items():
            if len(closes) > days:
                ref = float(closes.iloc[-days - 1])
                out[label] = (latest / ref - 1.0) * 100.0 if ref else None
            else:
                out[label] = None
        return out
