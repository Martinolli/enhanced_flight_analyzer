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
from .unit_conversion import PhysicalUnitConverter
from components.vibration_utils import apply_highpass, compute_band_rms, detect_psd_peaks


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
        self.unit_converter = PhysicalUnitConverter()

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
        # Configure x-axis formatting and optional interactions (range slider / selector)
        show_slider = bool(getattr(cfg, "show_x_range_slider", False))
        is_timestamp = (cfg.x_param == "Timestamp")
        
        # Add gridlines to all charts
        fig.update_layout(
            xaxis=dict(showgrid=True, gridwidth=1, gridcolor='lightgray'),
            yaxis=dict(showgrid=True, gridwidth=1, gridcolor='lightgray')
        )
        
        # If we have a Timestamp column, prefer date formatting when dtype is datetime
        if is_timestamp:
            if pd.api.types.is_datetime64_any_dtype(df_plot[cfg.x_param]):
                # Updated format to show HH:MM:SS without milliseconds
                fig.update_xaxes(
                    type="date", 
                    tickformat="%H:%M:%S",
                    rangeslider=dict(visible=show_slider),
                    showgrid=True,
                    gridwidth=1,
                    gridcolor='lightgray'
                )
            else:
                fig.update_xaxes(
                    tickformat=",.3f",
                    tickmode="auto",
                    rangeslider=dict(visible=show_slider),
                    showgrid=True,
                    gridwidth=1,
                    gridcolor='lightgray'
                )
        else:
            # Non-Timestamp x-axis (e.g., Elapsed Time (s) or other numeric)
            fig.update_xaxes(
                tickformat=",.3f" if pd.api.types.is_numeric_dtype(df_plot[cfg.x_param]) else None,
                tickmode="auto",
                rangeslider=dict(visible=show_slider),
                showgrid=True,
                gridwidth=1,
                gridcolor='lightgray'
            )

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
            if cfg.chart_type == "frequency":
                fig = go.Figure()
                palette = self.color_schemes.get(cfg.color_scheme, px.colors.sequential.Viridis)

                # Determine sampling
                time_col = "Elapsed Time (s)" if "Elapsed Time (s)" in df.columns else (
                    "Timestamp" if "Timestamp" in df.columns else cfg.x_param
                )
                if time_col not in df.columns:
                    return None

                t_series = df[time_col]
                if t_series.isna().any() or len(t_series) < cfg.freq_min_points:
                    return None

                t_vals = t_series.values.astype(float)
                diffs = np.diff(t_vals)
                if len(diffs) == 0:
                    return None
                avg_dt = np.mean(diffs)
                if avg_dt <= 0:
                    return None
                fs_computed = 1.0 / avg_dt
                fs = float(cfg.override_sample_rate) if (cfg.override_sample_rate and cfg.override_sample_rate > 0) else fs_computed

                irregular_ratio = np.std(diffs) / avg_dt if avg_dt > 0 else 0.0
                irregular_flag = irregular_ratio > cfg.freq_irregular_tol

                # Prepare subtitle diagnostics (updated later with Δf)
                subtitle_parts = [f"fs={fs:.2f} Hz", f"N={len(t_vals)}"]
                if cfg.override_sample_rate and cfg.override_sample_rate > 0:
                    subtitle_parts.append("fs_override")
                if irregular_flag:
                    subtitle_parts.append(f"Irregular (CV={irregular_ratio:.2%})")

                nyquist = fs / 2.0

                # Track if user restricts frequency display
                max_f = cfg.max_frequency if cfg.max_frequency and cfg.max_frequency > 0 else None
                if max_f and max_f > nyquist:
                    max_f = nyquist

                # RMS band accumulation (only meaningful for PSD)
                band_defs = []
                for pair in cfg.band_rms:
                    try:
                        lo, hi = float(pair[0]), float(pair[1])
                        if hi > lo > 0:
                            band_defs.append((lo, hi))
                    except Exception:
                        continue

                peak_annotations_done = False

                for idx, param in enumerate([p for p in cfg.y_params if p in df.columns]):
                    raw_unit = self.unit_detector.extract_unit_from_parameter(param)
                    normalized_unit = self.unit_detector.normalize_unit(raw_unit)
                    category = self.unit_detector.get_unit_category(raw_unit)
                    y_original = df[param].values.astype(float)

                    # Unit conversion (re‑use existing utilities)
                    y_converted, si_unit = self.unit_converter.convert_to_si(
                        y_original, normalized_unit, category
                    )
                    conv_info = self.unit_converter.get_conversion_info(normalized_unit, category)
                    display_unit = si_unit if conv_info['should_convert'] else (raw_unit or "")

                    y = y_converted

                    # Detrend (existing)
                    if cfg.freq_detrend:
                        if len(y) > 3:
                            y = scipy_detrend(y, type='linear')
                        else:
                            y = y - np.mean(y)

                    # High-pass (new)
                    y = apply_highpass(y, fs, cfg.highpass_cutoff)

                    N = len(y)
                    if N < cfg.freq_min_points:
                        continue

                    # PSD (Welch) path
                    if cfg.freq_type == "psd":
                        # Adjust nperseg if too large / small
                        nperseg = min(cfg.welch_nperseg, N)
                        if nperseg < 8:
                            continue
                        noverlap = int(min(max(0.0, cfg.welch_overlap), 0.95) * nperseg)
                        if noverlap >= nperseg:
                            noverlap = nperseg // 2

                        # Use SciPy Welch
                        f_freqs, Pxx = welch(
                            y,
                            fs=fs,
                            nperseg=nperseg,
                            noverlap=noverlap,
                            detrend=False,
                            window=cfg.freq_window if cfg.freq_window != "rect" else "boxcar"
                        )

                        # Restrict frequency range
                        if max_f:
                            mask = f_freqs <= max_f
                            f_plot = f_freqs[mask]
                            Pxx_plot = Pxx[mask]
                        else:
                            f_plot, Pxx_plot = f_freqs, Pxx

                        trace_name = f"{param} PSD"
                        if display_unit:
                            trace_name += f" ({display_unit}²/Hz)"
                        fig.add_trace(go.Scatter(
                            x=f_plot,
                            y=Pxx_plot,
                            mode="lines",
                            name=trace_name,
                            line=dict(color=palette[idx % len(palette)])
                        ))

                        # Peak detection (optional annotation)
                        if cfg.freq_peak_annotation and not peak_annotations_done and len(Pxx_plot) > 3:
                            peaks = detect_psd_peaks(f_plot, Pxx_plot, prominence=0.0, max_peaks=1)
                            if peaks:
                                pk = peaks[0]
                                fig.add_annotation(
                                    x=pk["frequency"],
                                    y=pk["value"],
                                    text=f"Peak {pk['frequency']:.2f} Hz",
                                    showarrow=True,
                                    arrowhead=2,
                                    font=dict(size=10),
                                    yshift=10
                                )
                            peak_annotations_done = True

                        # Band RMS (only PSD)
                        band_results = compute_band_rms(f_freqs, Pxx, band_defs) if band_defs else []

                    else:
                        # FFT amplitude spectrum
                        if cfg.freq_window != "rect":
                            try:
                                win = get_window(cfg.freq_window, N)
                            except Exception:
                                win = np.hanning(N)
                        else:
                            win = np.ones(N)
                        y_w = y * win
                        win_correction = np.sum(win) / N
                        yf = fft(y_w)
                        xf = fftfreq(N, 1.0 / fs)

                        # Positive freqs
                        pos_mask = xf >= 0
                        xf = xf[pos_mask]
                        yf_abs = (2.0 / (N * win_correction)) * np.abs(yf[pos_mask])
                        if N % 2 == 0 and len(yf_abs) > 1:
                            yf_abs[-1] /= 2.0

                        if max_f:
                            mask = xf <= max_f
                            xf_plot = xf[mask]
                            yf_plot = yf_abs[mask]
                        else:
                            xf_plot, yf_plot = xf, yf_abs

                        trace_name = f"{param} FFT"
                        if display_unit:
                            trace_name += f" ({display_unit})"
                        fig.add_trace(go.Scatter(
                            x=xf_plot,
                            y=yf_plot,
                            mode="lines",
                            name=trace_name,
                            line=dict(color=palette[idx % len(palette)])
                        ))

                        if cfg.freq_peak_annotation and len(yf_plot) > 2 and not peak_annotations_done:
                            peak_idx = np.argmax(yf_plot[1:]) + 1
                            fig.add_annotation(
                                x=float(xf_plot[peak_idx]),
                                y=float(yf_plot[peak_idx]),
                                text=f"Peak {xf_plot[peak_idx]:.2f} Hz",
                                showarrow=True,
                                arrowhead=2,
                                yshift=10,
                                font=dict(size=10)
                            )
                            peak_annotations_done = True

                        band_results = []  # Not using band RMS for FFT amplitude (PSD is correct domain)

                    # After first trace, we can finalize Δf
                    if idx == 0:
                        if cfg.freq_type == "psd":
                            if len(f_freqs) > 1:
                                delta_f = f_freqs[1] - f_freqs[0]
                            else:
                                delta_f = fs / N
                        else:
                            delta_f = fs / N
                        subtitle_parts.append(f"Nyq={nyquist:.1f} Hz")
                        subtitle_parts.append(f"Δf={delta_f:.3f} Hz")
                        if cfg.freq_type == "psd":
                            subtitle_parts.append(f"nperseg={nperseg}")
                            subtitle_parts.append(f"overlap={noverlap}")
                        if cfg.highpass_cutoff:
                            subtitle_parts.append(f"HP>{cfg.highpass_cutoff:.1f}Hz")
                        if max_f:
                            subtitle_parts.append(f"f≤{max_f:.0f}Hz")

                    # Add band RMS table as figure annotations (top-right stacking)
                    if band_results:
                        yref = 1.0
                        xref = 1.0
                        offset = 0
                        for bres in band_results:
                            fig.add_annotation(
                                xref="paper", yref="paper",
                                x=1.0, y=1.0 - (0.05 * offset),
                                showarrow=False,
                                align="right",
                                text=f"{param} {bres.band}: RMS={bres.rms:.4g}",
                                font=dict(size=10, color=palette[idx % len(palette)])
                            )
                            offset += 1

                base_title = cfg.title or "Frequency Analysis"
                fig.update_layout(
                    title=f"{base_title}<br><sub>{' • '.join(subtitle_parts)}</sub>",
                    xaxis_title="Frequency (Hz)",
                    yaxis_title="PSD" if cfg.freq_type == "psd" else "Amplitude",
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                )

                # Optional range slider on frequency axis as well
                if getattr(cfg, "show_x_range_slider", False):
                    fig.update_xaxes(rangeslider=dict(visible=True))

                if cfg.freq_log_scale:
                    fig.update_yaxes(type="log", exponentformat="power")

                return fig
        except Exception as e:
            # Consider using logging instead of print for production
            print(f"Error creating frequency chart: {e}")
            return None
