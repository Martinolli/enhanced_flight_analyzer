from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any


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
    freq_min_points: int = 8            # Minimum points required
    freq_irregular_tol: float = 0.05    # Relative std dev tolerance for sampling irregularity warning

    def to_legacy_dict(self) -> Dict[str, Any]:
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
            "freq_irregular_tol": self.freq_irregular_tol
        }

    def as_dict(self) -> Dict[str, Any]:
        base = asdict(self)
        base.update({
            "type": self.chart_type,
            "parameters": list(self.y_params),
            "x_axis": self.x_param,
        })
        return base


def migrate_chart_dict(old: Dict[str, Any]) -> ChartConfig:
    if isinstance(old, ChartConfig):
        return old
    return ChartConfig(
        id=old.get("id", old.get("chart_id", "chart")),
        title=old.get("title", "Chart"),
        chart_type=old.get("chart_type", old.get("type", "line")),
        x_param=old.get("x_param", old.get("x_axis", "Elapsed Time (s)")),
        y_params=old.get("y_params", old.get("parameters", [])) or [],
        secondary_y_params=old.get("secondary_y_params", []),
        y_axis_label=old.get("y_axis_label", "Value"),
        secondary_y_axis_label=old.get("secondary_y_axis_label", ""),
        color_scheme=old.get("color_scheme", "viridis"),
        freq_type=old.get("freq_type", "fft"),
        transformations=old.get("transformations", []),
        notes=old.get("notes"),
        sort_x=old.get("sort_x", False),
        auto_detect_units=old.get("auto_detect_units", True),
        force_unit_detection=old.get("force_unit_detection", False),
        manual_y_unit=old.get("manual_y_unit"),
        manual_secondary_y_unit=old.get("manual_secondary_y_unit"),
        synchronize_scales=old.get("synchronize_scales", False),
        show_units_in_legend=old.get("show_units_in_legend", True),
        unit_annotation_style=old.get("unit_annotation_style", "parentheses"),
        freq_detrend=old.get("freq_detrend", True),
        freq_window=old.get("freq_window", "hann"),
        freq_log_scale=old.get("freq_log_scale", False),
        freq_peak_annotation=old.get("freq_peak_annotation", True),
        freq_min_points=old.get("freq_min_points", 8),
        freq_irregular_tol=old.get("freq_irregular_tol", 0.05)
    )