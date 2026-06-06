# -*- coding: utf-8 -*-
"""
ARDS-X — Data Feed
==================
두 개의 무료 소스만 사용한다 (API 키 불필요):

  1) yfinance         — 지수 / 빅테크 / AI 인프라 가격
  2) FRED 무료 CSV    — 거시 지표 (수익률 곡선, Sahm, HY OAS, NFCI, 청구건수 …)
                        https://fred.stlouisfed.org/graph/fredgraph.csv?id=<ID>

네트워크가 막힌 환경(오프라인/CI)에서는 캐시(data/cache/*.csv)를 사용하고,
그래도 없으면 명시적으로 None 을 반환해 상위 로직이 '추정치(estimated)' 로
표시하도록 한다. (절대 조용히 가짜 숫자를 만들지 않는다.)
"""

import io
import os
import subprocess
import sys
import tempfile
import time
import urllib.request

import pandas as pd

# Azure Functions: 배포 패키지는 read-only → /tmp 로 캐시. Function 인스턴스
# 수명 동안만 유지되지만 yfinance batch 는 매 cron 새로 받으므로 무해.
CACHE_DIR = os.path.join(tempfile.gettempdir(), "vibe_ards_cache")
FRED_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={id}"
UA = "Mozilla/5.0 (ARDS-X regime classifier; research/educational)"


def _ensure_cache():
    os.makedirs(CACHE_DIR, exist_ok=True)


def _looks_like_csv(raw):
    """FRED 정상 응답인지 검증. 504 게이트웨이/HTML 에러 페이지를 캐시에 쓰지 않기 위함."""
    if not raw or len(raw) < 20:
        return False
    head = raw[:200].lstrip().lower()
    if head.startswith(b"<"):           # HTML 에러 페이지
        return False
    return b"," in raw[:200]


def _http_get(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def _curl_get(url, timeout=12):
    """urllib 이 막히는 환경(LibreSSL/방화벽)을 위한 curl 폴백."""
    try:
        p = subprocess.run(
            ["curl", "-sS", "--max-time", str(timeout), "-A", UA, url],
            capture_output=True, timeout=timeout + 5,
        )
        return p.stdout if p.returncode == 0 else None
    except Exception:
        return None


def _fetch_validated(url, retries=2, fast_timeout=10):
    """
    urllib → curl 순으로 빠르게 시도하고, 정상 CSV 인 응답만 반환. 실패 시 None.
    FRED 가 다운(504)이어도 전체 실행이 멈추지 않도록 짧은 타임아웃을 쓴다.
    (yield-curve·credit 등 핵심 팩터는 yfinance 로 대체되므로 FRED 는 best-effort.)
    """
    for attempt in range(retries):
        for getter in (_http_get, _curl_get):
            try:
                raw = getter(url, timeout=fast_timeout)
            except Exception:
                raw = None
            if _looks_like_csv(raw):
                return raw
        time.sleep(1)
    return None


# ---------------------------------------------------------------------------
# FRED
# ---------------------------------------------------------------------------
def fred_series(series_id, use_cache=True):
    """단일 FRED 시리즈를 pandas Series(날짜 인덱스)로 반환. 실패 시 None."""
    _ensure_cache()
    cache_path = os.path.join(CACHE_DIR, f"fred_{series_id}.csv")
    raw = _fetch_validated(FRED_URL.format(id=series_id))
    if _looks_like_csv(raw):
        with open(cache_path, "wb") as f:        # 검증된 CSV 만 캐시에 기록
            f.write(raw)
    else:                                        # 네트워크/504 실패 → 캐시 폴백
        sys.stderr.write(f"[fred] {series_id} 라이브 실패; 캐시 시도\n")
        raw = None
        if use_cache and os.path.exists(cache_path):
            with open(cache_path, "rb") as f:
                raw = f.read()
    if raw is None:
        return None
    try:
        df = pd.read_csv(io.BytesIO(raw))
        # FRED CSV 는 첫 열이 날짜(observation_date 또는 DATE), 둘째 열이 값
        date_col = df.columns[0]
        val_col = df.columns[1]
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
        df[val_col] = pd.to_numeric(df[val_col], errors="coerce")
        s = df.dropna(subset=[date_col]).set_index(date_col)[val_col].dropna()
        s.name = series_id
        return s if len(s) else None
    except Exception as e:
        sys.stderr.write(f"[fred] {series_id} 파싱 실패 ({e})\n")
        return None


def fred_many(series_ids):
    """병렬 fetch — FRED 가 느리거나 다운이어도 전체 대기시간을 ~타임아웃 수준으로 제한."""
    from concurrent.futures import ThreadPoolExecutor
    out = {}
    with ThreadPoolExecutor(max_workers=min(7, len(series_ids))) as ex:
        for sid, s in zip(series_ids, ex.map(fred_series, series_ids)):
            out[sid] = s
    return out


# ---------------------------------------------------------------------------
# yfinance
# ---------------------------------------------------------------------------
def prices(tickers, lookback_days=420):
    """
    {ticker: pandas Series(종가)} 반환. 실패한 티커는 캐시 폴백, 그래도 없으면 제외.
    """
    _ensure_cache()
    out = {}
    try:
        import yfinance as yf
    except ImportError:
        sys.stderr.write("[yf] yfinance 미설치 — 캐시만 사용\n")
        yf = None

    period = f"{max(lookback_days + 40, 400)}d"
    df = None
    if yf is not None:
        try:
            df = yf.download(
                list(tickers), period=period, interval="1d",
                auto_adjust=True, progress=False, group_by="ticker", threads=True,
            )
        except Exception as e:
            sys.stderr.write(f"[yf] 일괄 다운로드 실패 ({e})\n")

    for t in tickers:
        s = None
        if df is not None:
            try:
                if (t, "Close") in df.columns:
                    s = df[(t, "Close")].dropna()
                elif "Close" in df.columns:        # 단일 티커 케이스
                    s = df["Close"].dropna()
            except Exception:
                s = None
        cache_path = os.path.join(CACHE_DIR, f"px_{t.replace('^','_')}.csv")
        if s is not None and len(s) > 50:
            s.to_csv(cache_path)
            out[t] = s
        elif os.path.exists(cache_path):
            try:
                cs = pd.read_csv(cache_path, index_col=0, parse_dates=True).iloc[:, 0].dropna()
                if len(cs) > 50:
                    out[t] = cs
                    sys.stderr.write(f"[yf] {t} 캐시 사용\n")
            except Exception:
                pass
        else:
            sys.stderr.write(f"[yf] {t} 데이터 없음 — 제외\n")
    return out


if __name__ == "__main__":
    # 빠른 점검
    s = fred_series("T10Y3M")
    print("T10Y3M last:", None if s is None else (s.index[-1].date(), s.iloc[-1]))
    px = prices(["^GSPC", "AAPL"], 120)
    for k, v in px.items():
        print(k, "last:", v.index[-1].date(), round(float(v.iloc[-1]), 2))
