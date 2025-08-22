# Unit Detection and Dual-Axis API Reference

## ChartConfig New Options

### Unit Detection Options

```python
from components.config_models import ChartConfig

# Automatic unit detection (default)
config = ChartConfig(
    id="auto_units",
    title="Automatic Unit Detection",
    y_params=["Temperature (DGC)", "Pressure (psi)"],
    auto_detect_units=True,  # Default: True
    show_units_in_legend=True,  # Default: True
    unit_annotation_style="parentheses"  # Default: "parentheses"
)

# Manual unit specification
config = ChartConfig(
    id="manual_units",
    title="Manual Unit Control",
    y_params=["Parameter1"],
    secondary_y_params=["Parameter2"],
    auto_detect_units=False,
    manual_y_unit="DGC",
    manual_secondary_y_unit="psi",
    y_axis_label="Temperature",
    secondary_y_axis_label="Pressure"
)

# Force dual-axis for compatible units
config = ChartConfig(
    id="force_dual",
    title="Force Dual Axis",
    y_params=["Temp1 (DGC)", "Temp2 (DGC)"],
    force_unit_detection=True,  # Forces dual-axis even for compatible units
    synchronize_scales=True  # Sync scales for compatible units
)
```

### Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `auto_detect_units` | bool | True | Enable automatic unit detection from parameter names |
| `force_unit_detection` | bool | False | Force dual-axis even for compatible units |
| `manual_y_unit` | str | None | Manual override for primary y-axis unit |
| `manual_secondary_y_unit` | str | None | Manual override for secondary y-axis unit |
| `synchronize_scales` | bool | False | Synchronize y-axis scales for compatible units |
| `show_units_in_legend` | bool | True | Show units in legend entries |
| `unit_annotation_style` | str | "parentheses" | Unit annotation style: "parentheses", "bracket", "suffix" |

## Unit Detection API

### UnitDetector Class

```python
from components.unit_utils import UnitDetector

detector = UnitDetector()

# Extract unit from parameter name
unit = detector.extract_unit_from_parameter("Temperature (DGC)")  # Returns "DGC"

# Get unit category
category = detector.get_unit_category("deg")  # Returns "angle"

# Check unit compatibility
compatible = detector.are_units_compatible("DGC", "C")  # Returns True

# Analyze multiple parameters
analysis = detector.analyze_parameter_units([
    "Temperature (DGC)", 
    "Pressure (psi)",
    "Angle (deg)"
])

# Group parameters by compatibility
groups = detector.group_parameters_by_unit_compatibility([
    "Temp1 (DGC)", "Temp2 (C)",  # Group 1: temperature
    "Angle1 (deg)", "Angle2 (rad)",  # Group 2: angle
    "Force (N)"  # Group 3: force
])
```

### Mismatch Detection

```python
from components.unit_utils import detect_unit_mismatch

parameters = ["Temperature (DGC)", "Pressure (psi)", "Angle (deg)"]
result = detect_unit_mismatch(parameters)

print(result['has_mismatch'])  # True
print(result['needs_dual_axis'])  # True
print(result['parameter_groups'])  # [["Temperature (DGC)"], ["Pressure (psi)"], ["Angle (deg)"]]
print(result['unique_categories'])  # ["temperature", "pressure", "angle"]
```

## Supported Unit Categories

| Category | Units |
|----------|-------|
| time | s, sec, ms, min, h, hr |
| angle | deg, rad, arc-deg |
| force | N, lbf, lb, kgf |
| acceleration | g, m/s2, ft/s2 |
| pressure | Pa, kPa, psi, bar, atm |
| temperature | C, DGC, F, K |
| velocity | m/s, ft/s, kts, mph, km/h |
| percentage | %, percent, ratio |
| electrical | V, A, mA, mV |
| frequency | Hz, kHz, rpm |
| dimensionless | "", ADM, count, flag |

## Chart Behavior

### Automatic Dual-Axis Creation

The system automatically creates dual-axis charts when:

1. Parameters have incompatible unit categories
2. `force_unit_detection=True` is set
3. `secondary_y_params` is explicitly specified

### Single-Axis Charts

Single-axis charts are used when:

1. All parameters have compatible units
2. `auto_detect_units=False` and no secondary params specified
3. Only one parameter is plotted

### Axis Assignment

- **Primary Axis (left)**: Largest unit group or manually specified `y_params`
- **Secondary Axis (right)**: Smaller unit groups or manually specified `secondary_y_params`
- **Visual Distinction**: Secondary axis traces use dashed lines

## Examples

See `examples/unit_detection_demo.py` for comprehensive examples demonstrating:

- Automatic unit detection
- Dual-axis chart creation
- Manual unit specification
- Scale synchronization
- Legend control
