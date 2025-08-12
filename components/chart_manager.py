import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, Union
from scipy.signal import welch
from scipy.fft import fft, fftfreq

from .config_models import ChartConfig, migrate_chart_dict


class ChartManager:
    """
    Manages chart creation and configuration including arbitrary X-axis.
    """

    def __init__(self):
        self.color_schemes = {
            'viridis': px.colors.sequential.Viridis,
            'plasma': px.colors.sequential.Plasma,
            'inferno': px.colors.sequential.Inferno,
            'magma': px.colors.sequential.Magma,
            'cividis': px.colors.sequential.Cividis,
            'blues': px.colors.sequential.Blues,
            'reds': px.colors.sequential.Reds,
            'greens': px.colors.sequential.Greens,
            'purples': px.colors.sequential.Purples
        }

    def _ensure_config(self, config: Union[ChartConfig, Dict[str, Any]]) -> ChartConfig:
        return config if isinstance(config, ChartConfig) else migrate_chart_dict(config)

    def create_chart(self, df: pd.DataFrame, config: Union[ChartConfig, Dict[str, Any]]) -> Optional[go.Figure]:
        try:
            cfg = self._ensure_config(config)

            if cfg.chart_type != "frequency" and not cfg.y_params:
                return None

            if cfg.chart_type == 'frequency':
                return self._create_frequency_plot(df, cfg)

            if cfg.x_param not in df.columns:
                return None

            valid_y = [p for p in cfg.y_params if p in df.columns]
            if not valid_y:
                return None

            chosen_type = cfg.chart_type

            # DataFrame we will actually plot
            df_plot = df

            non_time = cfg.x_param not in ("Elapsed Time (s)", "Timestamp")
            x_series = df[cfg.x_param]

            if chosen_type == "line" and non_time:
                if not x_series.is_monotonic_increasing:
                    if cfg.sort_x:
                        df_plot = df.sort_values(cfg.x_param)
                    else:
                        chosen_type = "scatter"  # fallback

            palette = self.color_schemes.get(cfg.color_scheme, px.colors.sequential.Viridis)
            fig = go.Figure()

            for idx, param in enumerate(valid_y):
                color = palette[idx % len(palette)]
                x_vals = df_plot[cfg.x_param]
                y_vals = df_plot[param]

                if chosen_type == "line":
                    fig.add_trace(go.Scatter(
                        x=x_vals, y=y_vals,
                        mode="lines",
                        name=param,
                        line=dict(color=color)
                    ))
                elif chosen_type == "scatter":
                    fig.add_trace(go.Scatter(
                        x=x_vals, y=y_vals,
                        mode="markers",
                        name=param,
                        marker=dict(color=color, size=6)
                    ))
                elif chosen_type == "bar":
                    fig.add_trace(go.Bar(
                        x=x_vals, y=y_vals,
                        name=param,
                        marker_color=color
                    ))
                elif chosen_type == "area":
                    fig.add_trace(go.Scatter(
                        x=x_vals, y=y_vals,
                        mode="lines",
                        name=param,
                        line=dict(color=color),
                        fill="tozeroy"
                    ))
                else:
                    fig.add_trace(go.Scatter(
                        x=x_vals, y=y_vals,
                        mode="lines",
                        name=param
                    ))

            fig.update_layout(
                title=cfg.title,
                xaxis_title=cfg.x_param,
                yaxis_title=cfg.y_axis_label,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )

            return fig
        except Exception as e:
            print(f"Error creating chart: {e}")
            return None

    def _create_frequency_plot(self, df: pd.DataFrame, cfg: ChartConfig) -> Optional[go.Figure]:
        try:
            time_col = "Elapsed Time (s)" if "Elapsed Time (s)" in df.columns else (
                "Timestamp" if "Timestamp" in df.columns else cfg.x_param
            )
            if time_col not in df.columns:
                return None
            if not cfg.y_params:
                return None

            t = df[time_col]
            if t.isna().any() or len(t) < 2:
                return None

            diffs = np.diff(t.values.astype(float))
            avg_dt = np.mean(diffs)
            if avg_dt == 0:
                return None
            fs = 1.0 / avg_dt

            fig = go.Figure()
            for param in [p for p in cfg.y_params if p in df.columns]:
                y = df[param].values
                if cfg.freq_type == "psd":
                    f, Pxx = welch(y, fs=fs, nperseg=min(256, len(y)))
                    fig.add_trace(go.Scatter(x=f, y=Pxx, mode="lines", name=f"{param} PSD"))
                else:
                    N = len(y)
                    yf = np.abs(fft(y))
                    xf = fftfreq(N, avg_dt)[:N//2]
                    fig.add_trace(go.Scatter(
                        x=xf,
                        y=2.0 / N * yf[:N//2],
                        mode="lines",
                        name=f"{param} FFT"
                    ))

            fig.update_layout(
                title=cfg.title or "Frequency Analysis",
                xaxis_title="Frequency (Hz)",
                yaxis_title="Magnitude",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            return fig
        except Exception as e:
            print(f"Error creating frequency chart: {e}")
            return None