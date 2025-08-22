#!/usr/bin/env python3
"""
Test runner for the Enhanced Flight Analyzer test suite.

Runs all available tests and provides a comprehensive report.
"""

import sys
import os

# Add project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def run_original_tests():
    """Run the original chart manager tests."""
    print("Running Original Chart Manager Tests...")
    print("=" * 50)
    
    try:
        # Import and run the original test
        from tests.test_chart_manager import test_custom_x_axis_scatter_fallback
        test_custom_x_axis_scatter_fallback()
        print("✅ Original tests completed successfully\n")
        return True
    except Exception as e:
        print(f"❌ Original tests failed: {e}\n")
        return False


def run_edge_case_tests():
    """Run the comprehensive edge case tests."""
    print("Running Comprehensive Edge Case Tests...")
    print("=" * 50)
    
    try:
        from tests.test_chart_edge_cases import TestChartEdgeCases
        test_suite = TestChartEdgeCases()
        success = test_suite.run_all_tests()
        print(f"\n{'✅ Edge case tests completed successfully' if success else '❌ Some edge case tests failed'}\n")
        return success
    except Exception as e:
        print(f"❌ Edge case tests failed: {e}\n")
        return False


def main():
    """Run all tests and provide summary."""
    print("ENHANCED FLIGHT ANALYZER - COMPLETE TEST SUITE")
    print("=" * 60)
    print()
    
    # Run all test suites
    original_success = run_original_tests()
    edge_case_success = run_edge_case_tests()
    
    # Final summary
    print("=" * 60)
    print("FINAL TEST SUMMARY")
    print("=" * 60)
    
    total_suites = 2
    passed_suites = sum([original_success, edge_case_success])
    
    print(f"Test Suites Run: {total_suites}")
    print(f"Suites Passed: {passed_suites}")
    print(f"Suites Failed: {total_suites - passed_suites}")
    
    if passed_suites == total_suites:
        print("\n🎉 ALL TEST SUITES PASSED! 🎉")
        print("The chart generation system is ready for production use.")
        print("Edge cases are well covered and documented.")
        return 0
    else:
        print(f"\n⚠️  {total_suites - passed_suites} TEST SUITE(S) FAILED")
        print("Please review the failing tests before proceeding.")
        return 1


if __name__ == "__main__":
    exit(main())