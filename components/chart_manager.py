import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, Union, List
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

            if cfg.chart_type != "frequency" and not cfg.y_params and not cfg.secondary_y_params:
                return None

            if cfg.chart_type == 'frequency':
                return self._create_frequency_plot(df, cfg)

            if cfg.x_param not in df.columns:
                return None

            valid_y = [p for p in cfg.y_params if p in df.columns]
            valid_secondary_y = [p for p in cfg.secondary_y_params if p in df.columns]
            
            if not valid_y and not valid_secondary_y:
                return None

            chosen_type = cfg.chart_type

            # DataFrame we will actually plot
            df_plot = df

            # Handle Timestamp axis formatting: try converting to datetime; else force numeric tickformat
            x_is_datetime = False
            if cfg.x_param == "Timestamp":
                try:
                    # Attempt datetime coercion (infer_datetime_format deprecated; default behavior is sufficient)
                    x_dt = pd.to_datetime(df_plot[cfg.x_param], errors="coerce")
                    # Accept if majority parsed
                    if x_dt.notna().sum() >= max(3, int(0.8 * len(x_dt))):
                        df_plot = df_plot.copy()
                        df_plot[cfg.x_param] = x_dt
                        x_is_datetime = True
                except Exception:
                    x_is_datetime = False

            non_time = cfg.x_param not in ("Elapsed Time (s)", "Timestamp")
            x_series = df_plot[cfg.x_param]

            if chosen_type == "line" and non_time:
                if not x_series.is_monotonic_increasing:
                    if cfg.sort_x:
                        df_plot = df.sort_values(cfg.x_param)
                    else:
                        chosen_type = "scatter"  # fallback

            # Determine if we need secondary Y-axis
            has_secondary = len(valid_secondary_y) > 0
            
            if has_secondary:
                # Create subplot with secondary Y-axis
                fig = make_subplots(specs=[[{"secondary_y": True}]])
            else:
                # Regular single-axis figure
                fig = go.Figure()

            palette = self.color_schemes.get(cfg.color_scheme, px.colors.sequential.Viridis)
            
            # Helper function to get different line styles for secondary axis
            def get_line_style(is_secondary: bool, base_color: str) -> Dict[str, Any]:
                if is_secondary:
                    return {"color": base_color, "dash": "dash"}
                else:
                    return {"color": base_color}
            
            # Helper function to disambiguate legend names
            def get_legend_name(param: str, is_secondary: bool) -> str:
                if has_secondary:
                    axis_label = "(Right)" if is_secondary else "(Left)"
                    return f"{param} {axis_label}"
                return param

            # Add primary Y-axis traces
            for idx, param in enumerate(valid_y):
                color = palette[idx % len(palette)]
                x_vals = df_plot[cfg.x_param]
                y_vals = df_plot[param]
                legend_name = get_legend_name(param, False)

                if chosen_type == "line":
                    trace = go.Scatter(
                        x=x_vals, y=y_vals,
                        mode="lines",
                        name=legend_name,
                        line=get_line_style(False, color)
                    )
                elif chosen_type == "scatter":
                    trace = go.Scatter(
                        x=x_vals, y=y_vals,
                        mode="markers",
                        name=legend_name,
                        marker=dict(color=color, size=6)
                    )
                elif chosen_type == "bar":
                    trace = go.Bar(
                        x=x_vals, y=y_vals,
                        name=legend_name,
                        marker_color=color
                    )
                elif chosen_type == "area":
                    trace = go.Scatter(
                        x=x_vals, y=y_vals,
                        mode="lines",
                        name=legend_name,
                        line=get_line_style(False, color),
                        fill="tozeroy"
                    )
                else:
                    trace = go.Scatter(
                        x=x_vals, y=y_vals,
                        mode="lines",
                        name=legend_name
                    )

                if has_secondary:
                    fig.add_trace(trace, secondary_y=False)
                else:
                    fig.add_trace(trace)

            # Add secondary Y-axis traces
            for idx, param in enumerate(valid_secondary_y):
                # Continue color sequence from where primary left off
                color_idx = (len(valid_y) + idx) % len(palette)
                color = palette[color_idx]
                x_vals = df_plot[cfg.x_param]
                y_vals = df_plot[param]
                legend_name = get_legend_name(param, True)

                if chosen_type == "line":
                    trace = go.Scatter(
                        x=x_vals, y=y_vals,
                        mode="lines",
                        name=legend_name,
                        line=get_line_style(True, color)
                    )
                elif chosen_type == "scatter":
                    trace = go.Scatter(
                        x=x_vals, y=y_vals,
                        mode="markers",
                        name=legend_name,
                        marker=dict(color=color, size=6, symbol="diamond")  # Different symbol for secondary
                    )
                elif chosen_type == "bar":
                    trace = go.Bar(
                        x=x_vals, y=y_vals,
                        name=legend_name,
                        marker_color=color,
                        opacity=0.7  # Slightly transparent for secondary
                    )
                elif chosen_type == "area":
                    trace = go.Scatter(
                        x=x_vals, y=y_vals,
                        mode="lines",
                        name=legend_name,
                        line=get_line_style(True, color),
                        fill="tozeroy"
                    )
                else:
                    trace = go.Scatter(
                        x=x_vals, y=y_vals,
                        mode="lines",
                        name=legend_name,
                        line=get_line_style(True, color)
                    )

                fig.add_trace(trace, secondary_y=True)

            # Configure layout
            fig.update_layout(
                title=cfg.title,
                xaxis_title=cfg.x_param,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )

            if has_secondary:
                # Set Y-axes titles for dual-axis chart
                fig.update_yaxes(title_text=cfg.y_axis_label, secondary_y=False)
                fig.update_yaxes(title_text=cfg.secondary_y_axis_label, secondary_y=True)
            else:
                # Single axis chart
                fig.update_layout(yaxis_title=cfg.y_axis_label)

            # Enforce readable axis formatting for Timestamp
            if cfg.x_param == "Timestamp":
                if x_is_datetime:
                    # Use date axis and a readable tick format (time-of-day with ms)
                    fig.update_xaxes(type="date", tickformat="%H:%M:%S.%L")
                else:
                    # Not parseable as datetime: force decimal, not engineering
                    fig.update_xaxes(tickformat=",.3f", tickmode="auto")

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
                    from scipy.fft import fft, fftfreq  # local import in case scipy not fully present earlier
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