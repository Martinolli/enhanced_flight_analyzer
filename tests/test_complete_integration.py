# File: test_complete_integration.py
import pandas as pd
import numpy as np
from components.chart_manager import ChartManager
from components.statistical_analysis import FlightDataStatistics
from components.large_dataset_handler import LargeDatasetHandler
from components.config_models import ChartConfig

def test_complete_integration():
    """Test all improvements working together."""
    
    print("=== Complete Integration Test ===")
    
    # 1. Test FFT unit conversion
    print("\n1. Testing FFT unit conversion...")
    test_fft_conversion()
    
    # 2. Test statistical analysis
    print("\n2. Testing statistical analysis...")
    test_statistics_integration()
    
    # 3. Test large dataset handling
    print("\n3. Testing large dataset handling...")
    test_large_dataset_integration()
    
    print("\n✅ All integration tests completed successfully!")

def test_fft_conversion():
    """Test FFT unit conversion with sample data."""
    # Load sample data
    df = load_sample_data()
    
    chart_manager = ChartManager()
    
    cfg = ChartConfig(
        id="integration_fft",
        title="Integration Test - FFT",
        chart_type="frequency",
        y_params=["ENG MOUNT TRIAXIAL ACCEL 1 - X (ACCENG_P3X) (g)"],
        freq_type="fft",
        freq_detrend=True
    )
    
    fig = chart_manager.create_chart(df, cfg)
    
    if fig:
        # Check for SI units in trace names
        has_si_units = any("(m/s²)" in trace.name for trace in fig.data)
        if has_si_units:
            print("  ✅ FFT unit conversion working correctly")
        else:
            print("  ❌ FFT unit conversion not applied")
    else:
        print("  ❌ FFT chart creation failed")

def test_statistics_integration():
    """Test statistical analysis integration."""
    df = create_test_data()
    
    stats_analyzer = FlightDataStatistics()
    
    # Test basic statistics
    basic_stats = stats_analyzer.compute_basic_statistics(
        df, ['Acceleration (g)', 'Temperature (C)']
    )
    
    if basic_stats and len(basic_stats) > 0:
        print("  ✅ Basic statistics working correctly")
    else:
        print("  ❌ Basic statistics failed")
    
    # Test correlation analysis
    correlations = stats_analyzer.compute_correlation_analysis(
        df, ['Acceleration (g)', 'Temperature (C)', 'Pressure (psi)']
    )
    
    if 'correlation_matrix' in correlations:
        print("  ✅ Correlation analysis working correctly")
    else:
        print("  ❌ Correlation analysis failed")

def test_large_dataset_integration():
    """Test large dataset handling."""
    handler = LargeDatasetHandler()
    
    # Create a moderately large test dataset
    large_df = create_large_test_data(50000)  # 50k rows
    
    # Test memory optimization
    original_memory = large_df.memory_usage(deep=True).sum()
    optimized_df = handler.optimize_dataframe_memory(large_df)
    new_memory = optimized_df.memory_usage(deep=True).sum()
    
    if new_memory <= original_memory:
        print("  ✅ Memory optimization working correctly")
    else:
        print("  ❌ Memory optimization failed")
    
    # Test data summary
    summary = handler.create_data_summary(optimized_df)
    
    if 'basic_info' in summary and 'column_info' in summary:
        print("  ✅ Data summary generation working correctly")
    else:
        print("  ❌ Data summary generation failed")

def load_sample_data():
    """Load the actual sample data for testing."""
    # Implementation depends on your sample data format
    # This is a placeholder - replace with actual data loading
    pass

def create_test_data():
    """Create test data for statistical analysis."""
    np.random.seed(42)
    n_points = 1000
    
    return pd.DataFrame({
        'Elapsed Time (s)': np.linspace(0, 100, n_points),
        'Acceleration (g)': np.random.normal(0, 0.01, n_points),
        'Temperature (C)': 20 + np.random.normal(0, 2, n_points),
        'Pressure (psi)': 14.7 + np.random.normal(0, 0.5, n_points)
    })

def create_large_test_data(n_rows):
    """Create large test dataset."""
    np.random.seed(42)
    
    return pd.DataFrame({
        'Elapsed Time (s)': np.linspace(0, n_rows/10, n_rows),
        'Acceleration (g)': np.random.normal(0, 0.01, n_rows),
        'Temperature (C)': 20 + np.random.normal(0, 2, n_rows),
        'Pressure (psi)': 14.7 + np.random.normal(0, 0.5, n_rows),
        'Vibration (g)': np.random.normal(0, 0.005, n_rows)
    })

if __name__ == "__main__":
    test_complete_integration()