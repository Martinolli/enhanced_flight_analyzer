# Enhanced Flight Analyzer - Test Suite

This directory contains comprehensive tests for the Enhanced Flight Analyzer, with a focus on chart generation edge cases and dual/multi-axis functionality.

## Test Files

### `test_chart_manager.py`
Original test file with basic chart manager functionality tests.

### `test_chart_edge_cases.py`
Comprehensive test suite for dual/multi-axis chart edge cases including:
- Extreme value ranges
- Sparse data handling  
- Missing data alignment
- Non-monotonic X-axis behavior
- Chart type edge cases
- Frequency analysis edge cases
- Empty and invalid data handling
- Secondary Y-axis preparation

### `run_all_tests.py`
Test runner that executes all test suites and provides comprehensive reporting.

### `CHART_EDGE_CASES_DOCUMENTATION.md`
Detailed documentation of all test cases, expected results, and regression testing guidelines.

## Running Tests

### Run All Tests
```bash
python tests/run_all_tests.py
```

### Run Individual Test Suites
```bash
# Original tests
python tests/test_chart_manager.py

# Edge case tests
python tests/test_chart_edge_cases.py
```

## Test Coverage

The test suite covers:
- ✅ Chart creation with extreme value ranges
- ✅ Sparse and missing data scenarios
- ✅ Non-monotonic X-axis handling
- ✅ All chart types (line, scatter, bar, area, frequency)
- ✅ Empty and invalid data edge cases
- ✅ Configuration for future dual-axis implementation
- ✅ Synthetic data generation for reproducible testing

## Future Development

These tests are designed to support:
- Dual Y-axis implementation
- Multi-axis chart functionality
- Enhanced data validation
- Performance optimization
- Regression testing

For detailed information about test cases and expected results, see `CHART_EDGE_CASES_DOCUMENTATION.md`.