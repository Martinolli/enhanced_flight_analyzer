#!/usr/bin/env python3
"""
Example demonstrating the new unit detection and dual-axis chart features.

This script shows how the enhanced flight analyzer now automatically detects
units from parameter names and creates appropriate dual-axis charts when
parameters have incompatible units.
"""

import sys
import os
import pandas as pd
import numpy as np

# Add project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from components.chart_manager import ChartManager
from components.config_models import ChartConfig
from components.unit_utils import UnitDetector, detect_unit_mismatch


def create_sample_flight_data():
    """Create sample flight data with various unit types."""
    np.random.seed(42)
    time_points = np.linspace(0, 60, 301)  # 60 seconds at 5Hz
    
    # Time-based parameters
    elapsed_time = time_points
    
    # Temperature parameters (compatible units)
    engine_temp = 650 + 50 * np.sin(0.1 * time_points) + np.random.normal(0, 5, len(time_points))
    oil_temp = 90 + 10 * np.sin(0.05 * time_points) + np.random.normal(0, 2, len(time_points))
    
    # Angular parameters (compatible units)
    pitch_angle = 5 + 3 * np.sin(0.2 * time_points) + np.random.normal(0, 0.5, len(time_points))
    roll_angle = 2 * np.sin(0.15 * time_points) + np.random.normal(0, 0.3, len(time_points))
    
    # Force/pressure parameters (different unit categories)
    stick_force = 10 + 5 * np.sin(0.3 * time_points) + np.random.normal(0, 1, len(time_points))
    cabin_pressure = 14.7 + 0.5 * np.sin(0.1 * time_points) + np.random.normal(0, 0.1, len(time_points))
    
    # Speed parameter
    airspeed = 120 + 20 * np.sin(0.08 * time_points) + np.random.normal(0, 2, len(time_points))
    
    return pd.DataFrame({
        'Elapsed Time (s)': elapsed_time,
        'Engine Temperature (DGC)': engine_temp,
        'Oil Temperature (C)': oil_temp,
        'Pitch Angle (deg)': pitch_angle,
        'Roll Angle (deg)': roll_angle,
        'Stick Force (N)': stick_force,
        'Cabin Pressure (psi)': cabin_pressure,
        'Airspeed (kts)': airspeed
    })


def demonstrate_unit_detection():
    """Demonstrate the unit detection capabilities."""
    print("🔍 Unit Detection Demonstration")
    print("=" * 50)
    
    detector = UnitDetector()
    
    # Sample parameter names from flight data
    parameters = [
        'Engine Temperature (DGC)',
        'Oil Temperature (C)', 
        'Pitch Angle (deg)',
        'Roll Angle (deg)',
        'Stick Force (N)',
        'Cabin Pressure (psi)',
        'Airspeed (kts)'
    ]
    
    print("Parameter Analysis:")
    analysis = detector.analyze_parameter_units(parameters)
    for param, info in analysis.items():
        print(f"  {param}")
        print(f"    Unit: {info['unit']}")
        print(f"    Category: {info['category']}")
        print(f"    Base name: {info['base_name']}")
        print()
    
    print("Unit Compatibility Groups:")
    groups = detector.group_parameters_by_unit_compatibility(parameters)
    for i, group in enumerate(groups):
        units = [detector.extract_unit_from_parameter(p) for p in group]
        print(f"  Group {i+1}: {', '.join(group)}")
        print(f"    Units: {', '.join(filter(None, units))}")
        print()
    
    print("Mismatch Detection:")
    mismatch_info = detect_unit_mismatch(parameters)
    print(f"  Has mismatch: {mismatch_info['has_mismatch']}")
    print(f"  Needs dual axis: {mismatch_info['needs_dual_axis']}")
    print(f"  Unique categories: {', '.join(mismatch_info['unique_categories'])}")
    print()


def demonstrate_automatic_dual_axis():
    """Demonstrate automatic dual-axis chart creation."""
    print("📊 Automatic Dual-Axis Chart Demonstration")
    print("=" * 50)
    
    df = create_sample_flight_data()
    cm = ChartManager()
    
    # Example 1: Mixed units (should create dual-axis automatically)
    print("Example 1: Mixed Units - Temperature and Pressure")
    cfg1 = ChartConfig(
        id="mixed_units",
        title="Engine Monitoring - Mixed Units",
        chart_type="line",
        x_param="Elapsed Time (s)",
        y_params=["Engine Temperature (DGC)", "Cabin Pressure (psi)"],
        auto_detect_units=True
    )
    
    fig1 = cm.create_chart(df, cfg1)
    if fig1:
        print(f"  ✅ Created chart with {len(fig1.data)} traces")
        secondary_traces = [tr for tr in fig1.data if hasattr(tr, 'yaxis') and tr.yaxis == 'y2']
        print(f"  📈 Primary axis traces: {len(fig1.data) - len(secondary_traces)}")
        print(f"  📈 Secondary axis traces: {len(secondary_traces)}")
        print(f"  🏷️  Chart type: {'Dual-axis' if secondary_traces else 'Single-axis'}")
    print()
    
    # Example 2: Compatible units (should use single axis)
    print("Example 2: Compatible Units - Both Temperature")
    cfg2 = ChartConfig(
        id="compatible_units",
        title="Temperature Monitoring - Compatible Units",
        chart_type="line",
        x_param="Elapsed Time (s)",
        y_params=["Engine Temperature (DGC)", "Oil Temperature (C)"],
        auto_detect_units=True
    )
    
    fig2 = cm.create_chart(df, cfg2)
    if fig2:
        print(f"  ✅ Created chart with {len(fig2.data)} traces")
        secondary_traces = [tr for tr in fig2.data if hasattr(tr, 'yaxis') and tr.yaxis == 'y2']
        print(f"  📈 Primary axis traces: {len(fig2.data) - len(secondary_traces)}")
        print(f"  📈 Secondary axis traces: {len(secondary_traces)}")
        print(f"  🏷️  Chart type: {'Dual-axis' if secondary_traces else 'Single-axis'}")
    print()


