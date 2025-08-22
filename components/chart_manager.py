import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, Union, List
from scipy.signal import welch, get_window, detrend as scipy_detrend
from scipy.fft import fft, fftfreq

from .config_models import ChartConfig, migrate_chart_dict
from .unit_utils import UnitDetector, detect_unit_mismatch


class ChartManager:
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
        self.unit_detector = UnitDetector()

    def _ensure_config(self, config: Union[ChartConfig, Dict[str, Any]]) -> ChartConfig:
        return config if isinstance(config, ChartConfig) else migrate_chart_dict(config)

    def _analyze_parameter_units(self, cfg: ChartConfig) -> Dict[str, Any]:
        all_params = cfg.y_params + cfg.secondary_y_params
        if not cfg.auto_detect_units:
            return {
                'needs_dual_axis': bool(cfg.secondary_y_params),
                'primary_params': cfg.y_params,
                'secondary_params': cfg.secondary_y_params,
                'primary_unit': cfg.manual_y_unit,
                'secondary_unit': cfg.manual_secondary_y_unit,
                'unit_mismatch_detected': False
            }
        mismatch_info = detect_unit_mismatch(all_params)
        if cfg.secondary_y_params:
            return {
                'needs_dual_axis': True,
                'primary_params': cfg.y_params,
                'secondary_params': cfg.secondary_y_params,
                'primary_unit': cfg.manual_y_unit or self._get_common_unit(cfg.y_params),
                'secondary_unit': cfg.manual_secondary_y_unit or self._get_common_unit(cfg.secondary_y_params),
                'unit_mismatch_detected': mismatch_info['has_mismatch']
            }
        if mismatch_info['needs_dual_axis'] or cfg.force_unit_detection:
            groups = mismatch_info['parameter_groups']
            if cfg.force_unit_detection and len(groups) == 1 and len(groups[0]) > 1:
                all_params = groups[0]
                mid = len(all_params) // 2
                primary_params = all_params[:mid] if mid > 0 else all_params[:1]
                secondary_params = all_params[mid:] if mid < len(all_params) else []
                return {
                    'needs_dual_axis': True,
                    'primary_params': primary_params,
                    'secondary_params': secondary_params,
                    'primary_unit': cfg.manual_y_unit or self._get_common_unit(primary_params),
                    'secondary_unit': cfg.manual_secondary_y_unit or self._get_common_unit(secondary_params),
                    'unit_mismatch_detected': False
                }
            elif len(groups) >= 2:
                groups.sort(key=len, reverse=True)
                primary_params = groups[0]
                secondary_params = []
                for group in groups[1:]:
                    secondary_params.extend(group)
                return {
                    'needs_dual_axis': True,
                    'primary_params': primary_params,
                    'secondary_params': secondary_params,
                    'primary_unit': cfg.manual_y_unit or self._get_common_unit(primary_params),
                    'secondary_unit': cfg.manual_secondary_y_unit or self._get_common_unit(secondary_params),
                    'unit_mismatch_detected': True
                }
        return {
            'needs_dual_axis': False,
            'primary_params': cfg.y_params,
            'secondary_params': [],
            'primary_unit': cfg.manual_y_unit or self._get_common_unit(cfg.y_params),
            'secondary_unit': None,
            'unit_mismatch_detected': mismatch_info['has_mismatch']
        }

    def _get_common_unit(self, parameters: List[str]) -> Optional[str]:
        if not parameters:
            return None
        units = []
        for p in parameters:
            u = self.unit_detector.extract_unit_from_parameter(p)
            if u:
                units.append(u)
        if not units:
            return None
        from collections import Counter
        return Counter(units).most_common(1)[0][0]

    def _format_axis_label(self, base_label: str, unit: Optional[str], style: str = "parentheses") -> str:
        if not unit:
            return base_label
        if style == "bracket":
            return f"{base_label} [{unit}]"
        elif style == "suffix":
            return f"{base_label} {unit}"
        return f"{base_label} ({unit})"

    def _format_legend_name(self, param_name: str, show_units: bool, style: str = "parentheses") -> str:
        if not show_units:
            return self.unit_detector._get_base_parameter_name(param_name)
        unit = self.unit_detector.extract_unit_from_parameter(param_name)
        if unit:
            base_name = self.unit_detector._get_base_parameter_name(param_name)
            return self._format_axis_label(base_name, unit, style)
        return param_name

    def create_chart(self, df: pd.DataFrame, config: Union[ChartConfig, Dict[str, Any]]) -> Optional[go.Figure]:
        try:
            cfg = self._ensure_config(config)
            if cfg.chart_type == 'frequency':
                return self._create_frequency_plot(df, cfg)
            if not cfg.y_params:
                return None
            if cfg.x_param not in df.columns:
                return None
            unit_analysis = self._analyze_parameter_units(cfg)
            primary_params = unit_analysis['primary_params']
            secondary_params = unit_analysis['secondary_params']
            if unit_analysis['needs_dual_axis'] and secondary_params:
                return self._create_dual_axis_chart(df, cfg, unit_analysis, primary_params, secondary_params)
            else:
                return self._create_single_axis_chart(df, cfg, unit_analysis, primary_params)
        except Exception as e:
            print(f"Error creating chart: {e}")
            return None

    def _create_dual_axis_chart(self, df: pd.DataFrame, cfg: ChartConfig,
                                unit_analysis: Dict[str, Any], primary_params: List[str],
                                secondary_params: List[str]) -> go.Figure:
        df_plot = self._prepare_dataframe(df, cfg)
        chosen_type = self._determine_chart_type(df_plot, cfg)
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        palette = self.color_schemes.get(cfg.color_scheme, px.colors.sequential.Viridis)
        for idx, param in enumerate(primary_params):
            if param not in df_plot.columns:
                continue
            color = palette[idx % len(palette)]
            legend_name = self._format_legend_name(param, cfg.show_units_in_legend, cfg.unit_annotation_style)
            trace = self._create_trace(chosen_type, df_plot[cfg.x_param], df_plot[param], legend_name, color)
            fig.add_trace(trace, secondary_y=False)
        secondary_start = len(primary_params)
        for idx, param in enumerate(secondary_params):
            if param not in df_plot.columns:
                continue
            color = palette[(secondary_start + idx) % len(palette)]
            legend_name = self._format_legend_name(param, cfg.show_units_in_legend, cfg.unit_annotation_style)
            trace = self._create_trace(chosen_type, df_plot[cfg.x_param], df_plot[param], legend_name, color)
            if hasattr(trace, 'line'):
                trace.line.dash = 'dash'
            fig.add_trace(trace, secondary_y=True)
        primary_unit = unit_analysis['primary_unit']
        secondary_unit = unit_analysis['secondary_unit']
        primary_label = cfg.y_axis_label or "Value"
        if primary_unit:
            primary_label = self._format_axis_label(primary_label, primary_unit, cfg.unit_annotation_style)
        secondary_label = cfg.secondary_y_axis_label or "Secondary"
        if secondary_unit:
            secondary_label = self._format_axis_label(secondary_label, secondary_unit, cfg.unit_annotation_style)
        fig.update_layout(
            title=cfg.title,
            xaxis_title=cfg.x_param,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        fig.update_yaxes(title_text=primary_label, secondary_y=False)
        fig.update_yaxes(title_text=secondary_label, secondary_y=True)
        if (cfg.synchronize_scales and primary_unit and secondary_unit and
                self.unit_detector.are_units_compatible(primary_unit, secondary_unit)):
            self._synchronize_y_axes(fig, df_plot, primary_params, secondary_params)
        self._apply_timestamp_formatting(fig, cfg, df_plot)
        return fig

    def _prepare_dataframe(self, df: pd.DataFrame, cfg: ChartConfig) -> pd.DataFrame:
        df_plot = df.copy()
        if cfg.x_param == "Timestamp":
            try:
                x_dt = pd.to_datetime(df_plot[cfg.x_param], errors="coerce")
                if x_dt.notna().sum() >= max(3, int(0.8 * len(x_dt))):
                    df_plot[cfg.x_param] = x_dt
            except Exception:
                pass
        non_time = cfg.x_param not in ("Elapsed Time (s)", "Timestamp")
        if cfg.chart_type == "line" and non_time:
            x_series = df_plot[cfg.x_param]
            if not x_series.is_monotonic_increasing and cfg.sort_x:
                df_plot = df_plot.sort_values(cfg.x_param)
        return df_plot

    def _determine_chart_type(self, df_plot: pd.DataFrame, cfg: ChartConfig) -> str:
        chosen_type = cfg.chart_type
        non_time = cfg.x_param not in ("Elapsed Time (s)", "Timestamp")
        if chosen_type == "line" and non_time:
            x_series = df_plot[cfg.x_param]
            if not x_series.is_monotonic_increasing and not cfg.sort_x:
                chosen_type = "scatter"
        return chosen_type

    def _create_trace(self, chart_type: str, x_vals, y_vals, name: str, color: str) -> go.Scatter:
        if chart_type == "line":
            return go.Scatter(x=x_vals, y=y_vals, mode="lines", name=name, line=dict(color=color))
        elif chart_type == "scatter":
            return go.Scatter(x=x_vals, y=y_vals, mode="markers", name=name,
                              marker=dict(color=color, size=6))
        elif chart_type == "bar":
            return go.Bar(x=x_vals, y=y_vals, name=name, marker_color=color)
        elif chart_type == "area":
            return go.Scatter(x=x_vals, y=y_vals, mode="lines", name=name,
                              line=dict(color=color), fill="tozeroy")
        return go.Scatter(x=x_vals, y=y_vals, mode="lines", name=name)

    def _synchronize_y_axes(self, fig, df_plot: pd.DataFrame, primary_params: List[str],
                            secondary_params: List[str]):
        all_values = []
        for param in primary_params + secondary_params:
            if param in df_plot.columns:
                values = df_plot[param].dropna()
                all_values.extend(values)
        if all_values:
            min_val = min(all_values)
            max_val = max(all_values)
            pad = (max_val - min_val) * 0.05 if max_val > min_val else 1
            rmin = min_val - pad
            rmax = max_val + pad
            fig.update_yaxes(range=[rmin, rmax], secondary_y=False)
            fig.update_yaxes(range=[rmin, rmax], secondary_y=True)

    def _apply_timestamp_formatting(self, fig, cfg: ChartConfig, df_plot: pd.DataFrame):
        if cfg.x_param == "Timestamp":
            if pd.api.types.is_datetime64_any_dtype(df_plot[cfg.x_param]):
                fig.update_xaxes(type="date", tickformat="%H:%M:%S.%L")
            else:
                fig.update_xaxes(tickformat=",.3f", tickmode="auto")

    def _create_single_axis_chart(self, df: pd.DataFrame, cfg: ChartConfig,
                                  unit_analysis: Dict[str, Any], primary_params: List[str]) -> go.Figure:
        df_plot = self._prepare_dataframe(df, cfg)
        chosen_type = self._determine_chart_type(df_plot, cfg)
        fig = go.Figure()
        palette = self.color_schemes.get(cfg.color_scheme, px.colors.sequential.Viridis)
        for idx, param in enumerate(primary_params):
            if param not in df_plot.columns:
                continue
            color = palette[idx % len(palette)]
            legend_name = self._format_legend_name(param, cfg.show_units_in_legend, cfg.unit_annotation_style)
            trace = self._create_trace(chosen_type, df_plot[cfg.x_param], df_plot[param], legend_name, color)
            fig.add_trace(trace)
        primary_unit = unit_analysis['primary_unit']
        y_label = cfg.y_axis_label or "Value"
        if primary_unit:
            y_label = self._format_axis_label(y_label, primary_unit, cfg.unit_annotation_style)
        fig.update_layout(
            title=cfg.title,
            xaxis_title=cfg.x_param,
            yaxis_title=y_label,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        self._apply_timestamp_formatting(fig, cfg, df_plot)
        return fig

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
            if t.isna().any() or len(t) < cfg.freq_min_points:
                return None
            t_vals = t.values.astype(float)
            diffs = np.diff(t_vals)
            if len(diffs) == 0:
                return None
            avg_dt = np.mean(diffs)
            if avg_dt <= 0:
                return None
            fs = 1.0 / avg_dt
            irregular_ratio = np.std(diffs) / avg_dt if avg_dt > 0 else 0.0
            irregular_flag = irregular_ratio > cfg.freq_irregular_tol

            fig = go.Figure()
            palette = self.color_schemes.get(cfg.color_scheme, px.colors.sequential.Viridis)

            for idx, param in enumerate([p for p in cfg.y_params if p in df.columns]):
                y = df[param].values.astype(float)
                if cfg.freq_detrend:
                    # Use linear detrend only if length > 3 else mean removal
                    if len(y) > 3:
                        y_proc = scipy_detrend(y, type='linear')
                    else:
                        y_proc = y - np.mean(y)
                else:
                    y_proc = y

                N = len(y_proc)

                if cfg.freq_type == "psd":
                    # Welch PSD
                    nperseg = min(256, N)
                    if nperseg < 8:
                        continue
                    f, Pxx = welch(y_proc, fs=fs, nperseg=nperseg, detrend=False, window=cfg.freq_window if cfg.freq_window != "rect" else "boxcar")
                    trace_name = f"{param} PSD"
                    fig.add_trace(go.Scatter(x=f, y=Pxx, mode="lines",
                                             name=trace_name,
                                             line=dict(color=palette[idx % len(palette)])))
                    if cfg.freq_peak_annotation and len(Pxx) > 1:
                        peak_idx = int(np.argmax(Pxx[1:])) + 1  # ignore DC for peak
                        fig.add_annotation(
                            x=float(f[peak_idx]),
                            y=float(Pxx[peak_idx]),
                            text=f"Peak {f[peak_idx]:.2f} Hz",
                            showarrow=True,
                            arrowhead=2,
                            yshift=10,
                            font=dict(size=10)
                        )
                else:
                    # FFT amplitude spectrum
                    # Window
                    if cfg.freq_window != "rect":
                        try:
                            win = get_window(cfg.freq_window, N)
                        except Exception:
                            win = np.hanning(N)
                    else:
                        win = np.ones(N)
                    y_w = y_proc * win
                    # Amplitude correction (preserve RMS energy)
                    win_correction = np.sum(win) / N
                    yf = fft(y_w)
                    xf = fftfreq(N, avg_dt)
                    pos_mask = xf >= 0
                    xf = xf[pos_mask]
                    yf_abs = (2.0 / (N * win_correction)) * np.abs(yf[pos_mask])
                    # Avoid doubling DC & Nyquist properly
                    if N % 2 == 0 and len(yf_abs) > 1:
                        yf_abs[-1] /= 2.0
                    trace_name = f"{param} FFT"
                    fig.add_trace(go.Scatter(
                        x=xf,
                        y=yf_abs,
                        mode="lines",
                        name=trace_name,
                        line=dict(color=palette[idx % len(palette)])
                    ))
                    if cfg.freq_peak_annotation and len(yf_abs) > 2:
                        # ignore DC
                        peak_idx = np.argmax(yf_abs[1:]) + 1
                        fig.add_annotation(
                            x=float(xf[peak_idx]),
                            y=float(yf_abs[peak_idx]),
                            text=f"Peak {xf[peak_idx]:.2f} Hz",
                            showarrow=True,
                            arrowhead=2,
                            yshift=10,
                            font=dict(size=10)
                        )

            base_title = cfg.title or "Frequency Analysis"
            subtitle_parts = [f"fs={fs:.2f} Hz", f"N={len(t_vals)}"]
            if irregular_flag:
                subtitle_parts.append(f"Irregular sampling (CV={irregular_ratio:.2%})")
            fig.update_layout(
                title=f"{base_title}<br><sub>{' • '.join(subtitle_parts)}</sub>",
                xaxis_title="Frequency (Hz)",
                yaxis_title="PSD" if cfg.freq_type == "psd" else "Amplitude",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                font=dict(family="Arial, sans-serif", size=12, color="black"),
                plot_bgcolor="white",
                paper_bgcolor="white"
            )
            if cfg.freq_log_scale:
                fig.update_yaxes(type="log")
            return fig
        except Exception as e:
            print(f"Error creating frequency chart: {e}")
            return None