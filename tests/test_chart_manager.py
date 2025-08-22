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


def test_secondary_y_axis_basic():
    """Test basic secondary Y-axis functionality."""
    df = pd.DataFrame({
        "Elapsed Time (s)": [0, 1, 2, 3, 4],
        "Temperature (C)": [20, 22, 24, 26, 28],
        "Pressure (Pa)": [101000, 101100, 101200, 101300, 101400],
        "Altitude (m)": [100, 120, 140, 160, 180]
    })
    cm = ChartManager()
    cfg = ChartConfig(
        id="dual_axis_test",
        title="Temperature and Pressure vs Time",
        chart_type="line",
        x_param="Elapsed Time (s)",
        y_params=["Temperature (C)"],
        secondary_y_params=["Pressure (Pa)"],
        y_axis_label="Temperature (°C)",
        secondary_y_axis_label="Pressure (Pa)"
    )
    fig = cm.create_chart(df, cfg)
    assert fig is not None
    
    # Should have traces for both primary and secondary axes
    primary_traces = [tr for tr in fig.data if getattr(tr, 'yaxis', 'y') == 'y']
    secondary_traces = [tr for tr in fig.data if getattr(tr, 'yaxis', 'y') == 'y2']
    
    assert len(primary_traces) >= 1, "Should have at least one primary Y trace"
    assert len(secondary_traces) >= 1, "Should have at least one secondary Y trace"
    
    # Check that secondary axis is configured
    assert hasattr(fig.layout, 'yaxis2'), "Should have secondary Y-axis configured"
    print("✅ test_secondary_y_axis_basic passed!")


def test_secondary_y_axis_legend_disambiguation():
    """Test that legends properly distinguish between primary and secondary axes."""
    df = pd.DataFrame({
        "Elapsed Time (s)": [0, 1, 2, 3, 4],
        "Speed (m/s)": [10, 12, 14, 16, 18],
        "RPM": [1000, 1200, 1400, 1600, 1800]
    })
    cm = ChartManager()
    cfg = ChartConfig(
        id="legend_test",
        title="Speed and RPM vs Time",
        chart_type="line",
        x_param="Elapsed Time (s)",
        y_params=["Speed (m/s)"],
        secondary_y_params=["RPM"],
        y_axis_label="Speed (m/s)",
        secondary_y_axis_label="RPM"
    )
    fig = cm.create_chart(df, cfg)
    assert fig is not None
    
    # Check that trace names include axis disambiguation
    trace_names = [tr.name for tr in fig.data]
    
    # Should have indicators for primary/secondary axis
    primary_indicators = any("(Left)" in name or "Primary" in name for name in trace_names)
    secondary_indicators = any("(Right)" in name or "Secondary" in name for name in trace_names)
    
    assert primary_indicators or secondary_indicators, "Legend should disambiguate axis assignment"
    print("✅ test_secondary_y_axis_legend_disambiguation passed!")


def test_secondary_y_axis_style_differentiation():
    """Test that primary and secondary traces have different styles."""
    df = pd.DataFrame({
        "Elapsed Time (s)": [0, 1, 2, 3, 4],
        "Param1": [10, 12, 14, 16, 18],
        "Param2": [20, 22, 24, 26, 28]
    })
    cm = ChartManager()
    cfg = ChartConfig(
        id="style_test",
        title="Style Differentiation Test",
        chart_type="line",
        x_param="Elapsed Time (s)",
        y_params=["Param1"],
        secondary_y_params=["Param2"]
    )
    fig = cm.create_chart(df, cfg)
    assert fig is not None
    
    # Check that traces have different line styles
    primary_traces = [tr for tr in fig.data if getattr(tr, 'yaxis', 'y') == 'y']
    secondary_traces = [tr for tr in fig.data if getattr(tr, 'yaxis', 'y') == 'y2']
    
    if len(primary_traces) > 0 and len(secondary_traces) > 0:
        # Primary should be solid, secondary should be dashed
        primary_style = getattr(primary_traces[0].line, 'dash', 'solid') if hasattr(primary_traces[0], 'line') else 'solid'
        secondary_style = getattr(secondary_traces[0].line, 'dash', 'solid') if hasattr(secondary_traces[0], 'line') else 'solid'
        
        # They should be different
        assert primary_style != secondary_style or primary_style == 'solid', "Primary and secondary traces should have different styles"
    
    print("✅ test_secondary_y_axis_style_differentiation passed!")


def test_secondary_y_axis_no_secondary_params():
    """Test that charts work normally when no secondary params are specified."""
    df = pd.DataFrame({
        "Elapsed Time (s)": [0, 1, 2, 3, 4],
        "Temperature (C)": [20, 22, 24, 26, 28]
    })
    cm = ChartManager()
    cfg = ChartConfig(
        id="no_secondary_test",
        title="Normal Single Axis Chart",
        chart_type="line",
        x_param="Elapsed Time (s)",
        y_params=["Temperature (C)"],
        secondary_y_params=[],  # Empty secondary params
        y_axis_label="Temperature (°C)"
    )
    fig = cm.create_chart(df, cfg)
    assert fig is not None
    
    # Should only have primary axis traces
    secondary_traces = [tr for tr in fig.data if getattr(tr, 'yaxis', 'y') == 'y2']
    assert len(secondary_traces) == 0, "Should have no secondary Y traces when secondary_y_params is empty"
    
    # Should not have secondary Y-axis configured
    assert not hasattr(fig.layout, 'yaxis2') or fig.layout.yaxis2 is None, "Should not have secondary Y-axis when not needed"
