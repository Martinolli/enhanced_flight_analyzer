#!/usr/bin/env python3
"""
Integration test for the unit detection and dual-axis chart functionality.
"""

import sys
import os
import pandas as pd
import numpy as np

# Add project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from components.chart_manager import ChartManager
from components.config_models import ChartConfig


def test_end_to_end_integration():
    """Test the complete integration of unit detection and chart creation."""
    print("🧪 Running End-to-End Integration Test")
    print("=" * 50)
    
    # Create test data with realistic flight parameters
    df = pd.DataFrame({
        'Elapsed Time (s)': [0, 1, 2, 3, 4, 5],
        'Engine Temperature (DGC)': [650, 655, 660, 658, 652, 649],
        'Oil Temperature (C)': [85, 87, 89, 88, 86, 84],
        'Pitch Angle (deg)': [2.5, 3.0, 2.8, 2.2, 2.7, 2.9],
        'Roll Angle (deg)': [0.1, -0.2, 0.3, -0.1, 0.2, 0.0],
        'Airspeed (kts)': [120, 122, 125, 123, 121, 119],
        'Altitude (ft)': [5000, 5100, 5200, 5150, 5050, 4950],
        'Fuel Flow (gph)': [45, 46, 47, 46, 45, 44],
        'Manifold Pressure (inHg)': [28.5, 28.7, 28.9, 28.6, 28.4, 28.3]
    })
    
    cm = ChartManager()
    
    # Test 1: Automatic dual-axis for mixed units
    print("Test 1: Mixed Units - Should Create Dual-Axis")
    config1 = ChartConfig(
        id="test1",
        title="Engine Monitoring",
        y_params=["Engine Temperature (DGC)", "Airspeed (kts)"]
    )
    
    fig1 = cm.create_chart(df, config1)
    assert fig1 is not None, "Chart creation failed"
    
    secondary_traces = [tr for tr in fig1.data if hasattr(tr, 'yaxis') and tr.yaxis == 'y2']
    assert len(secondary_traces) > 0, "Should have created dual-axis chart"
    print("  ✅ Successfully created dual-axis chart for mixed units")
    
    # Test 2: Single axis for compatible units
    print("Test 2: Compatible Units - Should Use Single Axis")
    config2 = ChartConfig(
        id="test2",
        title="Temperature Monitoring",
        y_params=["Engine Temperature (DGC)", "Oil Temperature (C)"]
    )
    
    fig2 = cm.create_chart(df, config2)
    assert fig2 is not None, "Chart creation failed"
    
    secondary_traces = [tr for tr in fig2.data if hasattr(tr, 'yaxis') and tr.yaxis == 'y2']
    assert len(secondary_traces) == 0, "Should have used single axis for compatible units"
    print("  ✅ Successfully used single axis for compatible units")
    
    # Test 3: Manual unit specification
    print("Test 3: Manual Unit Specification")
    config3 = ChartConfig(
        id="test3",
        title="Manual Control",
        y_params=["Engine Temperature (DGC)"],
        secondary_y_params=["Altitude (ft)"],
        manual_y_unit="Celsius",
        manual_secondary_y_unit="Feet",
        auto_detect_units=False
    )
    
    fig3 = cm.create_chart(df, config3)
    assert fig3 is not None, "Chart creation failed"
    
    secondary_traces = [tr for tr in fig3.data if hasattr(tr, 'yaxis') and tr.yaxis == 'y2']
    assert len(secondary_traces) == 1, "Should have created dual-axis with manual specification"
    print("  ✅ Successfully handled manual unit specification")
    
    # Test 4: Force dual-axis for compatible units
    print("Test 4: Force Dual-Axis for Compatible Units")
    config4 = ChartConfig(
        id="test4",
        title="Forced Dual-Axis",
        y_params=["Pitch Angle (deg)", "Roll Angle (deg)"],
        force_unit_detection=True
    )
    
    fig4 = cm.create_chart(df, config4)
    assert fig4 is not None, "Chart creation failed"
    
    secondary_traces = [tr for tr in fig4.data if hasattr(tr, 'yaxis') and tr.yaxis == 'y2']
    assert len(secondary_traces) > 0, "Should have forced dual-axis for compatible units"
    print("  ✅ Successfully forced dual-axis for compatible units")
    
    # Test 5: Legend unit display control
    print("Test 5: Legend Unit Display Control")
    config5a = ChartConfig(
        id="test5a",
        title="With Units in Legend",
        y_params=["Engine Temperature (DGC)", "Airspeed (kts)"],
        show_units_in_legend=True
    )
    
    config5b = ChartConfig(
        id="test5b",
        title="Without Units in Legend",
        y_params=["Engine Temperature (DGC)", "Airspeed (kts)"],
        show_units_in_legend=False
    )
    
    fig5a = cm.create_chart(df, config5a)
    fig5b = cm.create_chart(df, config5b)
    
    assert fig5a is not None and fig5b is not None, "Chart creation failed"
    
    names_with = [tr.name for tr in fig5a.data]
    names_without = [tr.name for tr in fig5b.data]
    
    # Check that units are included/excluded as expected
    assert any("DGC" in name for name in names_with), "Units should be in legend"
    assert not any("DGC" in name for name in names_without), "Units should not be in legend"
    print("  ✅ Successfully controlled unit display in legend")
    
    # Test 6: Multiple unit categories
    print("Test 6: Multiple Unit Categories")
    config6 = ChartConfig(
        id="test6",
        title="Multiple Categories",
        y_params=["Engine Temperature (DGC)", "Airspeed (kts)", "Manifold Pressure (inHg)"]
    )
    
    fig6 = cm.create_chart(df, config6)
    assert fig6 is not None, "Chart creation failed"
    
    assert len(fig6.data) == 3, "Should have all three parameters"
    secondary_traces = [tr for tr in fig6.data if hasattr(tr, 'yaxis') and tr.yaxis == 'y2']
    assert len(secondary_traces) > 0, "Should have created dual-axis for multiple categories"
    print("  ✅ Successfully handled multiple unit categories")
    
    print("\n🎉 All integration tests passed!")
    print("\nFeatures Verified:")
    print("  ✓ Automatic unit detection from parameter names")
    print("  ✓ Dual-axis creation for incompatible units")
    print("  ✓ Single-axis for compatible units") 
    print("  ✓ Manual unit specification override")
    print("  ✓ Force dual-axis option")
    print("  ✓ Legend unit display control")
    print("  ✓ Multiple unit category handling")


if __name__ == "__main__":
    test_end_to_end_integration()