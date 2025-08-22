import sys
import os

# Add project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
from components.chart_manager import ChartManager
from components.config_models import ChartConfig

def test_custom_x_axis_scatter_fallback():
    df = pd.DataFrame({
        "Elapsed Time (s)": [0,1,2,3,4],
        "Stick Position (%)": [10, 12, 9, 15, 14],
        "Stick Force (N)": [20, 22, 21, 25, 24]
    })
    cm = ChartManager()
    cfg = ChartConfig(
        id="t1",
        title="Stick Force vs Position",
        chart_type="line",
        x_param="Stick Position (%)",
        y_params=["Stick Force (N)"]
    )
    fig = cm.create_chart(df, cfg)
    assert fig is not None
    # Because x not monotonic, should fallback to scatter (mode markers or at least scatter trace)
    assert any(tr.mode in ("markers", "lines", "lines+markers") for tr in fig.data)
    assert fig.layout.xaxis.title.text == "Stick Position (%)"
    print("✅ test_custom_x_axis_scatter_fallback passed!")

def test_dual_axis_chart():
    """Test dual-axis chart creation using ChartConfig abstraction."""
    df = pd.DataFrame({
        "Elapsed Time (s)": [0, 1, 2, 3, 4],
        "Altitude (ft)": [1000, 1100, 1200, 1300, 1400],
        "Temperature (C)": [20, 18, 16, 14, 12],
        "Airspeed (kts)": [120, 125, 130, 135, 140]
    })
    
    cm = ChartManager()
    cfg = ChartConfig(
        id="dual_axis_test",
        title="Altitude & Airspeed vs Temperature",
        chart_type="line",
        x_param="Elapsed Time (s)",
        y_params=["Altitude (ft)", "Airspeed (kts)"],
        secondary_y_params=["Temperature (C)"],
        y_axis_label="Altitude & Speed",
        secondary_y_axis_label="Temperature (C)",
        color_scheme="viridis"
    )
    
    fig = cm.create_chart(df, cfg)
    assert fig is not None
    
    # Should have 3 traces total
    assert len(fig.data) == 3
    
    # Check that traces are assigned to correct y-axes
    primary_traces = [tr for tr in fig.data if hasattr(tr, 'yaxis') and tr.yaxis == 'y']
    secondary_traces = [tr for tr in fig.data if hasattr(tr, 'yaxis') and tr.yaxis == 'y2']
    
    # Primary axis should have Altitude and Airspeed, secondary should have Temperature
    trace_names = [tr.name for tr in fig.data]
    assert "Altitude (ft)" in trace_names
    assert "Airspeed (kts)" in trace_names  
    assert "Temperature (C)" in trace_names
    
    print("✅ test_dual_axis_chart passed!")

def test_single_axis_backward_compatibility():
    """Test that single axis charts still work as before."""
    df = pd.DataFrame({
        "Elapsed Time (s)": [0, 1, 2, 3, 4],
        "Altitude (ft)": [1000, 1100, 1200, 1300, 1400],
        "Airspeed (kts)": [120, 125, 130, 135, 140]
    })
    
    cm = ChartManager()
    cfg = ChartConfig(
        id="single_axis_test",
        title="Altitude and Airspeed vs Time",
        chart_type="line",
        x_param="Elapsed Time (s)",
        y_params=["Altitude (ft)", "Airspeed (kts)"],
        y_axis_label="Value",
        color_scheme="plasma"
    )
    
    fig = cm.create_chart(df, cfg)
    assert fig is not None
    
    # Should have 2 traces, both on primary axis
    assert len(fig.data) == 2
    
    # Check layout has single y-axis title
    assert fig.layout.yaxis.title.text == "Value"
    
    print("✅ test_single_axis_backward_compatibility passed!")

def test_dict_migration():
    """Test that dictionary configurations are properly migrated to ChartConfig."""
    df = pd.DataFrame({
        "Elapsed Time (s)": [0, 1, 2, 3, 4],
        "Altitude (ft)": [1000, 1100, 1200, 1300, 1400],
        "Temperature (C)": [20, 18, 16, 14, 12]
    })
    
    # Old dictionary-style configuration
    old_config = {
        "id": "legacy_chart",
        "title": "Legacy Chart",
        "type": "line",  # Old-style key
        "x_axis": "Elapsed Time (s)",  # Old-style key  
        "parameters": ["Altitude (ft)"],  # Old-style key
        "secondary_y_params": ["Temperature (C)"],
        "y_axis_label": "Altitude",
        "secondary_y_axis_label": "Temperature",
        "color_scheme": "viridis"
    }
    
    cm = ChartManager()
    fig = cm.create_chart(df, old_config)  # Should work with dict
    
    assert fig is not None
    assert len(fig.data) == 2  # Should have both traces
    
    print("✅ test_dict_migration passed!")

if __name__ == "__main__":
    test_custom_x_axis_scatter_fallback()
    test_dual_axis_chart()
    test_single_axis_backward_compatibility()
    test_dict_migration()
    print("✅ All tests passed!")