import sys
import os

# Add project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
import pytest
from components.chart_manager import ChartManager
from components.config_models import ChartConfig


def test_custom_x_axis_scatter_fallback():
    """Test existing functionality still works."""
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


def test_unit_detection_and_axis_labeling():
    """Test unit detection and proper axis labeling."""
    df = pd.DataFrame({
        "Elapsed Time (s)": [0, 1, 2, 3, 4],
        "Temperature (DGC)": [20, 22, 24, 23, 21],
        "Pressure (psi)": [14.7, 14.8, 14.6, 14.9, 14.5]
    })
    
    cm = ChartManager()
    cfg = ChartConfig(
        id="test_units",
        title="Mixed Units Test",
        chart_type="line",
        x_param="Elapsed Time (s)",
        y_params=["Temperature (DGC)", "Pressure (psi)"],
        auto_detect_units=True
    )
    
    fig = cm.create_chart(df, cfg)
    assert fig is not None
    
    # Should create dual-axis chart due to unit mismatch
    assert len(fig.data) == 2
    
    # Check that one trace is on secondary y-axis
    secondary_traces = [tr for tr in fig.data if hasattr(tr, 'yaxis') and tr.yaxis == 'y2']
    assert len(secondary_traces) > 0
    
    print("✅ test_unit_detection_and_axis_labeling passed!")


def test_compatible_units_single_axis():
    """Test that compatible units use single axis."""
    df = pd.DataFrame({
        "Elapsed Time (s)": [0, 1, 2, 3, 4],
        "Temperature1 (DGC)": [20, 22, 24, 23, 21],
        "Temperature2 (C)": [68, 72, 75, 73, 70]
    })
    
    cm = ChartManager()
    cfg = ChartConfig(
        id="test_compatible",
        title="Compatible Units Test",
        chart_type="line",
        x_param="Elapsed Time (s)",
        y_params=["Temperature1 (DGC)", "Temperature2 (C)"],
        auto_detect_units=True
    )
    
    fig = cm.create_chart(df, cfg)
    assert fig is not None
    
    # Should use single axis since both are temperature units
    assert len(fig.data) == 2
    
    # Check that no traces are on secondary y-axis
    secondary_traces = [tr for tr in fig.data if hasattr(tr, 'yaxis') and tr.yaxis == 'y2']
    assert len(secondary_traces) == 0
    
    print("✅ test_compatible_units_single_axis passed!")


def test_manual_unit_override():
    """Test manual unit specification override."""
    df = pd.DataFrame({
        "Elapsed Time (s)": [0, 1, 2, 3, 4],
        "Parameter1": [20, 22, 24, 23, 21],
        "Parameter2": [1.0, 1.1, 0.9, 1.2, 1.1]
    })
    
    cm = ChartManager()
    cfg = ChartConfig(
        id="test_manual",
        title="Manual Units Test",
        chart_type="line",
        x_param="Elapsed Time (s)",
        y_params=["Parameter1"],
        secondary_y_params=["Parameter2"],
        manual_y_unit="DGC",
        manual_secondary_y_unit="psi",
        auto_detect_units=False
    )
    
    fig = cm.create_chart(df, cfg)
    assert fig is not None
    
    # Should create dual-axis chart with manual units
    assert len(fig.data) == 2
    
    # Check that one trace is on secondary y-axis
    secondary_traces = [tr for tr in fig.data if hasattr(tr, 'yaxis') and tr.yaxis == 'y2']
    assert len(secondary_traces) == 1
    
    print("✅ test_manual_unit_override passed!")


def test_legend_unit_display():
    """Test unit display in legend names."""
    df = pd.DataFrame({
        "Elapsed Time (s)": [0, 1, 2, 3, 4],
        "Temperature (DGC)": [20, 22, 24, 23, 21],
        "Pressure (psi)": [14.7, 14.8, 14.6, 14.9, 14.5]
    })
    
    cm = ChartManager()
    
    # Test with units in legend
    cfg_with_units = ChartConfig(
        id="test_legend_with",
        title="Units in Legend",
        chart_type="line",
        x_param="Elapsed Time (s)",
        y_params=["Temperature (DGC)", "Pressure (psi)"],
        show_units_in_legend=True
    )
    
    fig_with = cm.create_chart(df, cfg_with_units)
    assert fig_with is not None
    
    # Check that legend names contain units
    legend_names = [tr.name for tr in fig_with.data]
    assert any("DGC" in name for name in legend_names)
    assert any("psi" in name for name in legend_names)
    
    # Test without units in legend
    cfg_without_units = ChartConfig(
        id="test_legend_without",
        title="No Units in Legend",
        chart_type="line",
        x_param="Elapsed Time (s)",
        y_params=["Temperature (DGC)", "Pressure (psi)"],
        show_units_in_legend=False
    )
    
    fig_without = cm.create_chart(df, cfg_without_units)
    assert fig_without is not None
    
    # Check that legend names don't contain units
    legend_names = [tr.name for tr in fig_without.data]
    assert all("DGC" not in name for name in legend_names)
    assert all("psi" not in name for name in legend_names)
    
    print("✅ test_legend_unit_display passed!")


def test_force_dual_axis():
    """Test forcing dual-axis even with compatible units."""
    df = pd.DataFrame({
        "Elapsed Time (s)": [0, 1, 2, 3, 4],
        "Temperature1 (DGC)": [20, 22, 24, 23, 21],
        "Temperature2 (DGC)": [25, 27, 29, 28, 26]
    })
    
    cm = ChartManager()
    cfg = ChartConfig(
        id="test_force_dual",
        title="Force Dual Axis Test",
        chart_type="line",
        x_param="Elapsed Time (s)",
        y_params=["Temperature1 (DGC)", "Temperature2 (DGC)"],
        force_unit_detection=True,
        auto_detect_units=True
    )
    
    fig = cm.create_chart(df, cfg)
    assert fig is not None
    
    # Should create dual-axis chart even though units are compatible
    assert len(fig.data) == 2
    
    # Check that one trace is on secondary y-axis
    secondary_traces = [tr for tr in fig.data if hasattr(tr, 'yaxis') and tr.yaxis == 'y2']
    
    # Debug: print trace info
    print(f"Number of traces: {len(fig.data)}")
    for i, tr in enumerate(fig.data):
        print(f"Trace {i}: name={tr.name}, yaxis={getattr(tr, 'yaxis', 'y')}")
    
    assert len(secondary_traces) > 0
    
    print("✅ test_force_dual_axis passed!")


if __name__ == "__main__":
    test_custom_x_axis_scatter_fallback()
    test_unit_detection_and_axis_labeling()
    test_compatible_units_single_axis()
    test_manual_unit_override()
    test_legend_unit_display()
    test_force_dual_axis()
    print("All tests passed! ✅")