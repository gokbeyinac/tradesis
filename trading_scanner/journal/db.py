"""SQLite trade journal database."""

import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

_DB_DIR = Path(__file__).resolve().parent.parent / "data"
_DB_PATH = _DB_DIR / "journal.db"


class JournalDB:
    """Trade journal with SQLite storage."""

    def __init__(self, db_path: Path = _DB_PATH):
        self._db_path = db_path
        self._ensure_table()

    def _connect(self) -> sqlite3.Connection:
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_table(self) -> None:
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    date            TEXT,
                    instrument      TEXT NOT NULL,
                    direction       TEXT NOT NULL,
                    entry_price     REAL,
                    stop_loss       REAL,
                    take_profit     REAL,
                    risk_reward     REAL DEFAULT 0,
                    candle_pattern  TEXT,
                    chart_pattern   TEXT,
                    trend           TEXT,
                    result          TEXT DEFAULT 'open',
                    pnl_pips        REAL,
                    notes           TEXT,
                    created_at      TEXT NOT NULL
                )
            """)

    def add_trade(self, trade: dict) -> int:
        """Insert a new trade. Returns trade ID."""
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            cursor = conn.execute(
                """INSERT INTO trades
                   (date, instrument, direction, entry_price, stop_loss, take_profit,
                    risk_reward, candle_pattern, chart_pattern, trend, result, pnl_pips, notes, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    trade.get("date"),
                    trade["instrument"],
                    trade["direction"],
                    trade.get("entry_price"),
                    trade.get("stop_loss"),
                    trade.get("take_profit"),
                    trade.get("risk_reward", 0),
                    trade.get("candle_pattern"),
                    trade.get("chart_pattern"),
                    trade.get("trend"),
                    trade.get("result", "open"),
                    trade.get("pnl_pips"),
                    trade.get("notes"),
                    now,
                ),
            )
            return cursor.lastrowid

    def update_result(self, trade_id: int, result: str, pnl_pips: float | None = None) -> None:
        """Update trade result."""
        with self._connect() as conn:
            conn.execute(
                "UPDATE trades SET result = ?, pnl_pips = ? WHERE id = ?",
                (result, pnl_pips, trade_id),
            )

    def get_all(self) -> pd.DataFrame:
        """Return all trades as DataFrame."""
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM trades ORDER BY created_at DESC").fetchall()
        if not rows:
            return pd.DataFrame()
        return pd.DataFrame([dict(r) for r in rows])

    def get_statistics(self) -> dict:
        """Compute trade statistics."""
        df = self.get_all()
        if df.empty:
            return {"total_trades": 0, "wins": 0, "losses": 0, "win_rate": 0,
                    "by_instrument": {}, "by_candle_pattern": {}}

        closed = df[df["result"].isin(["win", "loss", "breakeven"])]
        total = len(closed)
        wins = len(closed[closed["result"] == "win"])
        losses = len(closed[closed["result"] == "loss"])
        win_rate = round(wins / total * 100, 1) if total > 0 else 0

        by_instrument = {}
        for inst, group in closed.groupby("instrument"):
            inst_wins = len(group[group["result"] == "win"])
            inst_total = len(group)
            by_instrument[inst] = round(inst_wins / inst_total * 100, 1) if inst_total > 0 else 0

        by_candle = {}
        candle_trades = closed[closed["candle_pattern"].notna()]
        for pat, group in candle_trades.groupby("candle_pattern"):
            pat_wins = len(group[group["result"] == "win"])
            pat_total = len(group)
            by_candle[pat] = round(pat_wins / pat_total * 100, 1) if pat_total > 0 else 0

        return {
            "total_trades": total,
            "wins": wins,
            "losses": losses,
            "win_rate": win_rate,
            "by_instrument": by_instrument,
            "by_candle_pattern": by_candle,
        }
