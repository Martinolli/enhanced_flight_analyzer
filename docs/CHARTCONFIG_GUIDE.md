# ChartConfig Abstraction Guide

## Overview

The Enhanced Flight Analyzer uses a `ChartConfig` abstraction layer to provide flexible, extensible chart creation capabilities. This abstraction enables easy configuration of various chart types while maintaining backward compatibility with existing configurations.

## Key Features

- **Multiple Chart Types**: Line, scatter, bar, area, and frequency analysis
- **Dual-Axis Support**: Primary and secondary Y-axes for comparing different parameter types
- **Flexible X-Axis**: Support for time series and custom parameters
- **Color Schemes**: Multiple built-in color schemes for visual customization
- **Backward Compatibility**: Seamless migration from dictionary-based configurations

## Basic Usage

### Single-Axis Chart

```python
from components.config_models import ChartConfig
from components.chart_manager import ChartManager

# Create a basic line chart
config = ChartConfig(
    id="altitude_chart",
    title="Altitude vs Time",
    chart_type="line",
    x_param="Elapsed Time (s)",
    y_params=["Altitude (ft)", "Airspeed (kts)"],
    y_axis_label="Flight Parameters",
    color_scheme="viridis"
)

# Generate the chart
chart_manager = ChartManager()
figure = chart_manager.create_chart(dataframe, config)
```

### Dual-Axis Chart

```python
# Create a dual-axis chart comparing altitude and temperature
dual_config = ChartConfig(
    id="altitude_temp",
    title="Altitude vs Temperature",
    chart_type="line",
    x_param="Elapsed Time (s)",
    y_params=["Altitude (ft)"],           # Primary Y-axis
    secondary_y_params=["Temperature (C)"], # Secondary Y-axis
    y_axis_label="Altitude (ft)",
    secondary_y_axis_label="Temperature (C)",
    color_scheme="plasma"
)

figure = chart_manager.create_chart(dataframe, dual_config)
```

## ChartConfig Parameters

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `id` | str | Unique identifier for the chart | Required |
| `title` | str | Chart display title | "Chart" |
| `chart_type` | str | Chart type: "line", "scatter", "bar", "area", "frequency" | "line" |
| `x_param` | str | Column name for X-axis data | "Elapsed Time (s)" |
| `y_params` | List[str] | Column names for primary Y-axis | [] |
| `secondary_y_params` | List[str] | Column names for secondary Y-axis | [] |
| `y_axis_label` | str | Primary Y-axis label | "Value" |
| `secondary_y_axis_label` | str | Secondary Y-axis label | "" |
| `color_scheme` | str | Color scheme name | "viridis" |
| `freq_type` | str | Frequency analysis type: "fft" or "psd" | "fft" |
| `transformations` | List[str] | Data transformations to apply | [] |
| `notes` | Optional[str] | Additional chart notes | None |
| `sort_x` | bool | Sort data by X parameter for line plots | False |

## Available Color Schemes

- `viridis`: Purple-blue-green-yellow gradient
- `plasma`: Purple-pink-yellow gradient  
- `inferno`: Black-red-yellow gradient
- `magma`: Black-purple-white gradient
- `cividis`: Blue-yellow gradient (colorblind-friendly)
- `blues`: Blue monochromatic
- `reds`: Red monochromatic
- `greens`: Green monochromatic
- `purples`: Purple monochromatic

## Chart Types

### Line Charts

Best for continuous time-series data and trend analysis.

### Scatter Charts

Ideal for examining relationships between variables or non-continuous data.

### Bar Charts

Suitable for categorical data and discrete measurements.

### Area Charts

Useful for showing cumulative values or filled regions under curves.

### Frequency Charts

Provides FFT or PSD analysis for frequency domain analysis.

## Backward Compatibility

The system automatically migrates legacy dictionary-based configurations:

```python
# Legacy dictionary format (still supported)
old_config = {
    "id": "legacy_chart",
    "title": "Legacy Chart",
    "type": "line",                    # Old key name
    "x_axis": "Elapsed Time (s)",      # Old key name  
    "parameters": ["Altitude (ft)"],   # Old key name
    "y_axis_label": "Altitude"
}

# Automatically converted to ChartConfig
figure = chart_manager.create_chart(dataframe, old_config)
```

## Template Examples

The layout manager includes pre-built templates that demonstrate dual-axis capabilities:

- **Altitude vs Temperature**: Shows altitude parameters on primary axis, temperature on secondary
- **Speed vs Engine**: Displays speed parameters on primary axis, engine parameters on secondary

These templates automatically detect relevant columns in your data and create appropriate dual-axis configurations.

## Extension Points

The ChartConfig abstraction is designed for future extensibility:

- Additional chart types can be easily added to the `chart_type` field
- New styling options can be incorporated through additional configuration fields
- Advanced layout options can be implemented through the `transformations` field
- Custom color schemes can be added to the ChartManager's color scheme registry

## Best Practices

1. **Use descriptive IDs**: Make chart IDs meaningful for easier management
2. **Choose appropriate chart types**: Match chart type to your data characteristics
3. **Leverage dual-axis for different units**: Use secondary Y-axis when comparing parameters with different scales or units
4. **Select appropriate color schemes**: Consider accessibility and visual clarity
5. **Provide clear axis labels**: Help users understand what each axis represents

## Error Handling

The ChartConfig abstraction includes robust error handling:

- Missing columns are automatically filtered out
- Invalid configurations return `None` instead of crashing
- Migration from legacy formats handles missing fields gracefully
- Type validation ensures configuration integrity

This abstraction layer provides a solid foundation for current chart needs while enabling future enhancements and maintaining backward compatibility.
