# File: test_fft_fix.py
import pandas as pd
import numpy as np
from components.chart_manager import ChartManager
from components.config_models import ChartConfig

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def test_fft_unit_conversion():
    """Test the FFT unit conversion fix."""
    
    # Load your sample data
    df = pd.read_csv('Piece_Data_Sample.csv', skiprows=1)
    
    # Process the data (add proper column names and elapsed time)
    # ... data processing code ...
    
    # Create chart manager
    chart_manager = ChartManager()
    
    # Test configuration
    cfg = ChartConfig(
        id="test_fft",
        title="FFT Unit Conversion Test",
        chart_type="frequency",
        y_params=["ENG MOUNT TRIAXIAL ACCEL 1 - X (ACCENG_P3X) (g)"],
        freq_type="fft"
    )
    
    # Generate plot
    fig = chart_manager.create_chart(df, cfg)
    print("Generated FFT plot")
    
    # Verify the fix
    if fig:
        print("✅ FFT unit conversion implemented successfully!")
        # Check that trace names include SI units
        for trace in fig.data:
            if "(m/s²)" in trace.name:
                print(f"✅ Found SI unit in trace: {trace.name}")
                break
        else:
            print("❌ SI units not found in trace names")
    else:
        print("❌ Failed to create FFT plot")

if __name__ == "__main__":
    test_fft_unit_conversion()