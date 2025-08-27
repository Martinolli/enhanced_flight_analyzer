# File: test_statistics.py
from components.statistical_analysis import FlightDataStatistics
import pandas as pd
import numpy as np

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def test_statistical_analysis():
    """Test the statistical analysis functionality."""
    
    # Create sample data
    np.random.seed(42)
    n_points = 1000
    
    df = pd.DataFrame({
        'Elapsed Time (s)': np.linspace(0, 100, n_points),
        'Acceleration (g)': np.random.normal(0, 0.01, n_points),
        'Temperature (C)': 20 + np.random.normal(0, 2, n_points),
        'Pressure (psi)': 14.7 + np.random.normal(0, 0.5, n_points)
    })
    
    # Add some outliers
    df.loc[50, 'Acceleration (g)'] = 0.5  # Outlier
    df.loc[100, 'Temperature (C)'] = 50   # Outlier
    
    stats_analyzer = FlightDataStatistics()
    
    # Test basic statistics
    print("Testing basic statistics...")
    basic_stats = stats_analyzer.compute_basic_statistics(
        df, ['Acceleration (g)', 'Temperature (C)', 'Pressure (psi)']
    )
    
    for param, stats in basic_stats.items():
        print(f"{param}: mean={stats['mean']:.4f}, std={stats['std']:.4f}")
    
    # Test outlier detection
    print("\nTesting outlier detection...")
    outliers = stats_analyzer.detect_outliers(
        df, ['Acceleration (g)', 'Temperature (C)'], method='iqr'
    )
    
    for param, outlier_info in outliers.items():
        print(f"{param}: {outlier_info['outlier_count']} outliers detected")
    
    # Test correlation analysis
    print("\nTesting correlation analysis...")
    correlations = stats_analyzer.compute_correlation_analysis(
        df, ['Acceleration (g)', 'Temperature (C)', 'Pressure (psi)']
    )
    
    if 'strongest_correlations' in correlations:
        for corr in correlations['strongest_correlations'][:3]:
            print(f"{corr['param1']} vs {corr['param2']}: r={corr['correlation']:.4f}")
    
    print("✅ Statistical analysis tests completed!")

if __name__ == "__main__":
    test_statistical_analysis()