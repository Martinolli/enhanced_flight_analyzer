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
    Manages chart creation and configuration using the ChartConfig abstraction.
    
    This class provides a unified interface for creating various types of charts
    from pandas DataFrames using the ChartConfig abstraction layer. It supports:
    
    - Single and dual-axis charts
    - Multiple chart types: line, scatter, bar, area, frequency analysis
    - Flexible X-axis parameters including time series and custom parameters
    - Color scheme customization
    - Backward compatibility with dictionary-based configurations
    
    The ChartConfig abstraction enables:
    - Easy chart configuration management
    - Extensible chart options for future enhancements  
    - Consistent API across different chart types
    - Support for complex layouts like dual-axis charts
    
    Example Usage:
        # Create chart manager
        cm = ChartManager()
        
        # Single-axis chart
        config = ChartConfig(
            id="basic_chart",
            title="Basic Line Chart", 
            chart_type="line",
            x_param="Time",
            y_params=["Altitude", "Speed"],
            y_axis_label="Flight Parameters"
        )
        fig = cm.create_chart(dataframe, config)
        
        # Dual-axis chart
        dual_config = ChartConfig(
            id="dual_chart",
            title="Altitude vs Temperature",
            chart_type="line", 
            x_param="Time",
            y_params=["Altitude"],
            secondary_y_params=["Temperature"],
            y_axis_label="Altitude (ft)",
            secondary_y_axis_label="Temperature (C)"
        )
        fig = cm.create_chart(dataframe, dual_config)
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
        """
        Create a chart from DataFrame using ChartConfig abstraction.
        
        Supports single and dual-axis charts based on configuration.
        
        Args:
            df: DataFrame containing the data to plot
            config: ChartConfig object or dict that will be migrated to ChartConfig
            
        Returns:
            Plotly Figure object or None if creation fails
        """
        try:
            cfg = self._ensure_config(config)

            if cfg.chart_type != "frequency" and not cfg.y_params:
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

            palette = self.color_schemes.get(cfg.color_scheme, px.colors.sequential.Viridis)
            
            # Create figure with secondary y-axis if needed
            has_secondary = len(valid_secondary_y) > 0
            if has_secondary:
                from plotly.subplots import make_subplots
                fig = make_subplots(specs=[[{"secondary_y": True}]])
            else:
                fig = go.Figure()

            # Add primary y-axis traces
            for idx, param in enumerate(valid_y):
                color = palette[idx % len(palette)]
                x_vals = df_plot[cfg.x_param]
                y_vals = df_plot[param]

                trace = self._create_trace(chosen_type, x_vals, y_vals, param, color)
                if has_secondary:
                    fig.add_trace(trace, secondary_y=False)
                else:
                    fig.add_trace(trace)

            # Add secondary y-axis traces if present
            for idx, param in enumerate(valid_secondary_y):
                color = palette[(idx + len(valid_y)) % len(palette)]
                x_vals = df_plot[cfg.x_param]
                y_vals = df_plot[param]

                trace = self._create_trace(chosen_type, x_vals, y_vals, param, color)
                fig.add_trace(trace, secondary_y=True)

            # Update layout
            fig.update_layout(
                title=cfg.title,
                xaxis_title=cfg.x_param,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )

            # Set y-axis titles
            if has_secondary:
                fig.update_yaxes(title_text=cfg.y_axis_label, secondary_y=False)
                fig.update_yaxes(title_text=cfg.secondary_y_axis_label, secondary_y=True)
            else:
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

    def _create_trace(self, chart_type: str, x_vals, y_vals, param: str, color: str) -> go.Scatter:
        """
        Create a plotly trace based on chart type.
        
        Args:
            chart_type: Type of chart (line, scatter, bar, area)
            x_vals: X-axis values
            y_vals: Y-axis values  
            param: Parameter name for the trace
            color: Color for the trace
            
        Returns:
            Plotly trace object
        """
        if chart_type == "line":
            return go.Scatter(
                x=x_vals, y=y_vals,
                mode="lines",
                name=param,
                line=dict(color=color)
            )
        elif chart_type == "scatter":
            return go.Scatter(
                x=x_vals, y=y_vals,
                mode="markers",
                name=param,
                marker=dict(color=color, size=6)
            )
        elif chart_type == "bar":
            return go.Bar(
                x=x_vals, y=y_vals,
                name=param,
                marker_color=color
            )
        elif chart_type == "area":
            return go.Scatter(
                x=x_vals, y=y_vals,
                mode="lines",
                name=param,
                line=dict(color=color),
                fill="tozeroy"
            )
        else:
            return go.Scatter(
                x=x_vals, y=y_vals,
                mode="lines",
                name=param
            )

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