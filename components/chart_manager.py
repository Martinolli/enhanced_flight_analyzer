import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, Union, List, Tuple
from scipy.signal import welch
from scipy.fft import fft, fftfreq

from .config_models import ChartConfig, migrate_chart_dict
from .unit_utils import UnitDetector, detect_unit_mismatch


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
        self.unit_detector = UnitDetector()

    def _ensure_config(self, config: Union[ChartConfig, Dict[str, Any]]) -> ChartConfig:
        return config if isinstance(config, ChartConfig) else migrate_chart_dict(config)
    
    def _analyze_parameter_units(self, cfg: ChartConfig) -> Dict[str, Any]:
        """
        Analyze units for the chart parameters.
        
        Args:
            cfg: Chart configuration
            
        Returns:
            Dictionary with unit analysis results
        """
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
        
        # Detect unit mismatches
        mismatch_info = detect_unit_mismatch(all_params)
        
        # If secondary_y_params is already specified, respect that
        if cfg.secondary_y_params:
            return {
                'needs_dual_axis': True,
                'primary_params': cfg.y_params,
                'secondary_params': cfg.secondary_y_params,
                'primary_unit': cfg.manual_y_unit or self._get_common_unit(cfg.y_params),
                'secondary_unit': cfg.manual_secondary_y_unit or self._get_common_unit(cfg.secondary_y_params),
                'unit_mismatch_detected': mismatch_info['has_mismatch']
            }
        
        # Auto-assign parameters to axes based on unit compatibility
        if mismatch_info['needs_dual_axis'] or cfg.force_unit_detection:
            groups = mismatch_info['parameter_groups']
            
            # If forcing dual axis and only one group, split the group
            if cfg.force_unit_detection and len(groups) == 1 and len(groups[0]) > 1:
                # Split the single group: first half to primary, second half to secondary
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
                    'unit_mismatch_detected': False  # Not actually mismatched, just forced
                }
            
            # Assign largest group to primary axis, others to secondary
            elif len(groups) >= 2:
                # Sort groups by size, largest first
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
        
        # No dual axis needed
        return {
            'needs_dual_axis': False,
            'primary_params': cfg.y_params,
            'secondary_params': [],
            'primary_unit': cfg.manual_y_unit or self._get_common_unit(cfg.y_params),
            'secondary_unit': None,
            'unit_mismatch_detected': mismatch_info['has_mismatch']
        }
    
    def _get_common_unit(self, parameters: List[str]) -> Optional[str]:
        """
        Get the most common unit from a list of parameters.
        
        Args:
            parameters: List of parameter names
            
        Returns:
            Most common unit or None
        """
        if not parameters:
            return None
        
        units = []
        for param in parameters:
            unit = self.unit_detector.extract_unit_from_parameter(param)
            if unit:
                units.append(unit)
        
        if not units:
            return None
        
        # Return most common unit
        from collections import Counter
        unit_counts = Counter(units)
        return unit_counts.most_common(1)[0][0]
    
    def _format_axis_label(self, base_label: str, unit: Optional[str], style: str = "parentheses") -> str:
        """
        Format axis label with unit annotation.
        
        Args:
            base_label: Base label text
            unit: Unit to append
            style: Annotation style ('parentheses', 'bracket', 'suffix')
            
        Returns:
            Formatted label with unit
        """
        if not unit:
            return base_label
        
        if style == "bracket":
            return f"{base_label} [{unit}]"
        elif style == "suffix":
            return f"{base_label} {unit}"
        else:  # parentheses (default)
            return f"{base_label} ({unit})"
    
    def _format_legend_name(self, param_name: str, show_units: bool, style: str = "parentheses") -> str:
        """
        Format legend name with optional unit display.
        
        Args:
            param_name: Parameter name
            show_units: Whether to show units in legend
            style: Unit annotation style
            
        Returns:
            Formatted legend name
        """
        if not show_units:
            # Remove existing unit annotations
            return self.unit_detector._get_base_parameter_name(param_name)
        
        # Keep existing format or apply style
        unit = self.unit_detector.extract_unit_from_parameter(param_name)
        if unit:
            base_name = self.unit_detector._get_base_parameter_name(param_name)
            return self._format_axis_label(base_name, unit, style)
        
        return param_name

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

            # Frequency (FFT/PSD) charts handled separately
            if cfg.chart_type == 'frequency':
                return self._create_frequency_plot(df, cfg)

            # Must have y parameters for non-frequency charts
            if not cfg.y_params:
                return None

            # X param must exist
            if cfg.x_param not in df.columns:
                return None

            # Analyze units / axis assignment
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
        """
        Create a dual-axis chart.
        
        Args:
            df: DataFrame containing the data
            cfg: Chart configuration
            unit_analysis: Unit analysis results
            primary_params: Parameters for primary y-axis
            secondary_params: Parameters for secondary y-axis
            
        Returns:
            Plotly figure with dual y-axes
        """
        df_plot = self._prepare_dataframe(df, cfg)
        chosen_type = self._determine_chart_type(df_plot, cfg)
        
        # Create subplot with secondary y-axis
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        palette = self.color_schemes.get(cfg.color_scheme, px.colors.sequential.Viridis)
        
        # Add primary axis traces
        for idx, param in enumerate(primary_params):
            color = palette[idx % len(palette)]
            x_vals = df_plot[cfg.x_param]
            y_vals = df_plot[param]
            
            legend_name = self._format_legend_name(param, cfg.show_units_in_legend, cfg.unit_annotation_style)
            trace = self._create_trace(chosen_type, x_vals, y_vals, legend_name, color)
            fig.add_trace(trace, secondary_y=False)

        # Add secondary axis traces
        secondary_start_idx = len(primary_params)
        for idx, param in enumerate(secondary_params):
            color = palette[(secondary_start_idx + idx) % len(palette)]
            x_vals = df_plot[cfg.x_param]
            y_vals = df_plot[param]
            
            legend_name = self._format_legend_name(param, cfg.show_units_in_legend, cfg.unit_annotation_style)
            trace = self._create_trace(chosen_type, x_vals, y_vals, legend_name, color)
            # Make secondary traces dashed to differentiate
            if hasattr(trace, 'line'):
                trace.line.dash = 'dash'
            fig.add_trace(trace, secondary_y=True)

        # Format axis labels
        primary_unit = unit_analysis['primary_unit']
        secondary_unit = unit_analysis['secondary_unit']
        
        primary_label = cfg.y_axis_label
        if primary_unit and primary_label == "Value":
            primary_label = self._format_axis_label("Value", primary_unit, cfg.unit_annotation_style)
        elif primary_unit:
            primary_label = self._format_axis_label(primary_label, primary_unit, cfg.unit_annotation_style)
            
        secondary_label = cfg.secondary_y_axis_label or "Secondary"
        if secondary_unit:
            secondary_label = self._format_axis_label(secondary_label, secondary_unit, cfg.unit_annotation_style)

        # Update layout
        fig.update_layout(
            title=cfg.title,
            xaxis_title=cfg.x_param,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        # Set y-axes titles
        fig.update_yaxes(title_text=primary_label, secondary_y=False)
        fig.update_yaxes(title_text=secondary_label, secondary_y=True)
        
        # Synchronize scales if requested and units are compatible
        if (cfg.synchronize_scales and primary_unit and secondary_unit and 
            self.unit_detector.are_units_compatible(primary_unit, secondary_unit)):
            self._synchronize_y_axes(fig, df_plot, primary_params, secondary_params)

        self._apply_timestamp_formatting(fig, cfg, df_plot)
        
        return fig
    
    def _prepare_dataframe(self, df: pd.DataFrame, cfg: ChartConfig) -> pd.DataFrame:
        """
        Prepare DataFrame for plotting (handle timestamps, sorting, etc.).
        
        Args:
            df: Input DataFrame
            cfg: Chart configuration
            
        Returns:
            Prepared DataFrame
        """
        df_plot = df.copy()

        # Handle Timestamp axis formatting
        if cfg.x_param == "Timestamp":
            try:
                x_dt = pd.to_datetime(df_plot[cfg.x_param], errors="coerce")
                if x_dt.notna().sum() >= max(3, int(0.8 * len(x_dt))):
                    df_plot[cfg.x_param] = x_dt
            except Exception:
                pass

        # Handle sorting for non-time x-axis
        non_time = cfg.x_param not in ("Elapsed Time (s)", "Timestamp")
        if cfg.chart_type == "line" and non_time:
            x_series = df_plot[cfg.x_param]
            if not x_series.is_monotonic_increasing and cfg.sort_x:
                df_plot = df_plot.sort_values(cfg.x_param)

        return df_plot
    
    def _determine_chart_type(self, df_plot: pd.DataFrame, cfg: ChartConfig) -> str:
        """
        Determine the actual chart type to use (may fallback from line to scatter).
        
        Args:
            df_plot: Prepared DataFrame
            cfg: Chart configuration
            
        Returns:
            Chart type to use
        """
        chosen_type = cfg.chart_type
        
        # Check if we need to fallback to scatter for non-monotonic data
        non_time = cfg.x_param not in ("Elapsed Time (s)", "Timestamp")
        if chosen_type == "line" and non_time:
            x_series = df_plot[cfg.x_param]
            if not x_series.is_monotonic_increasing and not cfg.sort_x:
                chosen_type = "scatter"  # fallback
        
        return chosen_type
    
    def _create_trace(self, chart_type: str, x_vals, y_vals, name: str, color: str) -> go.Scatter:
        """
        Create a plotly trace based on chart type.
        
        Args:
            chart_type: Type of chart
            x_vals: X values
            y_vals: Y values
            name: Trace name
            color: Trace color
            
        Returns:
            Plotly trace
        """
        if chart_type == "line":
            return go.Scatter(
                x=x_vals, y=y_vals,
                mode="lines",
                name=name,
                line=dict(color=color)
            )
        elif chart_type == "scatter":
            return go.Scatter(
                x=x_vals, y=y_vals,
                mode="markers",
                name=name,
                marker=dict(color=color, size=6)
            )
        elif chart_type == "bar":
            return go.Bar(
                x=x_vals, y=y_vals,
                name=name,
                marker_color=color
            )
        elif chart_type == "area":
            return go.Scatter(
                x=x_vals, y=y_vals,
                mode="lines",
                name=name,
                line=dict(color=color),
                fill="tozeroy"
            )
        else:
            return go.Scatter(
                x=x_vals, y=y_vals,
                mode="lines",
                name=name
            )
    
    def _synchronize_y_axes(self, fig, df_plot: pd.DataFrame, primary_params: List[str], 
                           secondary_params: List[str]):
        """
        Synchronize y-axis scales for dual-axis charts with compatible units.
        
        Args:
            fig: Plotly figure
            df_plot: DataFrame with plot data
            primary_params: Primary axis parameters
            secondary_params: Secondary axis parameters
        """
        # Calculate combined range for all parameters
        all_values = []
        for param in primary_params + secondary_params:
            if param in df_plot.columns:
                values = df_plot[param].dropna()
                all_values.extend(values)
        
        if all_values:
            min_val = min(all_values)
            max_val = max(all_values)
            
            # Add some padding
            range_padding = (max_val - min_val) * 0.05
            range_min = min_val - range_padding
            range_max = max_val + range_padding
            
            # Apply to both axes
            fig.update_yaxes(range=[range_min, range_max], secondary_y=False)
            fig.update_yaxes(range=[range_min, range_max], secondary_y=True)
    
    def _apply_timestamp_formatting(self, fig, cfg: ChartConfig, df_plot: pd.DataFrame):
        """
        Apply timestamp-specific formatting to the x-axis.
        
        Args:
            fig: Plotly figure
            cfg: Chart configuration
            df_plot: Prepared DataFrame
        """
        if cfg.x_param == "Timestamp":
            # Check if timestamp was successfully converted to datetime
            if pd.api.types.is_datetime64_any_dtype(df_plot[cfg.x_param]):
                fig.update_xaxes(type="date", tickformat="%H:%M:%S.%L")
            else:
                fig.update_xaxes(tickformat=",.3f", tickmode="auto")

    def _create_single_axis_chart(self, df: pd.DataFrame, cfg: ChartConfig, unit_analysis: Dict[str, Any],
                                  primary_params: List[str]) -> go.Figure:
        """Create a single-axis chart (line/scatter/bar/area)."""
        df_plot = self._prepare_dataframe(df, cfg)
        chosen_type = self._determine_chart_type(df_plot, cfg)
        fig = go.Figure()
        palette = self.color_schemes.get(cfg.color_scheme, px.colors.sequential.Viridis)

        for idx, param in enumerate(primary_params):
            if param not in df_plot.columns:
                continue
            color = palette[idx % len(palette)]
            x_vals = df_plot[cfg.x_param]
            y_vals = df_plot[param]
            legend_name = self._format_legend_name(param, cfg.show_units_in_legend, cfg.unit_annotation_style)
            trace = self._create_trace(chosen_type, x_vals, y_vals, legend_name, color)
            fig.add_trace(trace)

        # Axis label formatting
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
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                # Export-friendly defaults
                font=dict(family="Arial, sans-serif", size=12, color="black"),
                plot_bgcolor="white",
                paper_bgcolor="white"
            )
            return fig
        except Exception as e:
            print(f"Error creating frequency chart: {e}")
            return None