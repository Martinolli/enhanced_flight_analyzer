from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any


@dataclass
class ChartConfig:
    """
    Canonical chart configuration model.
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
    sort_x: bool = False                # New: if True and non-time X, sort to keep line plot

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
            "sort_x": self.sort_x
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
        sort_x=old.get("sort_x", False)
    )