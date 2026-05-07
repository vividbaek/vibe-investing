"""User profile abstraction.

A user profile carries persona choice, language preference, onboarding flags,
and free-form interest tags / watchlist tickers. Backed by SQLite for the
local 1차 phase; a Cosmos DB implementation will satisfy the same interface
in 2차 (see paper_plan.md §6.4).
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def make_anon_user_id(user_key: str, salt: str) -> str:
    digest = hashlib.sha256(f"{salt}:{user_key}".encode("utf-8")).hexdigest()
    return digest[:16]


@dataclass
class UserProfile:
    user_key: str
    anon_user_id: str
    persona_key: str
    language: str
    intro_seen: bool
    research_consent: bool
    onboarding_step: str
    interest_tags: list[str] = field(default_factory=list)
    watchlist_tickers: list[str] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""
    # §17.1 — sector follow-up tracking
    recent_tickers: list[str] = field(default_factory=list)        # LRU, max 10
    sector_count: dict[str, int] = field(default_factory=dict)     # {"Technology": 4, ...}
    last_followup_at: str = ""                                     # ISO; rate-limit follow-ups
    # §17.2 — daily deep analysis quota
    daily_deep_count: int = 0
    daily_deep_reset_at: str = ""                                  # ISO of next midnight KST
    # §T2E-A — gamification fields
    points_cumulative: int = 0          # never resets — lifetime total earned
    points_balance: int = 0             # current spendable balance
    points_this_season: int = 0         # resets each quarter (§4.3)
    season_id: str = ""                 # e.g. "2026-Q2"
    tier: str = "bronze"                # bronze|silver|gold|platinum|diamond
    tier_stage: int = 0                 # 0..4 within tier (visual ▼▼ → ▲▲)
    tier_updated_at: str = ""
    consecutive_login_days: int = 0     # for streak bonus
    last_attendance_kst: str = ""       # last KST-date checkin happened
    display_name: str = ""              # user-set; fallback to "User_<anon[:4]>"
    opt_in_leaderboard: bool = True
    # invite tracking (§T2E-C)
    invite_code: str = ""               # 8-char alphanumeric, generated lazily
    invited_by_anon: str = ""           # the inviter's anon_user_id (not user_key!)
    invite_validated_at: str = ""       # filled when first mission completes
    invite_landings_count: int = 0      # how many ref_ link clicks this user generated
    invite_validated_count: int = 0     # invitees who passed first-mission gate
    invite_zombie_count: int = 0        # 7-day no-activity invitees
    # §SAJU — Four Pillars (Saju) profile + recommendation unlocks
    saju_birth_date: str = ""           # ISO yyyy-mm-dd (KST)
    saju_birth_hour: int = -1           # 0–23 KST, -1 = unknown
    saju_first_used_at: str = ""        # ISO date of first /saju/ use (for 5-day free)
    saju_unlocked_today: list[str] = field(default_factory=list)  # tickers unlocked today
    saju_unlocked_date_kst: str = ""    # KST date when unlocks were last reset


class UserProfileRepo:
    """SQLite-backed repository. Thread-safe for the synchronous handlers."""

    _SCHEMA = """
        CREATE TABLE IF NOT EXISTS users (
            user_key            TEXT PRIMARY KEY,
            anon_user_id        TEXT NOT NULL,
            persona_key         TEXT NOT NULL DEFAULT 'buffett',
            language            TEXT NOT NULL DEFAULT 'en',
            intro_seen          INTEGER NOT NULL DEFAULT 0,
            research_consent    INTEGER NOT NULL DEFAULT 0,
            onboarding_step     TEXT NOT NULL DEFAULT 'greeting',
            interest_tags       TEXT NOT NULL DEFAULT '[]',
            watchlist_tickers   TEXT NOT NULL DEFAULT '[]',
            recent_tickers      TEXT NOT NULL DEFAULT '[]',
            sector_count        TEXT NOT NULL DEFAULT '{}',
            last_followup_at    TEXT NOT NULL DEFAULT '',
            daily_deep_count    INTEGER NOT NULL DEFAULT 0,
            daily_deep_reset_at TEXT NOT NULL DEFAULT '',
            points_cumulative   INTEGER NOT NULL DEFAULT 0,
            points_balance      INTEGER NOT NULL DEFAULT 0,
            points_this_season  INTEGER NOT NULL DEFAULT 0,
            season_id           TEXT NOT NULL DEFAULT '',
            tier                TEXT NOT NULL DEFAULT 'bronze',
            tier_stage          INTEGER NOT NULL DEFAULT 0,
            tier_updated_at     TEXT NOT NULL DEFAULT '',
            consecutive_login_days INTEGER NOT NULL DEFAULT 0,
            last_attendance_kst TEXT NOT NULL DEFAULT '',
            display_name        TEXT NOT NULL DEFAULT '',
            opt_in_leaderboard  INTEGER NOT NULL DEFAULT 1,
            invite_code         TEXT NOT NULL DEFAULT '',
            invited_by_anon     TEXT NOT NULL DEFAULT '',
            invite_validated_at TEXT NOT NULL DEFAULT '',
            invite_landings_count INTEGER NOT NULL DEFAULT 0,
            invite_validated_count INTEGER NOT NULL DEFAULT 0,
            invite_zombie_count INTEGER NOT NULL DEFAULT 0,
            saju_birth_date     TEXT NOT NULL DEFAULT '',
            saju_birth_hour     INTEGER NOT NULL DEFAULT -1,
            saju_first_used_at  TEXT NOT NULL DEFAULT '',
            saju_unlocked_today TEXT NOT NULL DEFAULT '[]',
            saju_unlocked_date_kst TEXT NOT NULL DEFAULT '',
            created_at          TEXT NOT NULL,
            updated_at          TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_users_anon ON users(anon_user_id);
        CREATE INDEX IF NOT EXISTS idx_users_invite_code ON users(invite_code);
    """

    # ALTER statements for upgrading older databases. SQLite ignores ALTER
    # if the column already exists (well, it errors — we catch).
    _MIGRATIONS = (
        "ALTER TABLE users ADD COLUMN recent_tickers TEXT NOT NULL DEFAULT '[]'",
        "ALTER TABLE users ADD COLUMN sector_count TEXT NOT NULL DEFAULT '{}'",
        "ALTER TABLE users ADD COLUMN last_followup_at TEXT NOT NULL DEFAULT ''",
        "ALTER TABLE users ADD COLUMN daily_deep_count INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE users ADD COLUMN daily_deep_reset_at TEXT NOT NULL DEFAULT ''",
        # §T2E-A migrations
        "ALTER TABLE users ADD COLUMN points_cumulative INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE users ADD COLUMN points_balance INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE users ADD COLUMN points_this_season INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE users ADD COLUMN season_id TEXT NOT NULL DEFAULT ''",
        "ALTER TABLE users ADD COLUMN tier TEXT NOT NULL DEFAULT 'bronze'",
        "ALTER TABLE users ADD COLUMN tier_stage INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE users ADD COLUMN tier_updated_at TEXT NOT NULL DEFAULT ''",
        "ALTER TABLE users ADD COLUMN consecutive_login_days INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE users ADD COLUMN last_attendance_kst TEXT NOT NULL DEFAULT ''",
        "ALTER TABLE users ADD COLUMN display_name TEXT NOT NULL DEFAULT ''",
        "ALTER TABLE users ADD COLUMN opt_in_leaderboard INTEGER NOT NULL DEFAULT 1",
        "ALTER TABLE users ADD COLUMN invite_code TEXT NOT NULL DEFAULT ''",
        "ALTER TABLE users ADD COLUMN invited_by_anon TEXT NOT NULL DEFAULT ''",
        "ALTER TABLE users ADD COLUMN invite_validated_at TEXT NOT NULL DEFAULT ''",
        "ALTER TABLE users ADD COLUMN invite_landings_count INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE users ADD COLUMN invite_validated_count INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE users ADD COLUMN invite_zombie_count INTEGER NOT NULL DEFAULT 0",
        # §SAJU migrations
        "ALTER TABLE users ADD COLUMN saju_birth_date TEXT NOT NULL DEFAULT ''",
        "ALTER TABLE users ADD COLUMN saju_birth_hour INTEGER NOT NULL DEFAULT -1",
        "ALTER TABLE users ADD COLUMN saju_first_used_at TEXT NOT NULL DEFAULT ''",
        "ALTER TABLE users ADD COLUMN saju_unlocked_today TEXT NOT NULL DEFAULT '[]'",
        "ALTER TABLE users ADD COLUMN saju_unlocked_date_kst TEXT NOT NULL DEFAULT ''",
    )

    def __init__(self, db_path: str | Path, salt: str) -> None:
        self._path = str(db_path)
        self._salt = salt
        self._lock = threading.Lock()
        Path(self._path).parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.executescript(self._SCHEMA)
            # Idempotent migrations (each ALTER may already be applied)
            for stmt in self._MIGRATIONS:
                try:
                    conn.execute(stmt)
                except sqlite3.OperationalError:
                    pass

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._path, isolation_level=None)
        conn.row_factory = sqlite3.Row
        return conn

    def get_or_create(self, user_key: str, default_language: str, default_persona: str) -> UserProfile:
        anon = make_anon_user_id(user_key, self._salt)
        now = _now_iso()
        with self._lock, self._connect() as conn:
            row = conn.execute("SELECT * FROM users WHERE user_key = ?", (user_key,)).fetchone()
            if row is None:
                conn.execute(
                    """
                    INSERT INTO users
                      (user_key, anon_user_id, persona_key, language,
                       intro_seen, research_consent, onboarding_step,
                       interest_tags, watchlist_tickers, created_at, updated_at)
                    VALUES (?, ?, ?, ?, 0, 0, 'greeting', '[]', '[]', ?, ?)
                    """,
                    (user_key, anon, default_persona, default_language, now, now),
                )
                row = conn.execute("SELECT * FROM users WHERE user_key = ?", (user_key,)).fetchone()
        return _row_to_profile(row)

    def update(self, user_key: str, **fields) -> UserProfile:
        if not fields:
            return self.get(user_key)

        coerced: dict[str, object] = {}
        for k, v in fields.items():
            if k in {"interest_tags", "watchlist_tickers", "recent_tickers",
                     "saju_unlocked_today"} and isinstance(v, list):
                coerced[k] = json.dumps(v, ensure_ascii=False)
            elif k == "sector_count" and isinstance(v, dict):
                coerced[k] = json.dumps(v, ensure_ascii=False)
            elif k in {"intro_seen", "research_consent", "opt_in_leaderboard"}:
                coerced[k] = 1 if v else 0
            else:
                coerced[k] = v
        coerced["updated_at"] = _now_iso()

        sets = ", ".join(f"{k} = ?" for k in coerced)
        params = list(coerced.values()) + [user_key]
        with self._lock, self._connect() as conn:
            conn.execute(f"UPDATE users SET {sets} WHERE user_key = ?", params)
            row = conn.execute("SELECT * FROM users WHERE user_key = ?", (user_key,)).fetchone()
        if row is None:
            raise KeyError(f"user not found: {user_key}")
        return _row_to_profile(row)

    def get(self, user_key: str) -> UserProfile:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM users WHERE user_key = ?", (user_key,)).fetchone()
        if row is None:
            raise KeyError(f"user not found: {user_key}")
        return _row_to_profile(row)

    def delete(self, user_key: str) -> bool:
        """Hard-delete the user's row. Returns True if a row was removed."""
        with self._lock, self._connect() as conn:
            cur = conn.execute("DELETE FROM users WHERE user_key = ?", (user_key,))
        return cur.rowcount > 0


def _row_to_profile(row: sqlite3.Row) -> UserProfile:
    keys = row.keys()
    def _g(name, default=""):
        return row[name] if name in keys else default
    return UserProfile(
        user_key=row["user_key"],
        anon_user_id=row["anon_user_id"],
        persona_key=row["persona_key"],
        language=row["language"],
        intro_seen=bool(row["intro_seen"]),
        research_consent=bool(row["research_consent"]),
        onboarding_step=row["onboarding_step"],
        interest_tags=json.loads(row["interest_tags"] or "[]"),
        watchlist_tickers=json.loads(row["watchlist_tickers"] or "[]"),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        recent_tickers=json.loads(_g("recent_tickers", "[]") or "[]"),
        sector_count=json.loads(_g("sector_count", "{}") or "{}"),
        last_followup_at=_g("last_followup_at", ""),
        daily_deep_count=_g("daily_deep_count", 0),
        daily_deep_reset_at=_g("daily_deep_reset_at", ""),
        # §T2E-A
        points_cumulative=_g("points_cumulative", 0),
        points_balance=_g("points_balance", 0),
        points_this_season=_g("points_this_season", 0),
        season_id=_g("season_id", ""),
        tier=_g("tier", "bronze"),
        tier_stage=_g("tier_stage", 0),
        tier_updated_at=_g("tier_updated_at", ""),
        consecutive_login_days=_g("consecutive_login_days", 0),
        last_attendance_kst=_g("last_attendance_kst", ""),
        display_name=_g("display_name", ""),
        opt_in_leaderboard=bool(_g("opt_in_leaderboard", 1)),
        invite_code=_g("invite_code", ""),
        invited_by_anon=_g("invited_by_anon", ""),
        invite_validated_at=_g("invite_validated_at", ""),
        invite_landings_count=_g("invite_landings_count", 0),
        invite_validated_count=_g("invite_validated_count", 0),
        invite_zombie_count=_g("invite_zombie_count", 0),
        saju_birth_date=_g("saju_birth_date", ""),
        saju_birth_hour=_g("saju_birth_hour", -1),
        saju_first_used_at=_g("saju_first_used_at", ""),
        saju_unlocked_today=json.loads(_g("saju_unlocked_today", "[]") or "[]"),
        saju_unlocked_date_kst=_g("saju_unlocked_date_kst", ""),
    )
