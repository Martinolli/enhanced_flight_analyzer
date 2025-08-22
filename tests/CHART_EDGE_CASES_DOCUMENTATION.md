# Dual/Multi-Axis Chart Edge Cases Test Documentation

This document provides comprehensive documentation of test cases and expected results for the Enhanced Flight Analyzer's chart generation system, with a focus on dual/multi-axis chart edge cases and challenging data scenarios.

## Test Suite Overview

The test suite (`tests/test_chart_edge_cases.py`) covers critical edge cases that could occur in flight data analysis, particularly scenarios that will be important when dual-axis functionality is implemented.

### Test Categories

1. **Extreme Value Ranges** - Parameters with vastly different scales
2. **Sparse Data Handling** - High percentage of missing values
3. **Missing Data Alignment** - Parameters with different valid time ranges
4. **Non-Monotonic X-Axis** - Custom X-axis with non-monotonic data
5. **Chart Type Edge Cases** - Different chart types with challenging data
6. **Frequency Analysis Edge Cases** - FFT/PSD with various data characteristics
7. **Empty and Invalid Data** - Edge cases with empty or invalid datasets
8. **Secondary Y-Axis Preparation** - Configuration for future dual-axis implementation

## Detailed Test Cases

### 1. Extreme Value Ranges

**Purpose**: Test chart creation with parameters spanning multiple orders of magnitude.

**Test Data**: 
- Pressure: 50,000-120,000 Pa (large scale)
- Vibration: 0.001-0.1 g (small scale)  
- Temperature: -50 to 150°C (medium scale)

**Test Scenarios**:
- Single axis with all three parameters
- Configuration for future dual-axis (large vs small scale)

**Expected Results**:
- Charts should be created successfully
- All parameters should be plotted on single axis (current behavior)
- No exceptions or errors
- Configuration should be ready for dual-axis implementation

**Current Behavior**: ✅ PASS
- Successfully creates charts with extreme value ranges
- Single axis plotting works correctly
- Dual-axis configuration stored for future implementation

### 2. Sparse Data Handling

**Purpose**: Test chart creation with high percentage of missing values.

**Test Data**: Synthetic parameters with 10%, 30%, 50%, 70%, and 90% missing values

**Test Scenarios**:
- Line charts with various sparsity levels
- Irregular time intervals
- Different missing value patterns per parameter

**Expected Results**:
- Charts should be created for all sparsity levels
- Missing values should be handled gracefully (gaps in lines)
- Performance should remain acceptable
- No crashes or exceptions

**Current Behavior**: ✅ PASS
- All sparsity levels handled correctly
- Plotly automatically handles NaN values by creating gaps
- Performance remains good even with 90% missing data

### 3. Missing Data Alignment

**Purpose**: Test parameters with different valid time ranges (common in real flight data).

**Test Data**:
- Full Range Param: Valid 0-100s (100/100 points)
- Mid Range Param: Valid 30-70s (40/100 points)
- Early Range Param: Valid 0-40s (40/100 points)
- Late Range Param: Valid 60-100s (40/100 points)

**Test Scenarios**:
- All parameters on same chart
- Different overlap patterns
- Realistic sensor start/stop scenarios

**Expected Results**:
- All parameters should be plotted
- Each parameter should only show data in its valid range
- No artifacts from misaligned data
- Legends should show all parameters

**Current Behavior**: ✅ PASS
- All parameters plotted correctly
- Missing data handled with gaps
- No interference between parameters with different ranges

### 4. Non-Monotonic X-Axis

**Purpose**: Test custom X-axis parameter that is not monotonically increasing.

**Test Data**: Altitude vs time (goes up and down), with dependent parameters like air density

**Test Scenarios**:
- Line chart with non-monotonic X (should fallback to scatter)
- Line chart with sorting enabled
- Dependent parameters that correlate with X

**Expected Results**:
- Non-monotonic line chart should fallback to scatter plot
- Sorted line chart should work correctly
- No misleading zig-zag lines
- Proper fallback behavior documented

**Current Behavior**: ✅ PASS
- Fallback to scatter plot works correctly
- Sorting option preserves line plot capability
- No visual artifacts from non-monotonic data

### 5. Chart Type Edge Cases

**Purpose**: Test different chart types with challenging data.

**Test Data**: Extreme value ranges across different chart types

**Test Scenarios**:
- Line, scatter, bar, and area charts
- Same data across all chart types
- Extreme value ranges in each type

**Expected Results**:
- All chart types should handle extreme ranges
- Each type should render appropriately
- No type-specific failures
- Consistent behavior across types

**Current Behavior**: ✅ PASS
- All chart types work with extreme data ranges
- Each type renders correctly
- No type-specific issues observed

### 6. Frequency Analysis Edge Cases

**Purpose**: Test FFT and PSD analysis with various data characteristics.

**Test Data**:
- Regular signals with known frequency components (5Hz, 10Hz, 25Hz)
- Sparse data for frequency analysis
- Different signal patterns

**Test Scenarios**:
- FFT analysis on regular data
- PSD analysis on regular data
- Frequency analysis on sparse data

