# ✈️ Enhanced Flight Data Analyzer Pro

Version: v2.4.0-dev (Statistical Analysis Suite + Enhanced Data Processing)

A sophisticated web-based application for analyzing flight test instrumentation data with advanced statistical capabilities, dual Y-axis plotting, and comprehensive frequency domain analysis.

## 🚀 What's New in v2.4.0-dev

### 📊 **Statistical Analysis Suite**

- **Comprehensive Statistics**: Mean, standard deviation, skewness, kurtosis, quartiles, and coefficient of variation
- **Advanced Outlier Detection**: IQR, Z-score, and Modified Z-score methods with configurable thresholds
- **Correlation Analysis**: Pearson, Spearman, and Kendall correlation methods with interactive heatmaps
- **Trend Analysis**: Linear trend detection with change point identification and statistical significance testing
- **Parameter Stability Analysis**: Rolling statistics to assess parameter stability over time

### 🔧 **Enhanced Data Processing**

- **Large Dataset Support**: Intelligent memory estimation and chunked processing for large flight test files
- **Data Quality Assessment**: Automated detection of missing values, duplicates, and constant parameters
- **Memory Optimization**: Automatic datatype optimization to reduce memory usage by 20-40%
- **Progress Tracking**: Real-time progress indicators for long-running operations

### 🎯 **Improved User Experience**

- **Interactive Visualizations**: Professional-grade statistical plots with Plotly integration
- **Actionable Insights**: Automated interpretation and recommendations based on analysis results
- **Comprehensive Reporting**: Detailed statistical summaries with export capabilities

## 🔑 Key Capabilities

### **Core Analysis Features**

- **Dual Y-axis plotting** with automatic unit detection & grouping
- **Enhanced frequency domain tools** (FFT & Welch PSD)
- **Statistical analysis suite** with multiple detection methods
- **Large dataset handling** with memory optimization
- **Interactive data exploration** with professional visualizations

### **Data Processing**

- **Automatic unit detection** from parameter names
- **Flexible timestamp parsing** with multiple format support
- **Data quality validation** with comprehensive reporting
- **Memory-efficient processing** for large datasets
- **Export capabilities** for analysis results

### **Visualization & Analysis**

- **Professional plotting** with customizable themes
- **Statistical overlays** including outliers and trends
- **Correlation heatmaps** with strength indicators
- **Frequency analysis** with peak detection
- **Interactive parameter selection** with real-time updates

## 🎯 Statistical Analysis Features

### **Basic Statistics**

| Metric | Description |
|--------|-------------|
| Descriptive Stats | Mean, median, std dev, min/max, quartiles |
| Distribution Shape | Skewness and kurtosis analysis |
| Variability | Range, IQR, coefficient of variation |
| Data Quality | Missing values, outlier percentages |

### **Outlier Detection Methods**

| Method | Best For | Threshold |
|--------|----------|-----------|
| **IQR Method** | General purpose, robust | 1.5 × IQR (configurable) |
| **Z-Score** | Normal distributions | 2-3 standard deviations |
| **Modified Z-Score** | Non-normal data, small samples | 3.5 (median-based) |

### **Correlation Analysis**

| Method | Use Case | Range |
|--------|----------|-------|
| **Pearson** | Linear relationships | -1 to +1 |
| **Spearman** | Monotonic relationships | -1 to +1 |
| **Kendall** | Small samples, robust | -1 to +1 |

### **Trend Analysis**

- **Linear trend detection** with slope and R² values
- **Statistical significance testing** (p-values)
- **Change point detection** using gradient analysis
- **Trend direction classification** (increasing/decreasing/stable)

## 🎯 Dual Axis & Unit Detection

| Feature | Behavior |
|---------|----------|
| **Auto Detect Units** | Parses units in parentheses or trailing tokens |
| **Axis Assignment** | Dominant unit group → primary axis, others → secondary |
| **Forced Split** | Enable "Force Dual-Axis Split" to separate homogeneous unit groups |
| **Manual Override** | Disable auto detection to specify primary/secondary units directly |
| **Sync Scales** | When units are compatible, align min/max ranges |
| **Legend Formatting** | Toggle units, select annotation style |

**Usage:**

1. Configure a chart (non-frequency)
2. Toggle "Enable Secondary Y Axis" to manually pick secondary parameters OR rely on auto detection by mixing distinct units
3. Adjust unit display & sync options as needed

## 🔊 Frequency Analysis Enhancements

| Option | Effect |
|--------|--------|
| **Detrend** | Removes linear trend/mean before spectral calculation |
| **Window** | Applies selected window (energy-corrected amplitude) |
| **Log Scale** | Logarithmic Y axis (useful for PSD) |
| **Peak Annotation** | Marks dominant non-DC frequency |
| **Irregular Sampling Warning** | Displays if timestamp interval CV > threshold |