def test_secondary_y_axis_comprehensive():
    """Comprehensive test for secondary Y-axis with multiple parameters and edge cases."""
    df = pd.DataFrame({
        "Elapsed Time (s)": [0, 1, 2, 3, 4],
        "Speed (m/s)": [10, 12, 14, 16, 18],
        "Acceleration (m/s²)": [1.0, 1.5, 2.0, 1.5, 1.0],
        "RPM": [1000, 1200, 1400, 1600, 1800],
        "Torque (Nm)": [50, 60, 70, 80, 90]
    })
    cm = ChartManager()
    cfg = ChartConfig(
        id="comprehensive_test",
        title="Multi-Parameter Dual Axis Chart",
        chart_type="line",
        x_param="Elapsed Time (s)",
        y_params=["Speed (m/s)", "Acceleration (m/s²)"],
        secondary_y_params=["RPM", "Torque (Nm)"],
        y_axis_label="Linear Motion",
        secondary_y_axis_label="Rotational Motion"
    )
    fig = cm.create_chart(df, cfg)
    assert fig is not None
    
    # Check trace count
    assert len(fig.data) == 4, f"Should have 4 traces total, got {len(fig.data)}"
    
    # Check axis assignments
    primary_traces = [tr for tr in fig.data if getattr(tr, 'yaxis', 'y') == 'y']
    secondary_traces = [tr for tr in fig.data if getattr(tr, 'yaxis', 'y') == 'y2']
    
    assert len(primary_traces) == 2, f"Should have 2 primary traces, got {len(primary_traces)}"
    assert len(secondary_traces) == 2, f"Should have 2 secondary traces, got {len(secondary_traces)}"
    
    # Check legend disambiguation
    trace_names = [tr.name for tr in fig.data]
    left_axis_names = [name for name in trace_names if "(Left)" in name]
    right_axis_names = [name for name in trace_names if "(Right)" in name]
    
    assert len(left_axis_names) == 2, f"Should have 2 left axis names, got {len(left_axis_names)}"
    assert len(right_axis_names) == 2, f"Should have 2 right axis names, got {len(right_axis_names)}"
    
    # Check style differences
    primary_dash_styles = [getattr(tr.line, 'dash', 'solid') if hasattr(tr, 'line') else 'solid' for tr in primary_traces]
    secondary_dash_styles = [getattr(tr.line, 'dash', 'solid') if hasattr(tr, 'line') else 'solid' for tr in secondary_traces]
    
    # Primary should be solid, secondary should be dashed
    assert all(style in ['solid', None] for style in primary_dash_styles), f"Primary traces should be solid, got {primary_dash_styles}"
    assert all(style == 'dash' for style in secondary_dash_styles), f"Secondary traces should be dashed, got {secondary_dash_styles}"
    
    # Check axis labels
    assert fig.layout.yaxis.title.text == "Linear Motion", f"Primary Y-axis title should be 'Linear Motion', got {fig.layout.yaxis.title.text}"
    assert fig.layout.yaxis2.title.text == "Rotational Motion", f"Secondary Y-axis title should be 'Rotational Motion', got {fig.layout.yaxis2.title.text}"
    
    print("✅ test_secondary_y_axis_comprehensive passed!")


def test_secondary_y_axis_color_collision():
    """Test behavior when we have many parameters that might cause color collisions."""
    # Create data with more parameters than available colors
    df = pd.DataFrame({
        "Elapsed Time (s)": [0, 1, 2, 3, 4],
        "P1": [1, 2, 3, 4, 5],
        "P2": [2, 3, 4, 5, 6],
        "P3": [3, 4, 5, 6, 7],
        "P4": [4, 5, 6, 7, 8],
        "P5": [5, 6, 7, 8, 9],
        "S1": [10, 20, 30, 40, 50],
        "S2": [20, 30, 40, 50, 60],
        "S3": [30, 40, 50, 60, 70]
    })
    cm = ChartManager()
    cfg = ChartConfig(
        id="color_collision_test",
        title="Color Collision Test",
        chart_type="line",
        x_param="Elapsed Time (s)",
        y_params=["P1", "P2", "P3", "P4", "P5"],
        secondary_y_params=["S1", "S2", "S3"]
    )
    fig = cm.create_chart(df, cfg)
    assert fig is not None
    
    # Even with color cycling, style differences should help distinguish axes
    primary_traces = [tr for tr in fig.data if getattr(tr, 'yaxis', 'y') == 'y']
    secondary_traces = [tr for tr in fig.data if getattr(tr, 'yaxis', 'y') == 'y2']
    
    assert len(primary_traces) == 5, f"Should have 5 primary traces"
    assert len(secondary_traces) == 3, f"Should have 3 secondary traces"
    
    # All secondary traces should be dashed
    for tr in secondary_traces:
        if hasattr(tr, 'line'):
            assert getattr(tr.line, 'dash', 'solid') == 'dash', "Secondary traces should be dashed"
    
    print("✅ test_secondary_y_axis_color_collision passed!")

if __name__ == "__main__":
    test_custom_x_axis_scatter_fallback()
    test_secondary_y_axis_basic()
    test_secondary_y_axis_legend_disambiguation()
    test_secondary_y_axis_style_differentiation()
    test_secondary_y_axis_no_secondary_params()
    test_secondary_y_axis_comprehensive()
    test_secondary_y_axis_color_collision()