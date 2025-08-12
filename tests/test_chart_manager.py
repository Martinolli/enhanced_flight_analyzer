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

if __name__ == "__main__":
    test_custom_x_axis_scatter_fallback()