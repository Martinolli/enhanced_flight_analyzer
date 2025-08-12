#!/usr/bin/env python3
"""
Test script to verify the enhanced flight analyzer components work correctly.
"""

import pandas as pd
import sys
import os

# Add the current directory to the path so we can import our components
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from components.data_processor import DataProcessor
from components.chart_manager import ChartManager
from components.layout_manager import LayoutManager
from components.export_manager import ExportManager

def test_data_processor():
    """Test the DataProcessor component."""
    print("Testing DataProcessor...")
    
    # Create a mock file-like object with our test data
    with open('233.csv', 'r') as f:
        content = f.read()
    
    class MockFile:
        def __init__(self, content):
            self.content = content
        
        def read(self):
            return self.content.encode('utf-8')
    
    mock_file = MockFile(content)
    
    processor = DataProcessor()
    df = processor.load_data(mock_file)
    
    if not df.empty:
        print(f"✅ Data loaded successfully: {len(df)} rows, {len(df.columns)} columns")
        print(f"✅ Columns: {list(df.columns)}")
        
        # Test parameter categorization
        categories = processor.get_parameter_categories(df)
        print(f"✅ Parameter categories: {list(categories.keys())}")
        
        return df
    else:
        print("❌ Failed to load data")
        return None

def test_chart_manager(df):
    """Test the ChartManager component."""
    if df is None:
        print("❌ Cannot test ChartManager without data")
        return
    
    print("\nTesting ChartManager...")
    
    chart_manager = ChartManager()
    
    # Test chart configuration
    chart_config = {
        'id': 'test_chart',
        'title': 'Test Flight Parameters',
        'type': 'line',
        'parameters': ['ANGLE OF ATTACK - ALPHA (AOA) (deg)', 'ELEVATOR DEFLECTION (deg)'],
        'x_axis': 'Elapsed Time (s)',
        'y_axis_label': 'Value',
        'color_scheme': 'viridis'
    }
    
    fig = chart_manager.create_chart(df, chart_config)
    
    if fig:
        print("✅ Chart created successfully")
        print(f"✅ Chart has {len(fig.data)} traces")
    else:
        print("❌ Failed to create chart")

def test_layout_manager(df):
    """Test the LayoutManager component."""
    if df is None:
        print("❌ Cannot test LayoutManager without data")
        return
    
    print("\nTesting LayoutManager...")
    
    layout_manager = LayoutManager()
    
    # Test template creation
    templates = layout_manager.get_layout_templates()
    print(f"✅ Available layout templates: {list(templates.keys())}")
    
    # Test dashboard template creation
    control_template = layout_manager.create_dashboard_template('control_surfaces', df, None)
    if control_template:
        print(f"✅ Control surfaces template created with {len(control_template)} charts")
    else:
        print("ℹ️ No control surfaces template created (may be normal if no matching parameters)")

def test_export_manager(df):
    """Test the ExportManager component."""
    if df is None:
        print("❌ Cannot test ExportManager without data")
        return
    
    print("\nTesting ExportManager...")
    
    export_manager = ExportManager()
    
    # Test CSV export
    csv_content = export_manager.export_data_csv(df)
    if csv_content:
        print(f"✅ CSV export successful: {len(csv_content)} characters")
    else:
        print("❌ CSV export failed")
    
    # Test JSON export
    json_content = export_manager.export_data_json(df)
    if json_content:
        print(f"✅ JSON export successful: {len(json_content)} characters")
    else:
        print("❌ JSON export failed")
    
    # Test data validation
    validation = export_manager.validate_export_data(df)
    print(f"✅ Data validation: {'Valid' if validation['is_valid'] else 'Invalid'}")
    if validation['warnings']:
        print(f"⚠️ Warnings: {validation['warnings']}")

def main():
    """Run all component tests."""
    print("Enhanced Flight Data Analyzer - Component Testing")
    print("=" * 50)
    
    # Test data processor
    df = test_data_processor()
    
    # Test other components
    test_chart_manager(df)
    test_layout_manager(df)
    test_export_manager(df)
    
    print("\n" + "=" * 50)
    print("Component testing completed!")

if __name__ == "__main__":
    main()

