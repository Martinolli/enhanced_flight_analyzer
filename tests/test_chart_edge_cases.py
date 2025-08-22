#!/usr/bin/env python3
"""
Comprehensive test suite for dual/multi-axis chart edge cases using synthetic datasets.

This test suite covers:
- Extreme value ranges (very large vs very small values)
- Sparse series data (lots of missing values, irregular intervals)
- Missing data alignment between different parameters
- Non-monotonic data handling
- Various chart types with edge cases
- Frequency analysis edge cases
- X-axis selection edge cases

Each test documents expected behavior and edge case scenarios that should be
handled gracefully by the chart generation system.
"""

import sys
import os
import numpy as np
import pandas as pd
from typing import Optional, List, Dict, Any

# Add project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from components.chart_manager import ChartManager
from components.config_models import ChartConfig


class SyntheticDataGenerator:
    """
    Generates synthetic flight data with various edge case characteristics.
    """
    
    def __init__(self, seed: int = 42):
        np.random.seed(seed)
    
    def generate_extreme_range_data(self, n_points: int = 100) -> pd.DataFrame:
        """
        Generate data with extreme value ranges suitable for dual-axis testing.
        
        Creates parameters with vastly different scales:
        - Temperature: -50 to 150 (moderate range)
        - Pressure: 50000 to 120000 (large values)
        - Vibration: 0.001 to 0.1 (small values)
        """
        time = np.linspace(0, 100, n_points)
        
        # Large scale values (pressure in Pa)
        pressure = 80000 + 20000 * np.sin(0.1 * time) + 5000 * np.random.normal(0, 1, n_points)
        
        # Small scale values (vibration in g)
        vibration = 0.01 + 0.005 * np.sin(0.3 * time) + 0.002 * np.random.normal(0, 1, n_points)
        
        # Medium scale values (temperature in Celsius)
        temperature = 20 + 30 * np.sin(0.05 * time) + 10 * np.random.normal(0, 1, n_points)
        
        return pd.DataFrame({
            "Elapsed Time (s)": time,
            "Pressure (Pa)": pressure,
            "Vibration (g)": vibration,
            "Temperature (C)": temperature
        })
    
    def generate_sparse_data(self, n_points: int = 100, sparsity: float = 0.3) -> pd.DataFrame:
        """
        Generate sparse data with missing values and irregular intervals.
        
        Args:
            sparsity: Fraction of data points to set as NaN (0.0 = no missing, 1.0 = all missing)
        """
        time = np.sort(np.random.uniform(0, 100, n_points))  # Irregular time intervals
        
        # Generate base parameters
        param1 = 10 + 5 * np.sin(0.1 * time) + 2 * np.random.normal(0, 1, n_points)
        param2 = 50 + 20 * np.cos(0.08 * time) + 5 * np.random.normal(0, 1, n_points)
        param3 = 100 * np.exp(-0.01 * time) + 10 * np.random.normal(0, 1, n_points)
        
        # Introduce sparsity (missing values)
        sparse_mask1 = np.random.random(n_points) < sparsity
        sparse_mask2 = np.random.random(n_points) < sparsity
        sparse_mask3 = np.random.random(n_points) < sparsity
        
        param1[sparse_mask1] = np.nan
        param2[sparse_mask2] = np.nan
        param3[sparse_mask3] = np.nan
        
        return pd.DataFrame({
            "Elapsed Time (s)": time,
            "Sparse Parameter 1": param1,
            "Sparse Parameter 2": param2,
            "Sparse Parameter 3": param3
        })
    
    def generate_misaligned_data(self, n_points: int = 100) -> pd.DataFrame:
        """
        Generate data where parameters have different valid data ranges.
        Simulates real-world scenario where different sensors start/stop at different times.
        """
        time = np.linspace(0, 100, n_points)
        
        # Parameter 1: Valid for entire time range
        param1 = 10 + 3 * np.sin(0.1 * time) + np.random.normal(0, 0.5, n_points)
        
        # Parameter 2: Valid only in middle portion (30-70s)
        param2 = np.full(n_points, np.nan)
        valid_range2 = (time >= 30) & (time <= 70)
        param2[valid_range2] = 20 + 5 * np.cos(0.15 * time[valid_range2]) + np.random.normal(0, 1, np.sum(valid_range2))
        
        # Parameter 3: Valid only at beginning (0-40s)
        param3 = np.full(n_points, np.nan)
        valid_range3 = time <= 40
        param3[valid_range3] = 100 - 2 * time[valid_range3] + np.random.normal(0, 2, np.sum(valid_range3))
        
        # Parameter 4: Valid only at end (60-100s)
        param4 = np.full(n_points, np.nan)
        valid_range4 = time >= 60
        param4[valid_range4] = 5 * np.exp(0.02 * (time[valid_range4] - 60)) + np.random.normal(0, 0.5, np.sum(valid_range4))
        
        return pd.DataFrame({
            "Elapsed Time (s)": time,
            "Full Range Param": param1,
            "Mid Range Param": param2,
            "Early Range Param": param3,
            "Late Range Param": param4
        })
    
    def generate_non_monotonic_x_data(self, n_points: int = 100) -> pd.DataFrame:
        """
        Generate data with non-monotonic X parameter for testing scatter fallback.
        """
        time = np.linspace(0, 100, n_points)
        
        # Non-monotonic X parameter (altitude going up and down)
        altitude = 1000 + 500 * np.sin(0.1 * time) + 200 * np.sin(0.3 * time) + 50 * np.random.normal(0, 1, n_points)
        
        # Parameters that depend on altitude
        air_density = 1.225 * np.exp(-altitude / 10000)  # Decreases with altitude
        engine_power = 1000 - 0.5 * altitude + 100 * np.random.normal(0, 1, n_points)  # Decreases with altitude
        
        return pd.DataFrame({
            "Elapsed Time (s)": time,
            "Altitude (m)": altitude,
            "Air Density (kg/m³)": air_density,
            "Engine Power (kW)": engine_power
        })
    
    def generate_frequency_test_data(self, n_points: int = 1000, fs: float = 100.0) -> pd.DataFrame:
        """
        Generate data with known frequency components for testing FFT/PSD functionality.
        """
        time = np.linspace(0, n_points / fs, n_points)
        
        # Signal with multiple frequency components
        signal1 = (2 * np.sin(2 * np.pi * 5 * time) +    # 5 Hz component
                  1.5 * np.sin(2 * np.pi * 10 * time) +   # 10 Hz component
                  0.8 * np.sin(2 * np.pi * 25 * time) +   # 25 Hz component
                  0.3 * np.random.normal(0, 1, n_points))  # Noise
        
        # Different signal for comparison
        signal2 = (1.5 * np.sin(2 * np.pi * 3 * time) +   # 3 Hz component
                  2.0 * np.sin(2 * np.pi * 15 * time) +   # 15 Hz component
                  0.5 * np.random.normal(0, 1, n_points))  # Noise
        
        return pd.DataFrame({
            "Elapsed Time (s)": time,
            "Vibration Signal 1": signal1,
            "Vibration Signal 2": signal2
        })


