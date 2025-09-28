# Copyright (c) 2025 Martinolli
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Configuration models for the application.

This module defines data classes for various configuration models used in the application,
including chart configurations with enhanced plotting functionalities."""

# Standard Library Imports
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any

CURRENT_SCHEMA_VERSION = 4 #  bumped

@dataclass
class ChartConfig:
    """
    Canonical chart configuration model for enhanced plotting functionality.
    """
    id: str
    title: str = "Chart"
    chart_type: str = "line"            # line | scatter | bar | area | frequency
    x_param: str = "Elapsed Time (s)"
    y_params: List[str] = field(default_factory=list)
    secondary_y_params: List[str] = field(default_factory=list)
    y_axis_label: str = "Value"
    secondary_y_axis_label: str = ""
    color_scheme: str = "viridis"
    freq_type: str = "fft"              # fft | psd
    transformations: List[str] = field(default_factory=list)
    notes: Optional[str] = None
    sort_x: bool = False

    # X-axis UX
    show_x_range_slider: bool = True    # Enable Plotly rangeslider on the x-axis

    # >>> NEW: X-range / timeframe filter <<<
    enable_x_filter: bool = False
    x_filter_min_value: Optional[float] = None    # for numeric X
    x_filter_max_value: Optional[float] = None    # for numeric X
    ts_filter_start: Optional[str] = None         # ISO datetime string for Timestamp X
    ts_filter_end: Optional[str] = None           # ISO datetime string for Timestamp X

    # Unit detection / dual axis
    auto_detect_units: bool = True
    force_unit_detection: bool = False
    manual_y_unit: Optional[str] = None
    manual_secondary_y_unit: Optional[str] = None
    synchronize_scales: bool = False
    show_units_in_legend: bool = True
    unit_annotation_style: str = "parentheses"  # parentheses | bracket | suffix

    # Frequency analysis enhancements
    freq_detrend: bool = True           # Remove mean / trend before FFT/PSD
    freq_window: str = "hann"           # hann | hamming | blackman | rect
    freq_log_scale: bool = False        # Log scale for Y (magnitude / PSD)
    freq_peak_annotation: bool = True   # Annotate dominant peak
    freq_min_points: int = 16           # Minimum points required
    freq_irregular_tol: float = 0.05    # Relative std dev tolerance for sampling irregularity warning

    # >>> NEW FIELDS <<<
    override_sample_rate: Optional[float] = None  # Hz
    max_frequency: Optional[float] = None         # Hz limit for plotting
    welch_nperseg: int = 2048
    welch_overlap: float = 0.5                    # 0..0.95
    highpass_cutoff: Optional[float] = None       # Hz
    band_rms: List[List[float]] = field(default_factory=list)  # [[lo, hi], ...]

    def as_dict(self) -> Dict[str, Any]:
        """
        Convert ChartConfig to a dictionary for storage or transmission.
        Note: Includes schema version for future migrations.
        Arguments:
            None
        Returns:
            Dict[str, Any]: Dictionary representation of the ChartConfig.
        """
        return {
            "id": self.id,
            "title": self.title,
            "type": self.chart_type,
            "chart_type": self.chart_type,
            "x_axis": self.x_param,
            "x_param": self.x_param,
            "parameters": list(self.y_params),
            "y_params": list(self.y_params),
            "secondary_y_params": list(self.secondary_y_params),
            "y_axis_label": self.y_axis_label,
            "secondary_y_axis_label": self.secondary_y_axis_label,
            "color_scheme": self.color_scheme,
            "freq_type": self.freq_type,
            "transformations": list(self.transformations),
            "notes": self.notes,
            "sort_x": self.sort_x,
            "show_x_range_slider": self.show_x_range_slider,
            "enable_x_filter": self.enable_x_filter,
            "x_filter_min_value": self.x_filter_min_value,
            "x_filter_max_value": self.x_filter_max_value,
            "ts_filter_start": self.ts_filter_start,
            "ts_filter_end": self.ts_filter_end,
            "auto_detect_units": self.auto_detect_units,
            "force_unit_detection": self.force_unit_detection,
            "manual_y_unit": self.manual_y_unit,
            "manual_secondary_y_unit": self.manual_secondary_y_unit,
            "synchronize_scales": self.synchronize_scales,
            "show_units_in_legend": self.show_units_in_legend,
            "unit_annotation_style": self.unit_annotation_style,
            "freq_detrend": self.freq_detrend,
            "freq_window": self.freq_window,
            "freq_log_scale": self.freq_log_scale,
            "freq_peak_annotation": self.freq_peak_annotation,
            "freq_min_points": self.freq_min_points,
            "freq_irregular_tol": self.freq_irregular_tol,
            "override_sample_rate": self.override_sample_rate,
            "max_frequency": self.max_frequency,
            "welch_nperseg": self.welch_nperseg,
            "welch_overlap": self.welch_overlap,
            "highpass_cutoff": self.highpass_cutoff,
            "band_rms": self.band_rms,
            "schema_version": CURRENT_SCHEMA_VERSION
        }
        
def migrate_chart_dict(d: Dict[str, Any]) -> ChartConfig:
    """
     Extend existing migration logic to fill defaults for new frequency fields.
     Arguments:
         d (Dict[str, Any]): The chart configuration dictionary to migrate.
    Returns:
            ChartConfig: The migrated ChartConfig instance.
    """
    # Existing migrations...
    if "override_sample_rate" not in d:
        d["override_sample_rate"] = None
    if "max_frequency" not in d:
        d["max_frequency"] = None
    if "welch_nperseg" not in d:
        d["welch_nperseg"] = 2048
    if "welch_overlap" not in d:
        d["welch_overlap"] = 0.5
    if "highpass_cutoff" not in d:
        d["highpass_cutoff"] = None
    if "band_rms" not in d:
        d["band_rms"] = []
    if "show_x_range_slider" not in d:
        d["show_x_range_slider"] = False
    if "enable_x_filter" not in d:
        d["enable_x_filter"] = False
    if "x_filter_min_value" not in d:
        d["x_filter_min_value"] = None
    if "x_filter_max_value" not in d:
        d["x_filter_max_value"] = None
    if "ts_filter_start" not in d:
        d["ts_filter_start"] = None
    if "ts_filter_end" not in d:
        d["ts_filter_end"] = None

    return ChartConfig(
        id=d["id"],
        title=d.get("title", "Chart"),
        chart_type=d.get("chart_type", "line"),
        x_param=d.get("x_param"),
        y_params=d.get("y_params", []),
        secondary_y_params=d.get("secondary_y_params", []),
        y_axis_label=d.get("y_axis_label", ""),
        secondary_y_axis_label=d.get("secondary_y_axis_label"),
        color_scheme=d.get("color_scheme", "viridis"),
        freq_type=d.get("freq_type", "fft"),
        sort_x=d.get("sort_x", False),
        show_x_range_slider=d.get("show_x_range_slider", False),
        enable_x_filter=d.get("enable_x_filter", False),
        x_filter_min_value=d.get("x_filter_min_value"),
        x_filter_max_value=d.get("x_filter_max_value"),
        ts_filter_start=d.get("ts_filter_start"),
        ts_filter_end=d.get("ts_filter_end"),
        auto_detect_units=d.get("auto_detect_units", True),
        force_unit_detection=d.get("force_unit_detection", False),
        synchronize_scales=d.get("synchronize_scales", False),
        show_units_in_legend=d.get("show_units_in_legend", True),
        unit_annotation_style=d.get("unit_annotation_style", "parentheses"),
        manual_y_unit=d.get("manual_y_unit"),
        manual_secondary_y_unit=d.get("manual_secondary_y_unit"),
        freq_detrend=d.get("freq_detrend", True),
        freq_window=d.get("freq_window", "hann"),
        freq_log_scale=d.get("freq_log_scale", False),
        freq_peak_annotation=d.get("freq_peak_annotation", True),
        freq_min_points=d.get("freq_min_points", 16),
        freq_irregular_tol=d.get("freq_irregular_tol", 0.05),
        override_sample_rate=d.get("override_sample_rate"),
        max_frequency=d.get("max_frequency"),
        welch_nperseg=d.get("welch_nperseg", 2048),
        welch_overlap=d.get("welch_overlap", 0.5),
        highpass_cutoff=d.get("highpass_cutoff"),
        band_rms=d.get("band_rms", []),
    )
