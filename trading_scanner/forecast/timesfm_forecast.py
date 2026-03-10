"""Google TimesFM 2.0 forecasting."""

import logging

import numpy as np
import pandas as pd

from config import FORECAST_HORIZON, TIMESFM_MODEL
from forecast.models import ForecastResult

logger = logging.getLogger(__name__)

_model = None


def _get_model():
    """Lazy-load TimesFM model."""
    global _model
    if _model is None:
        try:
            import timesfm

            _model = timesfm.TimesFm(
                hparams=timesfm.TimesFmHparams(
                    horizon_len=FORECAST_HORIZON,
                    input_patch_len=32,
                    output_patch_len=128,
                    num_layers=50,
                    model_dims=1280,
                ),
                checkpoint=timesfm.TimesFmCheckpoint(
                    huggingface_repo_id=TIMESFM_MODEL,
                ),
            )
        except Exception:
            logger.exception("Failed to load TimesFM model")
            return None
    return _model


def predict_timesfm(df: pd.DataFrame, horizon: int = FORECAST_HORIZON) -> ForecastResult | None:
    """Run TimesFM forecast on close prices."""
    try:
        model = _get_model()
        if model is None:
            return None

        close_values = df["Close"].values.astype(np.float32)
        forecasts = model.forecast([close_values])
        point_forecast = forecasts[0][0][:horizon]

        # Generate approximate dates
        last_dt = df.index[-1]
        freq = pd.Timedelta(hours=4)
        dates = [last_dt + freq * (i + 1) for i in range(horizon)]

        # Approximate confidence interval (±2% of forecast)
        lower = [round(float(v * 0.98), 5) for v in point_forecast]
        upper = [round(float(v * 1.02), 5) for v in point_forecast]

        return ForecastResult(
            dates=tuple(d.strftime("%Y-%m-%d %H:%M") for d in dates),
            values=tuple(round(float(v), 5) for v in point_forecast),
            lower=tuple(lower),
            upper=tuple(upper),
            model_name="TimesFM",
        )
    except Exception:
        logger.exception("TimesFM forecast failed")
        return None