**Expected Results**:
- FFT should work on regular, sampled data
- PSD should work on regular, sampled data
- Sparse data may fail frequency analysis (acceptable)
- No crashes on any data type

**Current Behavior**: ✅ PASS
- FFT and PSD work correctly on regular data
- Sparse data is handled appropriately
- Expected frequency peaks are visible

### 7. Empty and Invalid Data

**Purpose**: Test graceful handling of empty or invalid datasets.

**Test Data**:
- Empty DataFrame
- DataFrame with text columns only
- DataFrame with all-NaN parameters

**Test Scenarios**:
- Chart creation with empty data
- Chart creation with invalid parameter types
- Chart creation with all-NaN data

**Expected Results**:
- Empty data should return None gracefully
- Invalid parameters should be handled without crashes
- All-NaN data should be handled appropriately
- No exceptions should be thrown

**Current Behavior**: ✅ PASS
- Empty DataFrame returns None as expected
- Text columns are plotted (current behavior, may need future improvement)
- All-NaN data creates chart (current behavior, may need future improvement)
- No exceptions thrown in any case

### 8. Secondary Y-Axis Preparation

**Purpose**: Test configuration for future dual Y-axis implementation.

**Test Data**: Parameters with different scales suitable for dual-axis plotting

**Test Scenarios**:
- Configuration with primary and secondary Y parameters
- Different axis labels for each axis
- Preparation for dual-axis rendering

**Expected Results**:
- Configuration should be stored correctly
- Currently only primary Y parameters should be plotted
- Structure should be ready for dual-axis implementation
- No errors in configuration handling

**Current Behavior**: ✅ PASS
- Secondary Y configuration stored correctly
- Only primary Y parameters plotted (expected current behavior)
- Ready for future dual-axis implementation

## Synthetic Data Generation

The test suite includes a `SyntheticDataGenerator` class that creates realistic flight data scenarios:

### Data Generation Methods

1. **`generate_extreme_range_data()`**
   - Creates pressure (Pa), vibration (g), and temperature (°C) data
   - Simulates realistic sensor ranges with different scales

2. **`generate_sparse_data()`**
   - Creates data with configurable sparsity levels
   - Includes irregular time intervals
   - Simulates real-world data gaps

3. **`generate_misaligned_data()`**
   - Simulates sensors starting/stopping at different times
   - Creates realistic data alignment challenges
   - Tests parameter overlap scenarios

4. **`generate_non_monotonic_x_data()`**
   - Creates altitude profiles that go up and down
   - Includes parameters that depend on altitude
   - Tests X-axis sorting and fallback behavior

5. **`generate_frequency_test_data()`**
   - Creates signals with known frequency components
   - Includes noise and multiple frequency peaks
   - Tests FFT/PSD analysis capabilities

## Test Execution

### Running the Tests

```bash
cd /path/to/enhanced_flight_analyzer
python tests/test_chart_edge_cases.py
```

### Expected Output

The test suite provides:
- Real-time progress indicators (✅/❌)
- Detailed test descriptions and notes
- Summary statistics
- Comprehensive edge case documentation
- Success/failure analysis

### Success Criteria

- All tests should pass (100% success rate)
- No unhandled exceptions
- Graceful handling of all edge cases
- Proper documentation of current behavior
- Preparation for future dual-axis implementation

## Regression Testing Guidelines

### When to Run These Tests

1. **Before any chart generation changes**
2. **After modifying ChartManager or ChartConfig**
3. **When implementing dual-axis functionality**
4. **Before major releases**
5. **When adding new chart types**

### Adding New Test Cases

When adding new edge cases:

1. Add to the `SyntheticDataGenerator` class
2. Create a new test method in `TestChartEdgeCases`
3. Document expected behavior
4. Include realistic flight data scenarios
5. Update this documentation

### Expected Future Changes

When dual-axis functionality is implemented:

1. **Secondary Y-axis tests** will need updates
2. **Extreme value range tests** should show dual-axis behavior
3. **New edge cases** around axis alignment may emerge
4. **Performance tests** may be needed for dual-axis rendering

## Known Limitations and Future Improvements

### Current Behavior to Consider

1. **Text columns are plotted** - May need validation in future
2. **All-NaN data creates charts** - May need filtering in future
3. **Secondary Y-axis not implemented** - Configuration ready for implementation
4. **No data type validation** - May need enhancement for robustness

### Recommended Enhancements

1. **Data type validation** before chart creation
2. **Automatic dual-axis suggestion** for extreme value ranges
3. **Enhanced sparse data handling** with interpolation options
4. **Performance optimization** for large datasets
5. **Smart axis scaling** for mixed data types

## Conclusion

This test suite provides comprehensive coverage of edge cases that are critical for robust chart generation, particularly in preparation for dual/multi-axis functionality. The synthetic data generation ensures reproducible testing of challenging scenarios that occur in real flight data analysis.

The documentation serves as both a testing guide and a specification for expected behavior, enabling confident development of new features while maintaining compatibility with existing functionality.