## 📊 Large Dataset Handling

### **Memory Management**

- **Automatic estimation** of memory requirements before loading
- **Chunked processing** for files exceeding memory limits
- **Smart sampling** for very large datasets (>1M rows)
- **Memory optimization** through datatype downcasting

### **Performance Features**

- **Progress tracking** with real-time updates
- **Background processing** for long operations
- **Caching** of frequently accessed data
- **Parallel processing** where applicable

## 🛠️ Installation & Setup

### **Requirements**

```bash
numpy>=1.24.0
scipy>=1.10.0
pandas>=2.0.0
streamlit>=1.36.0
plotly>=5.22.0
scikit-learn>=1.3.0
openpyxl>=3.1.0
```

### **Installation**

```bash
# Clone the repository
git clone https://github.com/Martinolli/enhanced_flight_analyzer.git
cd enhanced_flight_analyzer

# Install dependencies
pip install -r requirements.txt

# Run the application
streamlit run app.py
```

## 📈 Usage Examples

### **Statistical Analysis Workflow**

1. **Load Data**: Upload your flight test data file
2. **Select Parameters**: Choose parameters for statistical analysis
3. **Choose Analysis Type**: Basic statistics, correlation, outliers, or trends
4. **Configure Settings**: Adjust thresholds and methods as needed
5. **Run Analysis**: Execute analysis and review results
6. **Export Results**: Save analysis results and visualizations

### **Outlier Detection Example**

```python
# Example: Detect outliers in acceleration data
parameters = ["ENG MOUNT TRIAXIAL ACCEL 1 - X (g)", "ENG MOUNT TRIAXIAL ACCEL 1 - Y (g)"]
method = "iqr"  # or "zscore", "modified_zscore"
threshold = 1.5

# Results include outlier indices, values, and percentages
outliers = detect_outliers(df, parameters, method, threshold)
```

### **Correlation Analysis Example**

```python
# Example: Analyze correlations between engine parameters
parameters = ["Engine Temperature", "Engine Torque", "Engine RPM"]
method = "pearson"  # or "spearman", "kendall"

# Results include correlation matrix and strongest relationships
correlations = compute_correlation_analysis(df, parameters, method)
```

## 🔧 Configuration

### **Statistical Analysis Settings**

- **Outlier Detection**: Configurable methods and thresholds
- **Correlation Analysis**: Multiple correlation methods
- **Trend Analysis**: Significance levels and change point sensitivity
- **Memory Limits**: Adjustable memory thresholds for large datasets

### **Performance Tuning**

- **Chunk Size**: Optimize for your system's memory
- **Sample Rate**: Balance between speed and accuracy for large datasets
- **Caching**: Enable/disable result caching
- **Parallel Processing**: Configure worker threads

## 📊 Data Quality Features

### **Automatic Validation**

- **Missing Value Detection**: Identify and report missing data points
- **Duplicate Row Detection**: Find and flag duplicate measurements
- **Constant Parameter Detection**: Identify parameters with no variation
- **Timestamp Validation**: Check for irregular sampling patterns

### **Quality Metrics**

- **Completeness**: Percentage of non-missing values
- **Consistency**: Duplicate and constant parameter analysis
- **Accuracy**: Outlier detection and statistical validation
- **Temporal Quality**: Sampling rate and irregularity assessment

## 🎨 Visualization Features

### **Interactive Charts**

- **Plotly Integration**: Professional, interactive visualizations
- **Customizable Themes**: Multiple color schemes and layouts
- **Export Options**: PNG, HTML, and PDF export capabilities
- **Responsive Design**: Optimized for desktop and mobile viewing

### **Statistical Plots**

- **Correlation Heatmaps**: Interactive correlation matrices
- **Box Plots**: Outlier visualization with statistical bounds
- **Trend Lines**: Linear regression with confidence intervals
- **Distribution Plots**: Histograms and density plots

## 🚀 Future Enhancements

### **Planned Features**

- **LLM Integration**: Intelligent interpretation and automated reporting
- **Advanced Analytics**: Machine learning-based anomaly detection
- **Real-time Processing**: Live data streaming capabilities
- **Custom Templates**: Saved analysis configurations
- **API Integration**: RESTful API for programmatic access

## 🤝 Contributing

We welcome contributions! Please see our contributing guidelines for details on:

- Code style and standards
- Testing requirements
- Documentation updates
- Feature request process

## 📄 License

Licensed under the Apache License 2.0 – see LICENSE file for details.

## 📞 Support

For questions, issues, or feature requests:

- **GitHub Issues**: Report bugs and request features
- **Documentation**: Comprehensive user guides and API documentation
- **Community**: Join our discussion forums

---

**Enhanced Flight Data Analyzer Pro** - Professional flight test data analysis with advanced statistical capabilities.
