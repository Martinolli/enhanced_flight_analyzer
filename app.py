import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import traceback
import io
import json
from datetime import datetime, timedelta
from scipy.fft import fft, fftfreq
import uuid

# Import custom components
from components.chart_manager import ChartManager
from components.data_processor import DataProcessor
from components.layout_manager import LayoutManager
from components.export_manager import ExportManager

# --- Page Configuration ---
st.set_page_config(
    page_title="Enhanced Flight Data Analyzer Pro",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom CSS for Enhanced Layout ---
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        text-align: center;
    }
    
    .chart-container {
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 10px;
        margin: 5px;
        background: white;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .dashboard-grid {
        display: grid;
        gap: 10px;
        margin: 10px 0;
    }
    
    .grid-2x2 { grid-template-columns: 1fr 1fr; grid-template-rows: 1fr 1fr; }
    .grid-3x2 { grid-template-columns: 1fr 1fr 1fr; grid-template-rows: 1fr 1fr; }
    .grid-2x3 { grid-template-columns: 1fr 1fr; grid-template-rows: 1fr 1fr 1fr; }
    .grid-1x4 { grid-template-columns: 1fr; grid-template-rows: repeat(4, 1fr); }
    
    .parameter-category {
        background: #f8f9fa;
        border-left: 4px solid #007bff;
        padding: 10px;
        margin: 5px 0;
        border-radius: 4px;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
        margin: 5px;
    }
    
    .chart-config-panel {
        background: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# --- Initialize Session State ---
if 'charts' not in st.session_state:
    st.session_state.charts = {}
if 'layout_config' not in st.session_state:
    st.session_state.layout_config = {'type': '2x2', 'charts': []}
if 'data' not in st.session_state:
    st.session_state.data = None
if 'chart_counter' not in st.session_state:
    st.session_state.chart_counter = 0

# --- Initialize Components ---
chart_manager = ChartManager()
data_processor = DataProcessor()
layout_manager = LayoutManager()
export_manager = ExportManager()

# --- App Header ---
st.markdown("""
<div class="main-header">
    <h1>✈️ Enhanced Flight Data Analyzer Pro</h1>
    <p>Advanced multi-chart flight test data analysis with customizable visualizations</p>
</div>
""", unsafe_allow_html=True)

# --- Sidebar Configuration ---
with st.sidebar:
    st.header("🎛️ Control Panel")
    
    # File Upload
    st.subheader("📁 Data Input")
    uploaded_file = st.file_uploader(
        "Upload Flight Data File",
        type=["csv", "txt"],
        help="CSV file with flight test data"
    )
    
    if uploaded_file is not None:
        # Process data
        with st.spinner("Processing data..."):
            df = data_processor.load_data(uploaded_file)
            st.session_state.data = df
        
        if not df.empty:
            st.success(f"✅ Data loaded: {len(df)} points, {len(df.columns)-2} parameters")
            
            # Dashboard Layout Selection
            st.subheader("📊 Dashboard Layout")
            layout_options = {
                "Single Chart": "1x1",
                "Side by Side": "1x2", 
                "2x2 Grid": "2x2",
                "3x2 Grid": "3x2",
                "2x3 Grid": "2x3",
                "Vertical Stack": "1x4"
            }
            
            selected_layout = st.selectbox(
                "Choose Layout",
                options=list(layout_options.keys()),
                index=2
            )
            st.session_state.layout_config['type'] = layout_options[selected_layout]
            
            # Chart Management
            st.subheader("📈 Chart Management")
            
            # Add New Chart Button
            if st.button("➕ Add New Chart", use_container_width=True):
                chart_id = f"chart_{st.session_state.chart_counter}"
                st.session_state.charts[chart_id] = {
                    'id': chart_id,
                    'title': f'Chart {st.session_state.chart_counter + 1}',
                    'type': 'line',
                    'parameters': [],
                    'x_axis': 'Elapsed Time (s)',
                    'y_axis_label': 'Value',
                    'color_scheme': 'viridis'
                }
                st.session_state.chart_counter += 1
                st.rerun()
            
            # Chart Configuration
            if st.session_state.charts:
                st.write("**Active Charts:**")
                for chart_id, config in st.session_state.charts.items():
                    with st.expander(f"⚙️ {config['title']}", expanded=False):
                        # Chart Title
                        new_title = st.text_input(
                            "Chart Title",
                            value=config['title'],
                            key=f"title_{chart_id}"
                        )
                        st.session_state.charts[chart_id]['title'] = new_title
                        
                        # Chart Type
                        chart_type = st.selectbox(
                            "Chart Type",
                            options=['line', 'scatter', 'bar', 'area', 'frequency'],
                            index=['line', 'scatter', 'bar', 'area', 'frequency'].index(config['type']),
                            key=f"type_{chart_id}"
                        )
                        st.session_state.charts[chart_id]['type'] = chart_type

                        if chart_type == 'frequency':
                            freq_type = st.selectbox(
                                "Frequency Analysis Type",
                                options=['fft', 'psd'],
                                index=0,
                                key=f"freq_type_{chart_id}"
                            )
                            st.session_state.charts[chart_id]['freq_type'] = freq_type
                        
                        # Parameter Selection
                        available_params = [col for col in df.columns 
                                          if col not in ['Timestamp', 'Elapsed Time (s)']]
                        
                        selected_params = st.multiselect(
                            "Parameters",
                            options=available_params,
                            default=config['parameters'],
                            key=f"params_{chart_id}"
                        )
                        st.session_state.charts[chart_id]['parameters'] = selected_params
                        
                        # Axis Configuration
                        col1, col2 = st.columns(2)
                        with col1:
                            x_axis = st.selectbox(
                                "X-Axis",
                                options=['Elapsed Time (s)', 'Timestamp'],
                                index=0 if config['x_axis'] == 'Elapsed Time (s)' else 1,
                                key=f"x_axis_{chart_id}"
                            )
                            st.session_state.charts[chart_id]['x_axis'] = x_axis
                        
                        with col2:
                            y_label = st.text_input(
                                "Y-Axis Label",
                                value=config['y_axis_label'],
                                key=f"y_label_{chart_id}"
                            )
                            st.session_state.charts[chart_id]['y_axis_label'] = y_label
                        
                        # Color Scheme
                        color_scheme = st.selectbox(
                            "Color Scheme",
                            options=['viridis', 'plasma', 'inferno', 'magma', 'cividis', 
                                   'blues', 'reds', 'greens', 'purples'],
                            index=0,
                            key=f"color_{chart_id}"
                        )
                        st.session_state.charts[chart_id]['color_scheme'] = color_scheme
                        
                        # Remove Chart Button
                        if st.button(f"🗑️ Remove Chart", key=f"remove_{chart_id}"):
                            del st.session_state.charts[chart_id]
                            st.rerun()
            
            # Export Options
            st.subheader("📤 Export Options")
            if st.button("📊 Export Dashboard as HTML"):
                html_content = export_manager.export_dashboard_html(
                    st.session_state.charts, df
                )
                st.download_button(
                    label="Download HTML Dashboard",
                    data=html_content,
                    file_name=f"flight_dashboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
                    mime="text/html"
                )

            if st.button("📥 Download HTML Report data"):
                # Generate HTML report with charts and data
                if st.session_state.data is not None:
                    html_content = export_manager.generate_auto_report(
                        st.session_state.charts, st.session_state.data
                    )
                    st.download_button(
                        label="Download HTML Report",
                        data=html_content,
                        file_name=f"flight_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
                        mime="text/html"
                    )
                else:
                    st.warning("No data available to generate the HTML report. Please upload a data file first.")

            if st.button("📈 Export All Charts as Images"):
                # This would be implemented to export individual chart images
                st.info("Chart image export functionality coming soon!")

# --- Main Content Area ---
if st.session_state.data is not None and not st.session_state.data.empty:
    df = st.session_state.data
    
    # Data Overview
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h3>{len(df)}</h3>
            <p>Data Points</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <h3>{len(df.columns)-2}</h3>
            <p>Parameters</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        duration_min = df['Elapsed Time (s)'].max() / 60 if 'Elapsed Time (s)' in df.columns else 0
        st.markdown(f"""
        <div class="metric-card">
            <h3>{duration_min:.1f}</h3>
            <p>Duration (min)</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <h3>{len(st.session_state.charts)}</h3>
            <p>Active Charts</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Dashboard Display
    if st.session_state.charts:
        st.header("📊 Flight Data Dashboard")
        
        # Create layout based on configuration
        layout_type = st.session_state.layout_config['type']
        charts = list(st.session_state.charts.values())
        
        if layout_type == "1x1" and len(charts) > 0:
            # Single chart display
            chart_config = charts[0]
            fig = chart_manager.create_chart(df, chart_config)
            if fig:
                st.plotly_chart(fig, use_container_width=True, key=f"display_{chart_config['id']}")
        
        elif layout_type == "1x2" and len(charts) >= 2:
            # Side by side
            col1, col2 = st.columns(2)
            with col1:
                fig1 = chart_manager.create_chart(df, charts[0])
                if fig1:
                    st.plotly_chart(fig1, use_container_width=True, key=f"display_{charts[0]['id']}")
            with col2:
                fig2 = chart_manager.create_chart(df, charts[1])
                if fig2:
                    st.plotly_chart(fig2, use_container_width=True, key=f"display_{charts[1]['id']}")
        
        elif layout_type == "2x2":
            # 2x2 Grid
            for i in range(0, min(4, len(charts)), 2):
                col1, col2 = st.columns(2)
                
                with col1:
                    if i < len(charts):
                        fig = chart_manager.create_chart(df, charts[i])
                        if fig:
                            st.plotly_chart(fig, use_container_width=True, key=f"display_{charts[i]['id']}")
                
                with col2:
                    if i + 1 < len(charts):
                        fig = chart_manager.create_chart(df, charts[i + 1])
                        if fig:
                            st.plotly_chart(fig, use_container_width=True, key=f"display_{charts[i + 1]['id']}")
        
        elif layout_type == "3x2":
            # 3x2 Grid
            for i in range(0, min(6, len(charts)), 3):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if i < len(charts):
                        fig = chart_manager.create_chart(df, charts[i])
                        if fig:
                            st.plotly_chart(fig, use_container_width=True, key=f"display_{charts[i]['id']}")
                
                with col2:
                    if i + 1 < len(charts):
                        fig = chart_manager.create_chart(df, charts[i + 1])
                        if fig:
                            st.plotly_chart(fig, use_container_width=True, key=f"display_{charts[i + 1]['id']}")
                
                with col3:
                    if i + 2 < len(charts):
                        fig = chart_manager.create_chart(df, charts[i + 2])
                        if fig:
                            st.plotly_chart(fig, use_container_width=True, key=f"display_{charts[i + 2]['id']}")
        
        elif layout_type == "1x4":
            # Vertical stack
            for chart_config in charts[:4]:
                fig = chart_manager.create_chart(df, chart_config)
                if fig:
                    st.plotly_chart(fig, use_container_width=True, key=f"display_{chart_config['id']}")
        
        # Advanced Analysis Section
        st.header("🔬 Advanced Analysis")
        
        analysis_tabs = st.tabs(["Parameter Correlation", "Statistical Summary", "Data Quality"])
        
        with analysis_tabs[0]:
            if len(df.select_dtypes(include=[np.number]).columns) > 2:
                numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
                if 'Elapsed Time (s)' in numeric_cols:
                    numeric_cols.remove('Elapsed Time (s)')
                
                if len(numeric_cols) > 1:
                    corr_matrix = df[numeric_cols].corr()
                    fig_corr = px.imshow(
                        corr_matrix,
                        title="Parameter Correlation Matrix",
                        color_continuous_scale='RdBu_r',
                        aspect='auto'
                    )
                    st.plotly_chart(fig_corr, use_container_width=True)
                else:
                    st.info("Need at least 2 numeric parameters for correlation analysis")
            else:
                st.info("No numeric parameters available for correlation analysis")
        
        with analysis_tabs[1]:
            numeric_data = df.select_dtypes(include=[np.number])
            if not numeric_data.empty:
                st.subheader("Statistical Summary")
                st.dataframe(numeric_data.describe())
            else:
                st.info("No numeric data available for statistical analysis")
        
        with analysis_tabs[2]:
            st.subheader("Data Quality Report")
            
            # Missing values
            missing_data = df.isnull().sum()
            if missing_data.sum() > 0:
                st.warning("Missing Values Detected:")
                missing_df = pd.DataFrame({
                    'Parameter': missing_data.index,
                    'Missing Count': missing_data.values,
                    'Missing %': (missing_data.values / len(df) * 100).round(2)
                })
                st.dataframe(missing_df[missing_df['Missing Count'] > 0])
            else:
                st.success("✅ No missing values detected")
            
            # Data range validation
            st.subheader("Parameter Ranges")
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) > 0:
                range_data = []
                for col in numeric_cols:
                    if col != 'Elapsed Time (s)':
                        range_data.append({
                            'Parameter': col,
                            'Min': df[col].min(),
                            'Max': df[col].max(),
                            'Mean': df[col].mean(),
                            'Std Dev': df[col].std()
                        })
                
                if range_data:
                    range_df = pd.DataFrame(range_data)
                    st.dataframe(range_df)
    
    else:
        st.info("👆 Add charts using the sidebar to start visualizing your flight data!")
        
        # Quick Start Templates
        st.header("🚀 Quick Start Templates")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🎯 Control Surfaces Analysis", use_container_width=True):
                # Auto-create charts for control surfaces
                control_params = [col for col in df.columns 
                                if any(keyword in col.lower() for keyword in 
                                      ['aileron', 'elevator', 'rudder', 'flap'])]
                
                if control_params:
                    chart_id = f"chart_{st.session_state.chart_counter}"
                    st.session_state.charts[chart_id] = {
                        'id': chart_id,
                        'title': 'Control Surfaces',
                        'type': 'line',
                        'parameters': control_params[:4],  # Limit to 4 parameters
                        'x_axis': 'Elapsed Time (s)',
                        'y_axis_label': 'Deflection (deg)',
                        'color_scheme': 'viridis'
                    }
                    st.session_state.chart_counter += 1
                    st.rerun()
        
        with col2:
            if st.button("📐 Angle Analysis", use_container_width=True):
                # Auto-create charts for angles
                angle_params = [col for col in df.columns 
                              if any(keyword in col.lower() for keyword in 
                                    ['angle', 'alpha', 'beta'])]
                
                if angle_params:
                    chart_id = f"chart_{st.session_state.chart_counter}"
                    st.session_state.charts[chart_id] = {
                        'id': chart_id,
                        'title': 'Flight Angles',
                        'type': 'line',
                        'parameters': angle_params[:4],
                        'x_axis': 'Elapsed Time (s)',
                        'y_axis_label': 'Angle (deg)',
                        'color_scheme': 'plasma'
                    }
                    st.session_state.chart_counter += 1
                    st.rerun()
        
        with col3:
            if st.button("⚖️ Force Analysis", use_container_width=True):
                # Auto-create charts for forces
                force_params = [col for col in df.columns 
                              if any(keyword in col.lower() for keyword in 
                                    ['force', 'strain', 'load'])]
                
                if force_params:
                    chart_id = f"chart_{st.session_state.chart_counter}"
                    st.session_state.charts[chart_id] = {
                        'id': chart_id,
                        'title': 'Force Measurements',
                        'type': 'line',
                        'parameters': force_params[:4],
                        'x_axis': 'Elapsed Time (s)',
                        'y_axis_label': 'Force (kg)',
                        'color_scheme': 'inferno'
                    }
                    st.session_state.chart_counter += 1
                    st.rerun()

else:
    # Welcome screen
    st.info("📁 Please upload a flight data file to begin analysis")
    
    # Data format help
    with st.expander("📋 Expected Data Format", expanded=True):
        st.markdown("""
        **File Format Requirements:**
        - CSV file with comma-separated values
        - Two header rows:
          - First row: Parameter descriptions/names
          - Second row: Units (EU, deg, kg, etc.)
        - First column: Timestamps in format `day:hour:minute:second.millisecond`
        - Subsequent columns: Numeric flight parameters
        
        **Example Structure:**
        ```
        Description,ANGLE OF ATTACK,AILERON DEFLECTION,ELEVATOR DEFLECTION
        EU,deg,deg,deg
        198:09:40:00.000,30.73,-0.066,-19.52
        198:09:40:00.100,30.73,0.000,-19.19
        ```
        """)
    
    # Feature highlights
    st.header("✨ Enhanced Features")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **🎯 Multi-Chart Dashboard**
        - Multiple charts in customizable layouts
        - 2x2, 3x2, vertical, and side-by-side arrangements
        - Real-time chart configuration
        
        **🎨 Customizable Visualizations**
        - Editable chart titles and axis labels
        - Multiple chart types (line, scatter, bar, area)
        - Color scheme selection
        - Parameter grouping and filtering
        """)
    
    with col2:
        st.markdown("""
        **📊 Advanced Analysis**
        - Parameter correlation analysis
        - Statistical summaries and data quality reports
        - Quick-start templates for common analyses
        - Interactive time-series exploration
        
        **📤 Export Capabilities**
        - HTML dashboard export
        - Individual chart image export
        - Processed data download
        - Professional report generation
        """)

# --- Footer ---
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 20px;'>
    Enhanced Flight Data Analyzer Pro v2.0 | Advanced Multi-Chart Flight Test Analysis
</div>
""", unsafe_allow_html=True)