def demonstrate_manual_override():
    """Demonstrate manual unit specification and controls."""
    print("⚙️ Manual Override Demonstration")
    print("=" * 50)
    
    df = create_sample_flight_data()
    cm = ChartManager()
    
    # Example 1: Force dual-axis for compatible units
    print("Example 1: Force Dual-Axis for Compatible Units")
    cfg1 = ChartConfig(
        id="force_dual",
        title="Force Dual-Axis - Both Angles",
        chart_type="line",
        x_param="Elapsed Time (s)",
        y_params=["Pitch Angle (deg)", "Roll Angle (deg)"],
        auto_detect_units=True,
        force_unit_detection=True
    )
    
    fig1 = cm.create_chart(df, cfg1)
    if fig1:
        secondary_traces = [tr for tr in fig1.data if hasattr(tr, 'yaxis') and tr.yaxis == 'y2']
        print(f"  🏷️  Chart type: {'Dual-axis' if secondary_traces else 'Single-axis'} (forced)")
    print()
    
    # Example 2: Manual unit specification
    print("Example 2: Manual Unit Specification")
    cfg2 = ChartConfig(
        id="manual_units",
        title="Manual Units - Custom Labels",
        chart_type="line",
        x_param="Elapsed Time (s)",
        y_params=["Stick Force (N)"],
        secondary_y_params=["Airspeed (kts)"],
        manual_y_unit="Newtons",
        manual_secondary_y_unit="Knots",
        auto_detect_units=False,
        y_axis_label="Force",
        secondary_y_axis_label="Speed"
    )
    
    fig2 = cm.create_chart(df, cfg2)
    if fig2:
        print(f"  ✅ Created chart with manual unit specifications")
        print(f"  🏷️  Primary axis: Force (Newtons)")
        print(f"  🏷️  Secondary axis: Speed (Knots)")
    print()
    
    # Example 3: Legend unit control
    print("Example 3: Legend Unit Display Control")
    cfg3a = ChartConfig(
        id="legend_with_units",
        title="Legend With Units",
        chart_type="line",
        x_param="Elapsed Time (s)",
        y_params=["Engine Temperature (DGC)", "Oil Temperature (C)"],
        show_units_in_legend=True
    )
    
    cfg3b = ChartConfig(
        id="legend_without_units", 
        title="Legend Without Units",
        chart_type="line",
        x_param="Elapsed Time (s)",
        y_params=["Engine Temperature (DGC)", "Oil Temperature (C)"],
        show_units_in_legend=False
    )
    
    fig3a = cm.create_chart(df, cfg3a)
    fig3b = cm.create_chart(df, cfg3b)
    
    if fig3a and fig3b:
        names_with = [tr.name for tr in fig3a.data]
        names_without = [tr.name for tr in fig3b.data]
        print(f"  🏷️  With units: {names_with}")
        print(f"  🏷️  Without units: {names_without}")
    print()


def demonstrate_scale_synchronization():
    """Demonstrate scale synchronization features."""
    print("🔗 Scale Synchronization Demonstration")
    print("=" * 50)
    
    df = create_sample_flight_data()
    cm = ChartManager()
    
    # Create compatible data with different scales
    df_scaled = df.copy()
    df_scaled['Scaled Temperature (DGC)'] = df['Engine Temperature (DGC)'] * 0.1  # Much smaller scale
    
    # Example: Synchronized scales for compatible units
    cfg = ChartConfig(
        id="sync_scales",
        title="Synchronized Scales - Compatible Units",
        chart_type="line",
        x_param="Elapsed Time (s)",
        y_params=["Engine Temperature (DGC)"],
        secondary_y_params=["Scaled Temperature (DGC)"],
        synchronize_scales=True,
        manual_y_unit="DGC",
        manual_secondary_y_unit="DGC"
    )
    
    fig = cm.create_chart(df_scaled, cfg)
    if fig:
        print(f"  ✅ Created chart with synchronized scales")
        print(f"  🔗 Both axes use the same scale range for easy comparison")
    print()


def main():
    """Run all demonstrations."""
    print("🚁 Enhanced Flight Analyzer - Unit Detection & Dual-Axis Demo")
    print("=" * 70)
    print()
    
    demonstrate_unit_detection()
    print()
    
    demonstrate_automatic_dual_axis()
    print()
    
    demonstrate_manual_override()
    print()
    
    demonstrate_scale_synchronization()
    print()
    
    print("✅ All demonstrations completed!")
    print()
    print("Key Features Demonstrated:")
    print("  • Automatic unit detection from parameter names")
    print("  • Dual-axis charts for incompatible units")
    print("  • Single-axis charts for compatible units")
    print("  • Manual unit specification and override")
    print("  • Legend unit display control")
    print("  • Scale synchronization for compatible units")
    print("  • Force dual-axis option")


if __name__ == "__main__":
    main()