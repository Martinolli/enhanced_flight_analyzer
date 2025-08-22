from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any


@dataclass
class ChartConfig:
    """
    Canonical chart configuration model for enhanced plotting functionality.
    
    This abstraction enables flexible chart creation with support for:
    - Multiple chart types (line, scatter, bar, area, frequency)
    - Dual-axis plotting with primary and secondary Y parameters
    - Customizable styling via color schemes
    - Extensible configuration for future chart enhancements
    
    Attributes:
        id (str): Unique identifier for the chart configuration
        title (str): Display title for the chart
        chart_type (str): Type of chart to create. Options:
            - 'line': Line plot for continuous data
            - 'scatter': Scatter plot for point data  
            - 'bar': Bar chart for categorical/discrete data
            - 'area': Area chart with fill
            - 'frequency': Frequency domain analysis (FFT/PSD)
        x_param (str): Column name for X-axis data
        y_params (List[str]): Column names for primary Y-axis parameters
        secondary_y_params (List[str]): Column names for secondary Y-axis parameters
            (enables dual-axis charts when specified)
        y_axis_label (str): Label for primary Y-axis
        secondary_y_axis_label (str): Label for secondary Y-axis
        color_scheme (str): Color scheme for plot traces. Options:
            'viridis', 'plasma', 'inferno', 'magma', 'cividis', 
            'blues', 'reds', 'greens', 'purples'
        freq_type (str): Frequency analysis type ('fft' or 'psd')
        transformations (List[str]): Data transformations to apply
        notes (Optional[str]): Additional notes about the chart
        sort_x (bool): Whether to sort data by X parameter for line plots
    
    Example:
        # Single-axis chart
        config = ChartConfig(
            id="altitude_speed",
            title="Altitude and Speed vs Time",
            chart_type="line",
            x_param="Elapsed Time (s)",
            y_params=["Altitude (ft)", "Airspeed (kts)"],
            y_axis_label="Altitude & Speed",
            color_scheme="viridis"
        )
        
        # Dual-axis chart
        config = ChartConfig(
            id="altitude_temp",
            title="Altitude vs Temperature",
            chart_type="line",
            x_param="Elapsed Time (s)",
            y_params=["Altitude (ft)"],
            secondary_y_params=["Temperature (C)"],
            y_axis_label="Altitude (ft)",
            secondary_y_axis_label="Temperature (C)",
            color_scheme="plasma"
        )
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


"""
ChartConfig Migration and Configuration Functions

This module provides utilities for working with the ChartConfig abstraction,
including migration from legacy dictionary-based configurations.

The ChartConfig abstraction supports:
- Single and dual-axis charts
- Multiple chart types (line, scatter, bar, area, frequency)
- Flexible color schemes and styling
- Backward compatibility with dictionary configurations
"""

def migrate_chart_dict(old: Dict[str, Any]) -> ChartConfig:
    """
    Migrate legacy dictionary-based chart configuration to ChartConfig object.
    
    This function ensures backward compatibility by converting old-style
    dictionary configurations to the new ChartConfig abstraction.
    
    Args:
        old: Dictionary containing chart configuration or existing ChartConfig
        
    Returns:
        ChartConfig object with migrated configuration
        
    Example:
        # Legacy dictionary config
        old_config = {
            "id": "altitude_chart",
            "title": "Altitude vs Time",
            "type": "line",
            "x_axis": "Elapsed Time (s)", 
            "parameters": ["Altitude (ft)"],
            "secondary_y_params": ["Temperature (C)"],
            "y_axis_label": "Altitude",
            "secondary_y_axis_label": "Temperature"
        }
        
        # Convert to ChartConfig
        config = migrate_chart_dict(old_config)
    """
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