"""Facebook Prophet forecasting — anchored to last known price."""

import logging

import pandas as pd

from config import FORECAST_HORIZON
from forecast.models import ForecastResult

logger = logging.getLogger(__name__)


def predict_prophet(df: pd.DataFrame, horizon: int = FORECAST_HORIZON) -> ForecastResult | None:
    """Run Prophet forecast on close prices, anchored to last known price."""
    try:
        from prophet import Prophet

        prophet_df = pd.DataFrame({
            "ds": df.index,
            "y": df["Close"].values,
        })

        model = Prophet(
            daily_seasonality=False,
            weekly_seasonality=True,
            yearly_seasonality=True,
            changepoint_prior_scale=0.15,
            n_changepoints=30,
        )
        model.fit(prophet_df)

        future = model.make_future_dataframe(periods=horizon, freq="4h")
        forecast = model.predict(future)

        # Anchor forecast to last known price
        last_actual = float(df["Close"].iloc[-1])
        # Get the last fitted value (row just before forecast-only rows)
        n_history = len(prophet_df)
        last_fitted = float(forecast.iloc[n_history - 1]["yhat"])
        offset = last_actual - last_fitted
        logger.info("Anchor: actual=%.2f fitted=%.2f offset=%.2f", last_actual, last_fitted, offset)

        pred = forecast.tail(horizon)
        values = [round(v + offset, 5) for v in pred["yhat"].tolist()]
        lower = [round(v + offset, 5) for v in pred["yhat_lower"].tolist()]
        upper = [round(v + offset, 5) for v in pred["yhat_upper"].tolist()]

        return ForecastResult(
            dates=tuple(pred["ds"].dt.strftime("%Y-%m-%d %H:%M").tolist()),
            values=tuple(values),
            lower=tuple(lower),
            upper=tuple(upper),
            model_name="Prophet",
        )
    except Exception:
        logger.exception("Prophet forecast failed")
        return None