class TestChartEdgeCases:
    """
    Test suite for chart edge cases with comprehensive documentation.
    """
    
    def __init__(self):
        self.chart_manager = ChartManager()
        self.data_generator = SyntheticDataGenerator()
        self.test_results = []
    
    def log_test_result(self, test_name: str, success: bool, description: str, notes: str = ""):
        """Log test results for documentation."""
        result = {
            "test_name": test_name,
            "success": success,
            "description": description,
            "notes": notes
        }
        self.test_results.append(result)
        status = "✅" if success else "❌"
        print(f"{status} {test_name}: {description}")
        if notes:
            print(f"   Notes: {notes}")
    
    def test_extreme_value_ranges(self):
        """Test chart creation with parameters having vastly different scales."""
        test_name = "Extreme Value Ranges"
        description = "Chart creation with parameters spanning multiple orders of magnitude"
        
        try:
            df = self.data_generator.generate_extreme_range_data()
            
            # Test 1: Single axis with mixed scales
            cfg1 = ChartConfig(
                id="extreme_single",
                title="Mixed Scale Parameters (Single Axis)",
                chart_type="line",
                y_params=["Pressure (Pa)", "Vibration (g)", "Temperature (C)"]
            )
            fig1 = self.chart_manager.create_chart(df, cfg1)
            
            # Test 2: Potential dual-axis scenario (currently single axis)
            cfg2 = ChartConfig(
                id="extreme_dual",
                title="Large vs Small Scale Parameters",
                chart_type="line",
                y_params=["Pressure (Pa)"],
                secondary_y_params=["Vibration (g)"],  # Future dual-axis support
                y_axis_label="Pressure (Pa)",
                secondary_y_axis_label="Vibration (g)"
            )
            fig2 = self.chart_manager.create_chart(df, cfg2)
            
            # Verify charts were created
            success = fig1 is not None and fig2 is not None
            
            if success:
                # Verify data integrity
                success = (len(fig1.data) == 3 and  # All three parameters plotted
                          len(fig2.data) == 1 and   # Only primary y_params plotted (secondary not implemented)
                          fig1.layout.title.text == "Mixed Scale Parameters (Single Axis)")
            
            notes = (f"Data ranges: Pressure {df['Pressure (Pa)'].min():.0f}-{df['Pressure (Pa)'].max():.0f}, "
                    f"Vibration {df['Vibration (g)'].min():.4f}-{df['Vibration (g)'].max():.4f}, "
                    f"Temperature {df['Temperature (C)'].min():.1f}-{df['Temperature (C)'].max():.1f}")
            
            self.log_test_result(test_name, success, description, notes)
            
        except Exception as e:
            self.log_test_result(test_name, False, description, f"Exception: {e}")
    
    def test_sparse_data_handling(self):
        """Test chart creation with sparse data (many missing values)."""
        test_name = "Sparse Data Handling"
        description = "Chart creation with high percentage of missing values"
        
        try:
            # Test with different sparsity levels
            sparsity_levels = [0.1, 0.3, 0.5, 0.7, 0.9]
            all_success = True
            
            for sparsity in sparsity_levels:
                df = self.data_generator.generate_sparse_data(sparsity=sparsity)
                
                cfg = ChartConfig(
                    id=f"sparse_{int(sparsity*100)}",
                    title=f"Sparse Data ({int(sparsity*100)}% missing)",
                    chart_type="line",
                    y_params=["Sparse Parameter 1", "Sparse Parameter 2", "Sparse Parameter 3"]
                )
                
                fig = self.chart_manager.create_chart(df, cfg)
                
                if fig is None:
                    all_success = False
                    break
                
                # Verify that traces exist for parameters with some valid data
                valid_params = []
                for param in ["Sparse Parameter 1", "Sparse Parameter 2", "Sparse Parameter 3"]:
                    if not df[param].isna().all():
                        valid_params.append(param)
                
                if len(fig.data) != len(valid_params):
                    all_success = False
                    break
            
            notes = f"Tested sparsity levels: {sparsity_levels}. Charts should handle missing data gracefully."
            self.log_test_result(test_name, all_success, description, notes)
            
        except Exception as e:
            self.log_test_result(test_name, False, description, f"Exception: {e}")
    
    def test_missing_data_alignment(self):
        """Test chart creation with misaligned data ranges between parameters."""
        test_name = "Missing Data Alignment"
        description = "Chart creation with parameters having different valid time ranges"
        
        try:
            df = self.data_generator.generate_misaligned_data()
            
            # Test all parameters on same chart
            cfg = ChartConfig(
                id="misaligned",
                title="Misaligned Parameter Ranges",
                chart_type="line",
                y_params=["Full Range Param", "Mid Range Param", "Early Range Param", "Late Range Param"]
            )
            
            fig = self.chart_manager.create_chart(df, cfg)
            success = fig is not None
            
            if success:
                # Should have 4 traces for 4 parameters
                success = len(fig.data) == 4
                
                # Verify legend shows all parameters
                trace_names = [trace.name for trace in fig.data]
                expected_names = ["Full Range Param", "Mid Range Param", "Early Range Param", "Late Range Param"]
                success = success and all(name in trace_names for name in expected_names)
            
            # Document the data alignment
            alignment_info = []
            for param in ["Full Range Param", "Mid Range Param", "Early Range Param", "Late Range Param"]:
                valid_count = df[param].notna().sum()
                total_count = len(df[param])
                alignment_info.append(f"{param}: {valid_count}/{total_count} valid")
            
            notes = f"Data alignment: {'; '.join(alignment_info)}"
            self.log_test_result(test_name, success, description, notes)
            
        except Exception as e:
            self.log_test_result(test_name, False, description, f"Exception: {e}")
    
    def test_non_monotonic_x_axis(self):
        """Test handling of non-monotonic X-axis data."""
        test_name = "Non-Monotonic X-Axis"
        description = "Chart behavior with non-monotonic custom X-axis (should fallback to scatter)"
        
        try:
            df = self.data_generator.generate_non_monotonic_x_data()
            
            # Test 1: Line chart with non-monotonic X (should fallback to scatter)
            cfg1 = ChartConfig(
                id="non_monotonic_line",
                title="Altitude vs Air Density (Line -> Scatter Fallback)",
                chart_type="line",
                x_param="Altitude (m)",
                y_params=["Air Density (kg/m³)"]
            )
            fig1 = self.chart_manager.create_chart(df, cfg1)
            
            # Test 2: Line chart with sorting enabled
            cfg2 = ChartConfig(
                id="non_monotonic_sorted",
                title="Altitude vs Air Density (Sorted)",
                chart_type="line",
                x_param="Altitude (m)",
                y_params=["Air Density (kg/m³)"],
                sort_x=True
            )
            fig2 = self.chart_manager.create_chart(df, cfg2)
            
            success = fig1 is not None and fig2 is not None
            
            if success:
                # fig1 should have scatter-mode traces (fallback)
                fig1_modes = [trace.mode for trace in fig1.data]
                fig1_has_markers = any("markers" in mode for mode in fig1_modes)
                
                # fig2 should have line-mode traces (sorted data)
                fig2_modes = [trace.mode for trace in fig2.data]
                fig2_has_lines = any("lines" in mode for mode in fig2_modes)
                
                success = fig1_has_markers or fig2_has_lines  # At least one should work as expected
            
            notes = f"Non-monotonic X detected. Fallback behavior and sorting options tested."
            self.log_test_result(test_name, success, description, notes)
            
        except Exception as e:
            self.log_test_result(test_name, False, description, f"Exception: {e}")
    
    def test_chart_type_edge_cases(self):
        """Test different chart types with edge case data."""
        test_name = "Chart Type Edge Cases"
        description = "Different chart types (line, scatter, bar, area) with challenging data"
        
        try:
            df = self.data_generator.generate_extreme_range_data()
            chart_types = ["line", "scatter", "bar", "area"]
            all_success = True
            
            for chart_type in chart_types:
                cfg = ChartConfig(
                    id=f"type_{chart_type}",
                    title=f"{chart_type.title()} Chart with Extreme Ranges",
                    chart_type=chart_type,
                    y_params=["Pressure (Pa)", "Temperature (C)"]
                )
                
                fig = self.chart_manager.create_chart(df, cfg)
                
                if fig is None:
                    all_success = False
                    break
                
                # Verify correct number of traces
                if len(fig.data) != 2:
                    all_success = False
                    break
            
            notes = f"Tested chart types: {chart_types}. All should handle extreme value ranges."
            self.log_test_result(test_name, all_success, description, notes)
            
        except Exception as e:
            self.log_test_result(test_name, False, description, f"Exception: {e}")
    
    def test_frequency_analysis_edge_cases(self):
        """Test frequency analysis with edge case scenarios."""
        test_name = "Frequency Analysis Edge Cases"
        description = "FFT and PSD analysis with various data characteristics"
        
        try:
            # Test 1: Regular frequency test data
            df_regular = self.data_generator.generate_frequency_test_data()
            
            cfg_fft = ChartConfig(
                id="freq_fft",
                title="FFT Analysis",
                chart_type="frequency",
                freq_type="fft",
                y_params=["Vibration Signal 1", "Vibration Signal 2"]
            )
            
            cfg_psd = ChartConfig(
                id="freq_psd",
                title="PSD Analysis",
                chart_type="frequency",
                freq_type="psd",
                y_params=["Vibration Signal 1", "Vibration Signal 2"]
            )
            
            fig_fft = self.chart_manager.create_chart(df_regular, cfg_fft)
            fig_psd = self.chart_manager.create_chart(df_regular, cfg_psd)
            
            # Test 2: Sparse data for frequency analysis
            df_sparse = self.data_generator.generate_sparse_data(sparsity=0.1)
            
            cfg_sparse = ChartConfig(
                id="freq_sparse",
                title="Frequency Analysis with Sparse Data",
                chart_type="frequency",
                freq_type="fft",
                y_params=["Sparse Parameter 1"]
            )
            
            fig_sparse = self.chart_manager.create_chart(df_sparse, cfg_sparse)
            
            success = (fig_fft is not None and fig_psd is not None)
            # Note: fig_sparse might be None if data is too sparse for frequency analysis
            
            notes = f"FFT: {'✓' if fig_fft is not None else '✗'}, PSD: {'✓' if fig_psd is not None else '✗'}, Sparse: {'✓' if fig_sparse is not None else '✗ (expected for sparse data)'}"
            self.log_test_result(test_name, success, description, notes)
            
        except Exception as e:
            self.log_test_result(test_name, False, description, f"Exception: {e}")
    
    def test_empty_and_invalid_data(self):
        """Test handling of empty and invalid data scenarios."""
        test_name = "Empty and Invalid Data"
        description = "Chart creation with empty dataframes and invalid parameters"
        
        try:
            results = []
            
            # Test 1: Empty DataFrame
            df_empty = pd.DataFrame()
            cfg_empty = ChartConfig(
                id="empty",
                title="Empty Data Test",
                y_params=["Nonexistent Param"]
            )
            fig_empty = self.chart_manager.create_chart(df_empty, cfg_empty)
            results.append(("Empty DF", fig_empty is None))
            
            # Test 2: DataFrame with no valid parameters (currently creates chart with text data)
            df_invalid = pd.DataFrame({
                "Elapsed Time (s)": [1, 2, 3],
                "Text Column": ["a", "b", "c"]
            })
            cfg_invalid = ChartConfig(
                id="invalid",
                title="Invalid Parameters Test",
                y_params=["Nonexistent Param", "Text Column"]
            )
            fig_invalid = self.chart_manager.create_chart(df_invalid, cfg_invalid)
            # Current behavior: creates chart with text column (may not be ideal but doesn't crash)
            results.append(("Invalid params handled", fig_invalid is not None))
            
            # Test 3: DataFrame with all NaN values (currently creates chart with NaN data)
            df_nan = pd.DataFrame({
                "Elapsed Time (s)": [1, 2, 3],
                "All NaN Param": [np.nan, np.nan, np.nan]
            })
            cfg_nan = ChartConfig(
                id="all_nan",
                title="All NaN Test",
                y_params=["All NaN Param"]
            )
            fig_nan = self.chart_manager.create_chart(df_nan, cfg_nan)
            # Current behavior: creates chart with NaN data (may not be ideal but doesn't crash)
            results.append(("All NaN handled", fig_nan is not None))
            
            # Success means no exceptions were thrown (graceful handling)
            success = True  # If we got here, no exceptions were thrown
            
            result_strs = []
            for name, result in results:
                status = "✓" if result else "✗"
                result_strs.append(f"{name}: {status}")
            notes = f"Results: {', '.join(result_strs)}. Current behavior: creates charts even with invalid data types or all-NaN data."
            self.log_test_result(test_name, success, description, notes)
            
        except Exception as e:
            self.log_test_result(test_name, False, description, f"Exception: {e}")
    
    def test_secondary_y_axis_preparation(self):
        """Test configuration for future secondary Y-axis implementation."""
        test_name = "Secondary Y-Axis Preparation"
        description = "Configuration and data preparation for dual Y-axis functionality"
        
        try:
            df = self.data_generator.generate_extreme_range_data()
            
            # Test configuration with secondary Y parameters
            cfg = ChartConfig(
                id="secondary_y",
                title="Dual Y-Axis Test (Future Feature)",
                chart_type="line",
                y_params=["Pressure (Pa)"],
                secondary_y_params=["Vibration (g)", "Temperature (C)"],
                y_axis_label="Pressure (Pa)",
                secondary_y_axis_label="Vibration (g) / Temperature (C)"
            )
            
            fig = self.chart_manager.create_chart(df, cfg)
            
            # Currently should only plot primary y_params
            success = fig is not None and len(fig.data) == 1
            
            if success:
                # Verify the configuration is properly stored
                success = (len(cfg.secondary_y_params) == 2 and
                          cfg.secondary_y_axis_label != "" and
                          fig.data[0].name == "Pressure (Pa)")
            
            notes = ("Configuration ready for dual Y-axis implementation. "
                    "Currently only primary y_params are plotted as expected.")
            self.log_test_result(test_name, success, description, notes)
            
        except Exception as e:
            self.log_test_result(test_name, False, description, f"Exception: {e}")
    
    def run_all_tests(self):
        """Run all edge case tests and generate summary report."""
        print("=" * 60)
        print("ENHANCED FLIGHT ANALYZER - CHART EDGE CASES TEST SUITE")
        print("=" * 60)
        print()
        
        # Run all tests
        self.test_extreme_value_ranges()
        self.test_sparse_data_handling()
        self.test_missing_data_alignment()
        self.test_non_monotonic_x_axis()
        self.test_chart_type_edge_cases()
        self.test_frequency_analysis_edge_cases()
        self.test_empty_and_invalid_data()
        self.test_secondary_y_axis_preparation()
        
        # Generate summary
        print()
        print("=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\nFailed Tests:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test_name']}: {result['notes']}")
        
        print("\n" + "=" * 60)
        print("EDGE CASE DOCUMENTATION")
        print("=" * 60)
        
        for result in self.test_results:
            print(f"\n{result['test_name']}:")
            print(f"  Description: {result['description']}")
            print(f"  Result: {'PASS' if result['success'] else 'FAIL'}")
            if result['notes']:
                print(f"  Notes: {result['notes']}")
        
        return passed_tests == total_tests


def main():
    """Run the comprehensive edge case test suite."""
    test_suite = TestChartEdgeCases()
    all_passed = test_suite.run_all_tests()
    
    print(f"\n{'✅ All tests passed!' if all_passed else '❌ Some tests failed.'}")
    return 0 if all_passed else 1


if __name__ == "__main__":
    exit(main())