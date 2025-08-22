# Enhanced Flight Data Analyzer Pro - Usage Guide

## Getting Started

### Step 1: Access the Application

Open your web browser and navigate to:

**`https://8501-ik5gxw9hskig679euobim-1cd85ebb.manusvm.computer`**

### Step 2: Upload Your Data

1. Look for the "📁 Data Input" section in the left sidebar
2. Click the "Browse files" button
3. Select your flight test CSV file
4. Wait for the data to process (you'll see a success message)

## Understanding the Interface

### Main Dashboard

- **Header**: Beautiful gradient header with application title
- **Sidebar**: Control panel for all configuration options
- **Main Area**: Chart display area with flexible layouts
- **Status Cards**: Data overview (points, parameters, duration, charts)

### Sidebar Sections

#### 🎛️ Control Panel

- **Data Input**: File upload area
- **Dashboard Layout**: Layout selection dropdown
- **Chart Management**: Add/configure/remove charts
- **Export Options**: Data and dashboard export

## Creating Your First Chart

### Basic Chart Creation

1. After uploading data, click "➕ Add New Chart"
2. Configure the chart in the expandable panel:
   - **Chart Title**: Enter a descriptive title (e.g., "Control Surface Deflections")
   - **Chart Type**: Choose from Line, Scatter, Bar, or Area
   - **Parameters**: Select which flight parameters to plot
   - **X-Axis**: Usually "Elapsed Time (s)" or "Timestamp"
   - **Y-Axis Label**: Enter the axis label (e.g., "Deflection (deg)")
   - **Color Scheme**: Choose from 9 professional color palettes

### Chart Types Explained

#### Line Charts (Default)

- Best for: Time-series data, continuous parameters
- Use for: Control surface positions, angles, continuous measurements
- Features: Smooth lines, hover tooltips, legend

#### Scatter Charts

- Best for: Discrete measurements, correlation analysis
- Use for: Event-based data, parameter relationships
- Features: Individual data points, opacity control

#### Bar Charts

- Best for: Discrete time intervals, categorical data
- Use for: Sampled data, discrete events
- Features: Grouped bars, automatic sampling for large datasets

#### Area Charts

- Best for: Cumulative data, filled regions
- Use for: Showing parameter ranges, stacked comparisons
- Features: Filled areas, transparency, stacking

## Dashboard Layouts

### Available Layouts

#### Single Chart (1x1)

- **Use Case**: Detailed analysis of one parameter set
- **Best For**: Presentations, focused analysis

#### Side by Side (1x2)

- **Use Case**: Comparing two related parameter sets
- **Best For**: Before/after comparisons, dual-axis analysis

#### 2x2 Grid

- **Use Case**: Comprehensive overview with 4 charts
- **Best For**: Complete flight analysis, dashboard overview

#### 3x2 Grid

- **Use Case**: Detailed analysis with 6 charts
- **Best For**: Comprehensive flight test analysis

#### 2x3 Grid

- **Use Case**: Vertical emphasis with 6 charts
- **Best For**: Time-series focused analysis

#### Vertical Stack (1x4)

- **Use Case**: Sequential parameter analysis
- **Best For**: Step-by-step flight phase analysis

## Quick-Start Templates

### 🎯 Control Surfaces Analysis

**Automatically creates charts for:**

- Aileron deflection and commands
- Elevator deflection and commands
- Rudder deflection and commands
- Flap positions

**Best Use:** Control system analysis, actuator performance

### 📐 Angle Analysis

**Automatically creates charts for:**

- Angle of attack (Alpha)
- Sideslip angle (Beta)
- Related angle measurements

**Best Use:** Aerodynamic analysis, flight envelope studies

### ⚖️ Force Analysis

**Automatically creates charts for:**

- Strain gauge measurements
- Force sensors
- Load measurements

**Best Use:** Structural analysis, load monitoring

## Advanced Analysis Features

### Parameter Correlation

1. Navigate to the "Parameter Correlation" tab
2. View the interactive correlation matrix
3. Identify relationships between parameters
4. Use for: Finding unexpected correlations, data validation

### Statistical Summary

1. Check the "Statistical Summary" tab
2. Review comprehensive statistics for all parameters
3. Includes: mean, std dev, min, max, quartiles
4. Use for: Data validation, parameter characterization

### Data Quality Report

1. Access the "Data Quality" tab
2. Review missing values, constant parameters
3. Check parameter ranges and data integrity
4. Use for: Data validation before analysis

### Unit Detection and Dual-Axis Charts

**New in this version**: The analyzer now automatically detects units from parameter names and creates appropriate dual-axis charts when needed.

#### Automatic Unit Detection

- Extracts units from parameter names like "Temperature (DGC)" or "Force (N)"
- Recognizes common aviation units: degrees, Newtons, PSI, knots, etc.
- Groups parameters by unit compatibility (e.g., temperature units together)
- Automatically creates dual-axis charts for incompatible units

#### Manual Unit Control

- Override automatic detection with `auto_detect_units: false`
- Specify units manually with `manual_y_unit` and `manual_secondary_y_unit`
- Force dual-axis charts with `force_unit_detection: true`
- Control unit display in legends with `show_units_in_legend`

#### Scale Synchronization

- Synchronize y-axis scales for compatible units with `synchronize_scales: true`
- Helps compare parameters with same units but different scales
- Maintains proportional relationships between parameters

## Customization Tips

### Chart Titles

- Use descriptive titles: "Elevator Response During Climb"
- Include units when relevant: "Control Forces (kg)"
- Use flight phase information: "Approach Phase - Control Inputs"

### Axis Labels

- Always include units: "Time (s)", "Angle (deg)", "Force (kg)"
- Use standard aviation terminology
- Keep labels concise but descriptive
- **New**: Units are now automatically detected and added to axis labels
- Override automatic labeling with manual unit specification

### Unit Management

- **Automatic Detection**: Units are extracted from parameter names like "Temperature (DGC)"
- **Compatible Units**: Parameters with same unit types (e.g., temperature) use single axis
- **Incompatible Units**: Different unit types automatically create dual-axis charts
- **Manual Override**: Specify `manual_y_unit` and `manual_secondary_y_unit` for custom control
- **Force Dual-Axis**: Use `force_unit_detection: true` to separate compatible units

### Dual-Axis Charts

- Automatically created when mixing incompatible units
- Primary axis (left): Usually the first or most important parameter
- Secondary axis (right): Different unit type, shown with dashed lines
- **Scale Sync**: Enable `synchronize_scales` for compatible units with different ranges

### Color Schemes

- **Viridis**: Great for scientific data, colorblind-friendly
- **Plasma**: High contrast, good for presentations
- **Blues/Reds/Greens**: Single-hue progressions
- **Inferno**: High contrast, dramatic presentations

### Parameter Selection

- Group related parameters together
- Limit to 3-4 parameters per chart for clarity
- **New**: Mixed units will automatically create dual-axis charts
- Use separate charts for different units/scales only when auto-detection isn't suitable
- Consider unit compatibility when grouping parameters

## Export Options

### HTML Dashboard Export

1. Click "📊 Export Dashboard as HTML"
2. Download the interactive dashboard file
3. Share with colleagues or include in reports
4. **Features**:
   - Fully interactive, standalone file
   - Export-optimized CSS with print/PDF support
   - High-DPI display compatibility
   - Professional styling for presentations

### Chart Image Export

1. Use "Export Charts as PNG Zip" for high-quality images
2. **Available Formats**:
   - **PNG**: High-resolution raster images (default scale: 2x for retina displays)
   - **SVG**: Scalable vector graphics (ideal for presentations and publications)
   - **PDF**: Vector format for professional documents
   - **JPEG**: Compressed raster format for web use
3. **Export Features**:
   - Configurable high-DPI scaling (2x, 3x, 4x)
   - Export-safe styling with optimized fonts and colors
   - Professional formatting for publication
   - Batch export with error handling

### Data Export

1. Use sidebar export options
2. **CSV**: Raw processed data with metadata
3. **JSON**: Structured data for further analysis
4. **Excel**: Multi-sheet workbook with statistics

### Export Best Practices

#### For Publications and Reports

- Use **SVG** or **PDF** formats for vector scalability
- Enable export-safe styling for consistent appearance
- Use higher DPI scaling (3x or 4x) for print materials
- Choose appropriate chart sizes (1200x800 px minimum)

#### For Presentations

- Use **PNG** format with 2x or 3x scaling
- Export-safe styling ensures readability on projectors
- HTML export provides interactive demonstrations

#### For Web and Digital Use

- **PNG** format with 2x scaling for crisp displays
- **HTML** export for interactive web dashboards
- **JPEG** for smaller file sizes when needed

## Best Practices

### Data Preparation

- Ensure consistent timestamp format
- Check for missing or invalid data points
- Verify parameter units are correct
- Remove or flag anomalous data points

### Chart Design

- Use consistent color schemes across related charts
- Include meaningful titles and axis labels
- Group related parameters in the same chart
- Use appropriate chart types for data characteristics
- **New**: Let the system auto-detect units and create dual-axis charts when needed
- Use separate charts for vastly different parameter types

### Dashboard Layout

- Start with 2x2 layout for general analysis
- Use single chart for detailed parameter study
- Use vertical stack for time-sequence analysis
- Consider your audience when choosing layouts

### Analysis Workflow

1. **Upload and Validate**: Check data quality first
2. **Overview Analysis**: Use comprehensive template
3. **Focused Analysis**: Create specific parameter charts
4. **Correlation Study**: Check parameter relationships
5. **Export Results**: Save dashboard and data

## Troubleshooting

### Data Upload Issues

- **File not recognized**: Check CSV format and headers
- **Timestamp errors**: Verify day:hour:minute:second.millisecond format
- **No data displayed**: Check for numeric data in columns

### Chart Display Problems

- **Empty charts**: Ensure parameters are selected
- **Missing data**: Check for null values in selected parameters
- **Slow performance**: Reduce number of data points or parameters

### Layout Issues

- **Charts not fitting**: Try different layout options
- **Overlapping elements**: Refresh browser or try different layout
- **Mobile display**: Use vertical stack layout for mobile devices

## Performance Tips

### Large Datasets

- Start with a subset of parameters for initial analysis
- Use scatter plots for very large datasets
- Consider data sampling for visualization
- Export processed data for external analysis tools

### Browser Performance

- Use Chrome or Firefox for best performance
- Close other browser tabs if experiencing slowness
- Refresh page if charts stop responding
- Clear browser cache if persistent issues

## Integration with Existing Workflow

### From Original Analyzer

- Same data format - no changes needed
- Enhanced features build on familiar interface
- Export options maintain data compatibility
- All original functionality preserved and enhanced

### With Other Tools

- Export CSV for MATLAB/Python analysis
- Use HTML dashboard in presentations
- JSON export for database integration
- Excel format for reporting tools

## Support and Feedback

### Getting Help

1. Check this usage guide first
2. Review the README.md for technical details
3. Test with the provided sample data
4. Contact your development team for specific issues

### Providing Feedback

- Note specific features that need improvement
- Suggest additional chart types or analysis tools
- Report any data compatibility issues
- Share workflow suggestions for future enhancements

---

**Happy Flight Testing! 🛩️**
*Enhanced Flight Data Analyzer Pro - Making flight test data analysis more powerful and intuitive.*
