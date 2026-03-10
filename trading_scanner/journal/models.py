"""Journal models."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Trade:
    """Trade journal entry."""
    id: int | None
    date: str
    instrument: str
    direction: str          # "long" | "short"
    entry_price: float | None
    stop_loss: float | None
    take_profit: float | None
    risk_reward: float
    candle_pattern: str | None
    chart_pattern: str | None
    trend: str | None
    result: str             # "open" | "win" | "loss" | "breakeven"
    pnl_pips: float | None
    notes: str | None
    created_at: str | None
