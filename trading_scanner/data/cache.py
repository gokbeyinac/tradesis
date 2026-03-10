"""SQLite-backed DataFrame cache with TTL."""

import io
import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

_CACHE_DIR = Path(__file__).resolve().parent.parent / "data"
_CACHE_DB = _CACHE_DIR / "cache.db"


class CacheStore:
    """SQLite cache for DataFrames serialized as parquet."""

    def __init__(self, db_path: Path = _CACHE_DB):
        self._db_path = db_path
        self._ensure_table()

    def _connect(self) -> sqlite3.Connection:
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        return sqlite3.connect(self._db_path)

    def _ensure_table(self) -> None:
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS df_cache (
                    key         TEXT PRIMARY KEY,
                    fetched_at  TEXT NOT NULL,
                    dataframe   BLOB NOT NULL
                )
            """)

    def get(self, key: str, ttl_hours: float) -> pd.DataFrame | None:
        """Return cached DataFrame if valid, else None."""
        try:
            with self._connect() as conn:
                row = conn.execute(
                    "SELECT fetched_at, dataframe FROM df_cache WHERE key = ?",
                    (key,),
                ).fetchone()
            if row is None:
                return None
            fetched_at = datetime.fromisoformat(row[0]).replace(tzinfo=timezone.utc)
            age_hours = (datetime.now(timezone.utc) - fetched_at).total_seconds() / 3600
            if age_hours >= ttl_hours:
                return None
            return pd.read_parquet(io.BytesIO(row[1]))
        except Exception:
            logger.exception("Cache read failed for %s", key)
            return None

    def set(self, key: str, df: pd.DataFrame) -> None:
        """Store DataFrame in cache."""
        try:
            buf = io.BytesIO()
            df.to_parquet(buf, index=True)
            now_iso = datetime.now(timezone.utc).isoformat()
            with self._connect() as conn:
                conn.execute(
                    """INSERT INTO df_cache (key, fetched_at, dataframe)
                       VALUES (?, ?, ?)
                       ON CONFLICT(key) DO UPDATE SET
                           fetched_at = excluded.fetched_at,
                           dataframe  = excluded.dataframe""",
                    (key, now_iso, buf.getvalue()),
                )
        except Exception:
            logger.exception("Cache write failed for %s", key)

    def invalidate(self, key: str) -> None:
        """Remove a cache entry."""
        with self._connect() as conn:
            conn.execute("DELETE FROM df_cache WHERE key = ?", (key,))

    def clear(self) -> None:
        """Remove all cache entries."""
        with self._connect() as conn:
            conn.execute("DELETE FROM df_cache")
