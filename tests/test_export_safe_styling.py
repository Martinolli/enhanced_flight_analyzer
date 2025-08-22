import sys
import os
import tempfile
import zipfile

# Add project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
from components.export_manager import ExportManager
from components.config_models import ChartConfig

def test_export_safe_styling():
    """Test export-safe styling functionality."""
    # Create test data
    df = pd.DataFrame({
        "Elapsed Time (s)": [0, 1, 2, 3, 4, 5],
        "Altitude (ft)": [1000, 1100, 1200, 1250, 1300, 1350],
        "Speed (knots)": [120, 125, 130, 135, 140, 145]
    })
    
    # Create test charts
    charts = {
        "altitude_chart": {
            "id": "alt1",
            "title": "Altitude vs Time",
            "chart_type": "line",
            "x_param": "Elapsed Time (s)",
            "y_params": ["Altitude (ft)"],
            "color_scheme": "viridis"
        },
        "speed_chart": {
            "id": "spd1", 
            "title": "Speed vs Time",
            "chart_type": "line",
            "x_param": "Elapsed Time (s)",
            "y_params": ["Speed (knots)"],
            "color_scheme": "blues"
        }
    }
    
    em = ExportManager()
    
    # Test PNG export with high-DPI
    png_zip = em.export_charts_as_images_zip(
        charts, df, fmt="png", scale=3.0, export_safe_styling=True
    )
    assert len(png_zip) > 0, "PNG export should produce non-empty zip"
    
    # Test SVG export (vector)
    svg_zip = em.export_charts_as_images_zip(
        charts, df, fmt="svg", export_safe_styling=True
    )
    assert len(svg_zip) > 0, "SVG export should produce non-empty zip"
    
    # Test PDF export (vector)
    pdf_zip = em.export_charts_as_images_zip(
        charts, df, fmt="pdf", export_safe_styling=True
    )
    assert len(pdf_zip) > 0, "PDF export should produce non-empty zip"
    
    # Verify ZIP contents
    with tempfile.TemporaryDirectory() as temp_dir:
        for fmt, zip_data in [("png", png_zip), ("svg", svg_zip), ("pdf", pdf_zip)]:
            zip_path = os.path.join(temp_dir, f"test_{fmt}.zip")
            with open(zip_path, "wb") as f:
                f.write(zip_data)
            
            with zipfile.ZipFile(zip_path, "r") as zf:
                files = zf.namelist()
                # Should have 2 chart files
                chart_files = [f for f in files if f.endswith(f".{fmt}")]
                assert len(chart_files) == 2, f"Should have 2 {fmt} files, got {len(chart_files)}"
                
                # Verify no error files
                error_files = [f for f in files if f.startswith("ERROR_")]
                assert len(error_files) == 0, f"Should have no error files, got {error_files}"
    
    print("✅ test_export_safe_styling passed!")

def test_html_export_improvements():
    """Test improved HTML export with export-safe styling."""
    df = pd.DataFrame({
        "Elapsed Time (s)": [0, 1, 2, 3, 4],
        "Temperature (°C)": [20, 22, 24, 26, 28]
    })
    
    charts = {
        "temp_chart": {
            "id": "temp1",
            "title": "Temperature Over Time",
            "chart_type": "line",
            "x_param": "Elapsed Time (s)",
            "y_params": ["Temperature (°C)"],
            "color_scheme": "reds"
        }
    }
    
    em = ExportManager()
    html_content = em.export_dashboard_html(charts, df)
    
    # Verify improved HTML structure
    assert "<!DOCTYPE html>" in html_content
    assert "viewport" in html_content  # Mobile-friendly
    assert "grid-template-columns" in html_content  # CSS Grid
    assert "@media print" in html_content  # Print styles
    assert "page-break-inside: avoid" in html_content  # PDF optimization
    assert "Arial" in html_content  # Export-safe font
    
    print("✅ test_html_export_improvements passed!")

def test_chart_styling_defaults():
    """Test that charts have export-friendly default styling."""
    df = pd.DataFrame({
        "Time": [0, 1, 2],
        "Value": [10, 20, 15]
    })
    
    em = ExportManager()
    cfg = ChartConfig(
        id="test1",
        title="Test Chart",
        chart_type="line",
        x_param="Time",
        y_params=["Value"]
    )
    
    fig = em.chart_manager.create_chart(df, cfg)
    assert fig is not None
    
    # Verify export-friendly defaults
    layout = fig.layout
    assert layout.font.family == "Arial, sans-serif"
    assert layout.font.color == "black"
    assert layout.plot_bgcolor == "white"
    assert layout.paper_bgcolor == "white"
    
    print("✅ test_chart_styling_defaults passed!")

if __name__ == "__main__":
    test_export_safe_styling()
    test_html_export_improvements()
    test_chart_styling_defaults()
    print("All export styling tests passed! 🎉")