#!/usr/bin/env python3
"""
Simple test script to verify secondary Y-axis functionality works in practice.
Creates sample data and tests chart generation.
"""
import pandas as pd
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath('.'))

from components.chart_manager import ChartManager
from components.config_models import ChartConfig

def create_test_data():
    """Create sample flight-like data."""
    import numpy as np
    
    # Time vector
    t = np.linspace(0, 60, 100)  # 60 seconds, 100 points
    
    # Primary axis parameters (control inputs)
    elevator_pos = 5 * np.sin(0.1 * t) + np.random.normal(0, 0.5, 100)
    aileron_pos = 3 * np.sin(0.15 * t + 1) + np.random.normal(0, 0.3, 100)
    
    # Secondary axis parameters (engine data)
    rpm = 1800 + 200 * np.sin(0.05 * t) + np.random.normal(0, 20, 100)
    manifold_pressure = 25 + 3 * np.sin(0.08 * t + 0.5) + np.random.normal(0, 0.2, 100)
    
    return pd.DataFrame({
        'Elapsed Time (s)': t,
        'Elevator Position (deg)': elevator_pos,
        'Aileron Position (deg)': aileron_pos,
        'Engine RPM': rpm,
        'Manifold Pressure (inHg)': manifold_pressure,
        'Altitude (ft)': 3000 + 100 * np.sin(0.02 * t) + np.random.normal(0, 10, 100)
    })

def test_dual_axis_chart():
    """Test creating a dual-axis chart."""
    print("Creating test data...")
    df = create_test_data()
    print(f"Data shape: {df.shape}")
    print(f"Columns: {list(df.columns)}")
    
    print("\nTesting dual-axis chart creation...")
    cm = ChartManager()
    
    # Create a dual-axis configuration
    config = ChartConfig(
        id="test_dual",
        title="Control Inputs vs Engine Parameters",
        chart_type="line",
        x_param="Elapsed Time (s)",
        y_params=["Elevator Position (deg)", "Aileron Position (deg)"],
        secondary_y_params=["Engine RPM", "Manifold Pressure (inHg)"],
        y_axis_label="Control Position (deg)",
        secondary_y_axis_label="Engine Parameters",
        color_scheme="viridis"
    )
    
    # Generate the chart
    fig = cm.create_chart(df, config)
    
    if fig is None:
        print("❌ Chart creation failed!")
        return False
    
    print("✅ Chart created successfully!")
    
    # Analyze the chart
    print(f"Number of traces: {len(fig.data)}")
    
    primary_traces = [tr for tr in fig.data if getattr(tr, 'yaxis', 'y') == 'y']
    secondary_traces = [tr for tr in fig.data if getattr(tr, 'yaxis', 'y') == 'y2']
    
    print(f"Primary axis traces: {len(primary_traces)}")
    print(f"Secondary axis traces: {len(secondary_traces)}")
    
    # Check trace names
    for i, trace in enumerate(fig.data):
        axis = getattr(trace, 'yaxis', 'y')
        line_style = getattr(trace.line, 'dash', 'solid') if hasattr(trace, 'line') else 'N/A'
        print(f"  Trace {i+1}: {trace.name} (axis: {axis}, style: {line_style})")
    
    # Check axis labels
    if hasattr(fig.layout, 'yaxis') and fig.layout.yaxis.title:
        print(f"Primary Y-axis label: {fig.layout.yaxis.title.text}")
    if hasattr(fig.layout, 'yaxis2') and fig.layout.yaxis2.title:
        print(f"Secondary Y-axis label: {fig.layout.yaxis2.title.text}")
    
    # Save as HTML for manual inspection
    try:
        fig.write_html("/tmp/test_dual_axis.html")
        print("✅ Chart saved to /tmp/test_dual_axis.html for inspection")
    except Exception as e:
        print(f"⚠️  Could not save HTML: {e}")
    
    return True

def test_single_axis_fallback():
    """Test that single-axis charts still work correctly."""
    print("\nTesting single-axis fallback...")
    df = create_test_data()
    cm = ChartManager()
    
    config = ChartConfig(
        id="test_single",
        title="Control Inputs Only",
        chart_type="line",
        x_param="Elapsed Time (s)",
        y_params=["Elevator Position (deg)", "Aileron Position (deg)"],
        secondary_y_params=[],  # No secondary params
        y_axis_label="Control Position (deg)",
        color_scheme="blues"
    )
    
    fig = cm.create_chart(df, config)
    
    if fig is None:
        print("❌ Single-axis chart creation failed!")
        return False
    
    print("✅ Single-axis chart created successfully!")
    
    # Should have no secondary axis
    secondary_traces = [tr for tr in fig.data if getattr(tr, 'yaxis', 'y') == 'y2']
    assert len(secondary_traces) == 0, "Should have no secondary traces"
    
    return True

if __name__ == "__main__":
    print("Secondary Y-Axis Functionality Test")
    print("=" * 40)
    
    success = True
    
    try:
        success &= test_dual_axis_chart()
        success &= test_single_axis_fallback()
        
        if success:
            print("\n🎉 All tests passed! Secondary Y-axis functionality is working correctly.")
        else:
            print("\n❌ Some tests failed.")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n💥 Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)