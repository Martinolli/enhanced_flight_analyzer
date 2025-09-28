# Copyright (c) 2025 Martinolli
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.



# (Only sections that changed are annotated with # >>> UPDATED <<< comments for clarity)
# Full file included for ease of replacement.

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import uuid
import plotly.graph_objects as go
import plotly.express as px
import math

from components.chart_manager import ChartManager
from components.data_processor import DataProcessor
from components.layout_manager import LayoutManager
from components.config_models import migrate_chart_dict, ChartConfig
from components.export_html_zip import export_charts_as_html_zip
from components.plotly_ui import download_config, sanitize_filename
from components.export_manager import ExportManager
from components.statistical_analysis import FlightDataStatistics
from components.large_dataset_handler import LargeDatasetHandler

st.set_page_config(
    page_title="Enhanced Flight Data Analyzer Pro",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
.metric-card {
    background: linear-gradient(135deg,#667eea 0%,#764ba2 100%);
    color:#fff;
    padding:1rem;
    border-radius:8px;
    text-align:center;
    margin:5px;
    box-shadow:0 2px 4px rgba(0,0,0,0.15);
}
</style>
""", unsafe_allow_html=True)

if 'charts' not in st.session_state:
    st.session_state.charts = {}
if 'layout_config' not in st.session_state:
    st.session_state.layout_config = {'type': '2x2', 'charts': []}
if 'data' not in st.session_state:
    st.session_state.data = None
if 'schema_version' not in st.session_state:
    st.session_state.schema_version = 4  # bumped for advanced frequency enhancements
if 'statistics' not in st.session_state:
    st.session_state.statistics = FlightDataStatistics()

chart_manager = ChartManager()
data_processor = DataProcessor()
layout_manager = LayoutManager()
export_manager = ExportManager()

def migrate_all_charts():
    migrated = {}
    for cid, cfg in st.session_state.charts.items():
        migrated[cid] = migrate_chart_dict(cfg).as_dict()
    st.session_state.charts = migrated

migrate_all_charts()

@st.cache_data(show_spinner=False)
def compute_corr(df_num: pd.DataFrame):
    return df_num.corr()

def _format_seconds_as_dhhmmss(seconds: float) -> str:
    """Format seconds as DDD:HH:MM:SS.mmm (days zero-padded to 3)."""
    if seconds is None or (isinstance(seconds, float) and math.isnan(seconds)):
        return ""
    millis_total = int(round(seconds * 1000))
    days, rem_ms = divmod(millis_total, 24 * 60 * 60 * 1000)
    hours, rem_ms = divmod(rem_ms, 60 * 60 * 1000)
    minutes, rem_ms = divmod(rem_ms, 60 * 1000)
    secs, millis = divmod(rem_ms, 1000)
    if millis > 0:
        return f"{days:03d}:{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"
    return f"{days:03d}:{hours:02d}:{minutes:02d}:{secs:02d}"


def create_statistics_section():
    """Create the statistical analysis section in the UI."""
    st.subheader("📈 Statistical Analysis")
    
    if st.session_state.data is not None:
        df = st.session_state.data
        numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
        
        # Parameter selection for analysis
        selected_params = st.multiselect(
            "Select parameters for statistical analysis:",
            numeric_cols,
            default=numeric_cols[:5] if len(numeric_cols) >= 5 else numeric_cols
        )
        
        if selected_params:
            analysis_type = st.selectbox(
                "Analysis Type:",
                ["Basic Statistics", "Correlation Analysis", "Outlier Detection", "Trend Analysis"]
            )
            
            if st.button("Run Analysis"):
                with st.spinner("Performing statistical analysis..."):
                    stats_analyzer = st.session_state.statistics
                    
                    if analysis_type == "Basic Statistics":
                        results = stats_analyzer.compute_basic_statistics(df, selected_params)
                        display_basic_statistics(results)
                        
                    elif analysis_type == "Correlation Analysis":
                        results = stats_analyzer.compute_correlation_analysis(df, selected_params)
                        display_correlation_analysis(results)
                        
                    elif analysis_type == "Outlier Detection":
                        method = st.selectbox("Detection Method:", ["iqr", "zscore", "modified_zscore"])
                        results = stats_analyzer.detect_outliers(df, selected_params, method=method)
                        display_outlier_analysis(results)
                        
                    elif analysis_type == "Trend Analysis":
                        time_col = st.selectbox("Time Column:", ["Elapsed Time (s)", "Timestamp"])
                        results = stats_analyzer.perform_trend_analysis(df, time_col, selected_params)
                        display_trend_analysis(results)
def display_correlation_analysis(results):
    """Display correlation analysis results."""
    st.subheader("🔗 Correlation Analysis Results")
    
    if 'error' in results:
        st.error(f"❌ {results['error']}")
        return
    
    # Display method and data info
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Method", results['method'].title())
    with col2:
        st.metric("Parameters", len(results['parameter_list']))
    with col3:
        st.metric("Data Points", results['data_points'])
    
    # Display strongest correlations
    st.subheader("🏆 Strongest Correlations")
    
    if results['strongest_correlations']:
        correlation_data = []
        for corr in results['strongest_correlations'][:10]:  # Top 10
            correlation_data.append({
                'Parameter 1': corr['param1'],
                'Parameter 2': corr['param2'],
                'Correlation': f"{corr['correlation']:.4f}",
                'Strength': _get_correlation_strength(abs(corr['correlation']))
            })
        
        df_corr = pd.DataFrame(correlation_data)
        st.dataframe(df_corr, use_container_width=True)
        
        # Create correlation heatmap
        st.subheader("🔥 Correlation Heatmap")
        
        # Convert correlation matrix to DataFrame for plotting
        corr_matrix = pd.DataFrame(results['correlation_matrix'])
        
        # Create heatmap
        fig = px.imshow(
            corr_matrix.values,
            x=corr_matrix.columns,
            y=corr_matrix.index,
            color_continuous_scale='RdBu_r',
            aspect='auto',
            title=f"Correlation Matrix ({results['method'].title()})"
        )
        
        fig.update_layout(
            xaxis_title="Parameters",
            yaxis_title="Parameters",
            height=600
        )
        
        # Add correlation values as text
        for i in range(len(corr_matrix.index)):
            for j in range(len(corr_matrix.columns)):
                fig.add_annotation(
                    x=j, y=i,
                    text=f"{corr_matrix.iloc[i, j]:.2f}",
                    showarrow=False,
                    font=dict(color="white" if abs(corr_matrix.iloc[i, j]) > 0.5 else "black")
                )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Interpretation
        st.subheader("📊 Interpretation")
        strong_correlations = [corr for corr in results['strongest_correlations'] if abs(corr['correlation']) > 0.7]
        moderate_correlations = [corr for corr in results['strongest_correlations'] if 0.3 < abs(corr['correlation']) <= 0.7]
        
        if strong_correlations:
            st.success(f"🔴 **Strong correlations found:** {len(strong_correlations)} parameter pairs with |r| > 0.7")
            for corr in strong_correlations[:3]:  # Show top 3
                st.write(f"• **{corr['param1']}** ↔ **{corr['param2']}**: r = {corr['correlation']:.3f}")
        
        if moderate_correlations:
            st.info(f"🟡 **Moderate correlations:** {len(moderate_correlations)} parameter pairs with 0.3 < |r| ≤ 0.7")
        
        weak_correlations = len(results['strongest_correlations']) - len(strong_correlations) - len(moderate_correlations)
        if weak_correlations > 0:
            st.info(f"🟢 **Weak correlations:** {weak_correlations} parameter pairs with |r| ≤ 0.3")
    
    else:
        st.warning("No correlations found.")

def display_outlier_analysis(results):
    """Display outlier analysis results."""
    st.subheader("🎯 Outlier Detection Results")
    
    if not results:
        st.warning("No outlier analysis results to display.")
        return
    
    # Summary metrics
    total_outliers = sum(info['outlier_count'] for info in results.values())
    total_points = sum(len(results) * 1000 for _ in results.values())  # Approximate
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Outliers", total_outliers)
    with col2:
        st.metric("Parameters Analyzed", len(results))
    with col3:
        method = list(results.values())[0]['method'] if results else "Unknown"
        st.metric("Detection Method", method.upper())
    
    # Detailed results for each parameter
    st.subheader("📋 Parameter-wise Results")
    
    outlier_summary = []
    for param, info in results.items():
        outlier_summary.append({
            'Parameter': param,
            'Outliers Found': info['outlier_count'],
            'Outlier %': f"{info['outlier_percentage']:.2f}%",
            'Method': info['method'].upper(),
            'Threshold': info['threshold']
        })
    
    df_outliers = pd.DataFrame(outlier_summary)
    st.dataframe(df_outliers, use_container_width=True)
    
    # Visualization of outliers
    st.subheader("📊 Outlier Visualization")
    
    # Create subplot for each parameter with outliers
    params_with_outliers = [param for param, info in results.items() if info['outlier_count'] > 0]
    
    if params_with_outliers:
        selected_param = st.selectbox("Select parameter to visualize:", params_with_outliers)
        
        if selected_param and selected_param in results:
            info = results[selected_param]
            
            # Create box plot showing outliers
            fig = go.Figure()
            
            # We need the actual data to create the plot - this is a limitation
            # In a real implementation, you'd pass the original data as well
            st.info("💡 **Note:** For detailed outlier visualization, the original data would be needed. "
                   "The outlier indices and values are available in the analysis results.")
            
            # Show outlier details
            if info['outlier_values']:
                st.subheader(f"🔍 Outlier Details for {selected_param}")
                
                outlier_details = pd.DataFrame({
                    'Index': info['outlier_indices'],
                    'Value': info['outlier_values']
                })
                
                st.dataframe(outlier_details, use_container_width=True)
                
                # Show bounds if available
                if info['bounds']['lower'] is not None and info['bounds']['upper'] is not None:
                    st.write(f"**Detection Bounds:**")
                    st.write(f"• Lower bound: {info['bounds']['lower']:.6f}")
                    st.write(f"• Upper bound: {info['bounds']['upper']:.6f}")
    
    else:
        st.success("🎉 No outliers detected in any of the analyzed parameters!")
    
    # Recommendations
    st.subheader("💡 Recommendations")
    
    high_outlier_params = [param for param, info in results.items() if info['outlier_percentage'] > 5]
    
    if high_outlier_params:
        st.warning(f"⚠️ **High outlier percentage detected** in: {', '.join(high_outlier_params)}")
        st.write("Consider:")
        st.write("• Investigating data collection issues")
        st.write("• Checking sensor calibration")
        st.write("• Reviewing flight test conditions")
    else:
        st.success("✅ **Data quality looks good** - low outlier percentages across all parameters")

def display_trend_analysis(results):
    """Display trend analysis results."""
    st.subheader("📈 Trend Analysis Results")
    
    if 'error' in results:
        st.error(f"❌ {results['error']}")
        return
    
    if not results:
        st.warning("No trend analysis results to display.")
        return
    
    # Summary statistics
    total_params = len(results)
    increasing_trends = sum(1 for info in results.values() if info['linear_trend']['trend_direction'] == 'increasing')
    decreasing_trends = sum(1 for info in results.values() if info['linear_trend']['trend_direction'] == 'decreasing')
    stable_trends = total_params - increasing_trends - decreasing_trends
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Parameters Analyzed", total_params)
    with col2:
        st.metric("Increasing Trends", increasing_trends)
    with col3:
        st.metric("Decreasing Trends", decreasing_trends)
    with col4:
        st.metric("Stable Trends", stable_trends)
    
    # Detailed results
    st.subheader("📊 Trend Details")
    
    trend_summary = []
    for param, info in results.items():
        trend = info['linear_trend']
        trend_summary.append({
            'Parameter': param,
            'Trend Direction': trend['trend_direction'].title(),
            'Slope': f"{trend['slope']:.6f}",
            'R²': f"{trend['r_squared']:.4f}",
            'P-value': f"{trend['p_value']:.6f}",
            'Significance': "Significant" if trend['p_value'] < 0.05 else "Not Significant",
            'Data Points': info['data_points'],
            'Duration (s)': f"{info['time_range']['duration']:.1f}"
        })
    
    df_trends = pd.DataFrame(trend_summary)
    st.dataframe(df_trends, use_container_width=True)
    
    # Trend visualization
    st.subheader("📉 Trend Visualization")
    
    # Select parameter for detailed view
    param_options = list(results.keys())
    selected_param = st.selectbox("Select parameter for detailed trend view:", param_options)
    
    if selected_param and selected_param in results:
        info = results[selected_param]
        trend = info['linear_trend']
        
        # Display trend information
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Slope", f"{trend['slope']:.6f}")
            st.metric("R² (Fit Quality)", f"{trend['r_squared']:.4f}")
            st.metric("P-value", f"{trend['p_value']:.6f}")
        
        with col2:
            direction_emoji = {"increasing": "📈", "decreasing": "📉", "stable": "➡️"}
            st.metric("Trend Direction", 
                     f"{direction_emoji.get(trend['trend_direction'], '❓')} {trend['trend_direction'].title()}")
            
            significance = "Significant" if trend['p_value'] < 0.05 else "Not Significant"
            significance_emoji = "✅" if trend['p_value'] < 0.05 else "❌"
            st.metric("Statistical Significance", f"{significance_emoji} {significance}")
        
        # Change points
        if info['change_points']:
            st.subheader("🔄 Change Points Detected")
            change_points_df = pd.DataFrame({
                'Change Point Time (s)': info['change_points']
            })
            st.dataframe(change_points_df, use_container_width=True)
        else:
            st.info("No significant change points detected in the trend.")
        
        # Trend interpretation
        st.subheader("🧠 Interpretation")
        
        if trend['p_value'] < 0.05:
            if trend['trend_direction'] == 'increasing':
                st.success(f"📈 **Significant increasing trend** detected in {selected_param}")
                st.write(f"• The parameter increases by {abs(trend['slope']):.6f} units per second")
                st.write(f"• Trend explains {trend['r_squared']*100:.1f}% of the variance")
            elif trend['trend_direction'] == 'decreasing':
                st.warning(f"📉 **Significant decreasing trend** detected in {selected_param}")
                st.write(f"• The parameter decreases by {abs(trend['slope']):.6f} units per second")
                st.write(f"• Trend explains {trend['r_squared']*100:.1f}% of the variance")
            else:
                st.info(f"➡️ **Stable behavior** in {selected_param}")
        else:
            st.info(f"📊 **No significant trend** detected in {selected_param} (p > 0.05)")
            st.write("The observed changes may be due to random variation rather than a systematic trend.")
    
    # Overall assessment
    st.subheader("🎯 Overall Assessment")
    
    significant_trends = [param for param, info in results.items() 
                         if info['linear_trend']['p_value'] < 0.05]
    
    if significant_trends:
        st.warning(f"⚠️ **{len(significant_trends)} parameters show significant trends:**")
        for param in significant_trends:
            direction = results[param]['linear_trend']['trend_direction']
            emoji = {"increasing": "📈", "decreasing": "📉", "stable": "➡️"}
            st.write(f"• {emoji.get(direction, '❓')} **{param}**: {direction}")
        
        st.write("**Recommendations:**")
        st.write("• Investigate causes of trending parameters")
        st.write("• Consider if trends are expected or indicate issues")
        st.write("• Monitor trending parameters closely in future flights")
    else:
        st.success("✅ **No significant trends detected** - parameters appear stable over time")

def _get_correlation_strength(abs_correlation):
    """Get correlation strength description."""
    if abs_correlation >= 0.8:
        return "Very Strong"
    elif abs_correlation >= 0.6:
        return "Strong"
    elif abs_correlation >= 0.4:
        return "Moderate"
    elif abs_correlation >= 0.2:
        return "Weak"
    else:
        return "Very Weak"

def display_basic_statistics(results):
    """Display basic statistics results."""
    st.subheader("Basic Statistics Results")
    
    for param, stats in results.items():
        st.write(f"**{param}**")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Mean", f"{stats['mean']:.4f}")
            st.metric("Std Dev", f"{stats['std']:.4f}")
        with col2:
            st.metric("Min", f"{stats['min']:.4f}")
            st.metric("Max", f"{stats['max']:.4f}")
        with col3:
            st.metric("Median", f"{stats['median']:.4f}")
            st.metric("IQR", f"{stats['iqr']:.4f}")
        with col4:
            st.metric("Skewness", f"{stats['skewness']:.4f}")
            st.metric("Kurtosis", f"{stats['kurtosis']:.4f}")
        
        st.divider()

def optimize_memory_usage():
    """Optimize memory usage of loaded data."""
    if st.session_state.data is not None:
        original_memory = st.session_state.data.memory_usage(deep=True).sum() / (1024 * 1024)
        
        handler = LargeDatasetHandler()
        optimized_df = handler.optimize_dataframe_memory(st.session_state.data)
        
        new_memory = optimized_df.memory_usage(deep=True).sum() / (1024 * 1024)
        memory_saved = original_memory - new_memory
        
        if memory_saved > 0:
            st.session_state.data = optimized_df
            st.success(f"✅ Memory optimized! Saved {memory_saved:.1f} MB ({memory_saved/original_memory*100:.1f}%)")
        else:
            st.info("ℹ️ Data is already optimally stored")

def show_chart(fig, title_base: str | None = None, key: str | None = None, height: int | None = None):
    if fig is None:
        st.info("No figure to display.")
        return
    title = title_base
    if not title:
        try:
            title = getattr(fig.layout.title, "text", None) or "chart"
        except Exception:
            title = "chart"
    safe_title = sanitize_filename(str(title)) or "chart"
    if height:
        try:
            fig.update_layout(height=height)
        except Exception:
            pass
    try:
        fig.update_xaxes(rangeslider_visible=True)
    except Exception:
        pass
    try:
        cfg = download_config(safe_title)
    except Exception:
        cfg = {"responsive": True, "displaylogo": False}
    st.plotly_chart(fig, use_container_width=True, config=cfg, key=key)

st.markdown("""
<div class="main-header">
  <h1>✈️ Enhanced Flight Data Analyzer Pro</h1>
  <p>Advanced multi-chart flight test data analysis with customizable visualizations</p>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.header("🎛️ Control Panel")
    uploaded_file = st.file_uploader("Upload Flight Data File", type=["csv", "txt"])
    if uploaded_file:
        with st.spinner("Processing data..."):
            st.session_state.data = data_processor.load_data(uploaded_file)

    if st.session_state.data is not None:
        df = st.session_state.data
        st.success(f"✅ Data loaded: {len(df)} points, {len(df.columns)} columns")

        layout_options = {
            "Single Chart": "1x1",
            "Side by Side": "1x2",
            "2x2 Grid": "2x2",
            "3x2 Grid": "3x2",
            "2x3 Grid": "2x3",
            "Vertical Stack": "1x4"
        }
        layout_label = st.selectbox("Choose Layout", list(layout_options.keys()), index=2)
        st.session_state.layout_config['type'] = layout_options[layout_label]

        st.subheader("📈 Chart Management")
        if st.button("➕ Add New Chart", use_container_width=True):
            chart_id = f"chart_{uuid.uuid4().hex[:8]}"
            st.session_state.charts[chart_id] = ChartConfig(
                id=chart_id,
                title=f"Chart {len(st.session_state.charts)+1}"
            ).as_dict()
            st.rerun()

        numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
        time_candidates = [c for c in ["Elapsed Time (s)", "Timestamp"] if c in df.columns]
        x_choices = time_candidates + [c for c in numeric_cols if c not in time_candidates]

        for chart_id, cfg in list(st.session_state.charts.items()):
            cfg_obj = migrate_chart_dict(cfg)
            with st.expander(f"⚙️ {cfg_obj.title}", expanded=False):
                title = st.text_input("Title", value=cfg_obj.title, key=f"title_{chart_id}")
                chart_type = st.selectbox(
                    "Chart Type",
                    ['line', 'scatter', 'bar', 'area', 'frequency'],
                    index=['line', 'scatter', 'bar', 'area', 'frequency'].index(cfg_obj.chart_type),
                    key=f"type_{chart_id}"
                )
                x_param = st.selectbox(
                    "X Parameter",
                    x_choices,
                    index=x_choices.index(cfg_obj.x_param) if cfg_obj.x_param in x_choices else 0,
                    key=f"x_{chart_id}"
                )

                # >>> NEW: Timeframe / X-range filter UI
                st.markdown("**Timeframe / X-range Filter**")
                enable_x_filter = cfg_obj.enable_x_filter
                ts_filter_start = cfg_obj.ts_filter_start
                ts_filter_end = cfg_obj.ts_filter_end
                x_filter_min_value = cfg_obj.x_filter_min_value
                x_filter_max_value = cfg_obj.x_filter_max_value

                # Compute data-driven limits
                x_series = df[x_param]
                if x_param == "Timestamp":
                    x_dt = pd.to_datetime(x_series, errors="coerce")
                    if x_dt.notna().any():
                        dt_min = x_dt.min()
                        dt_max = x_dt.max()

                        # Defaults from config or dataset bounds
                        cfg_start_dt = pd.to_datetime(ts_filter_start, errors="coerce") if ts_filter_start else dt_min
                        cfg_end_dt = pd.to_datetime(ts_filter_end, errors="coerce") if ts_filter_end else dt_max

                        # Compute elapsed seconds relative to start (for user-friendly slider)
                        elapsed_s = (x_dt - dt_min).dt.total_seconds()
                        s_min = float(elapsed_s.min())
                        s_max = float(elapsed_s.max())

                        cfg_start_s = float((cfg_start_dt - dt_min).total_seconds())
                        cfg_end_s = float((cfg_end_dt - dt_min).total_seconds())

                        # Choose a sensible step from median sampling; fallback to 0.1 s
                        if 'Elapsed Time (s)' in df.columns and df['Elapsed Time (s)'].notna().sum() > 1:
                            step_guess = float(df['Elapsed Time (s)'].diff().dropna().median())
                        else:
                            step_guess = float(elapsed_s.diff().dropna().median()) if elapsed_s.notna().sum() > 1 else 0.1
                        step_guess = step_guess if step_guess and step_guess > 0 else 0.1

                        enable_x_filter = st.checkbox("Limit time range", value=enable_x_filter, key=f"xfilter_en_{chart_id}")
                        if enable_x_filter:
                            start_s, end_s = st.slider(
                                "Timeframe (Elapsed seconds)",
                                min_value=s_min,
                                max_value=s_max,
                                value=(cfg_start_s, cfg_end_s),
                                step=step_guess,
                                format="%.3f s",
                                key=f"xfilter_sec_{chart_id}",
                            )
                            
                            # Show DDD:HH:MM:SS.mmm for clarity
                            st.caption(f"Selected: {_format_seconds_as_dhhmmss(start_s)} → {_format_seconds_as_dhhmmss(end_s)}")

                            # Convert back to concrete datetimes for downstream filtering/plotting
                            start_dt = (dt_min + pd.to_timedelta(start_s, unit="s")).to_pydatetime()
                            end_dt = (dt_min + pd.to_timedelta(end_s, unit="s")).to_pydatetime()
                        
                            ts_filter_start = start_dt.isoformat()
                            ts_filter_end = end_dt.isoformat()
                        else:
                            ts_filter_start = None
                            ts_filter_end = None
                    else:
                        enable_x_filter = False
                        ts_filter_start, ts_filter_end = None, None
                        st.info("Timestamp column is not parseable; timeframe filter disabled.")
                        pass

                else:
                    # Numeric X axis (Elapsed Time (s) or other numeric)
                    x_num = pd.to_numeric(x_series, errors="coerce")
                    if x_num.notna().any():
                        vmin = float(np.nanmin(x_num.values))
                        vmax = float(np.nanmax(x_num.values))
                        cur_min = x_filter_min_value if x_filter_min_value is not None else vmin
                        cur_max = x_filter_max_value if x_filter_max_value is not None else vmax

                        enable_x_filter = st.checkbox("Limit X range", value=enable_x_filter, key=f"xfilter_en_{chart_id}")
                        if enable_x_filter:
                            cur_min, cur_max = st.slider(
                                "X range",
                                min_value=vmin,
                                max_value=vmax,
                                value=(cur_min, cur_max),
                                step=(vmax - vmin) / 100 if vmax > vmin else 1.0,
                                key=f"xfilter_num_{chart_id}"
                            )
                            x_filter_min_value = float(cur_min)
                            x_filter_max_value = float(cur_max)
                        else:
                            x_filter_min_value, x_filter_max_value = None, None
                    else:
                        enable_x_filter = False
                        x_filter_min_value, x_filter_max_value = None, None
                        st.info("Selected X is not numeric; X-range filter disabled.")

                # Frequency-specific controls
                if chart_type == 'frequency':
                    freq_type = st.selectbox(
                        "Frequency Analysis Type",
                        ['fft', 'psd'],
                        index=0 if cfg_obj.freq_type == 'fft' else 1,
                        key=f"freq_{chart_id}"
                    )
                    st.markdown("**Frequency Options**")
                    colf1, colf2, colf3 = st.columns(3)
                    with colf1:
                        freq_detrend = st.checkbox("Detrend", value=cfg_obj.freq_detrend, key=f"fdetr_{chart_id}")
                        freq_log = st.checkbox("Log Scale Y", value=cfg_obj.freq_log_scale, key=f"flog_{chart_id}")
                        override_fs = st.number_input("Override fs (Hz)", min_value=0.0,
                                                      value=float(cfg_obj.override_sample_rate or 0.0),
                                                      help="Set >0 to ignore computed fs.", key=f"ofs_{chart_id}")
                    with colf2:
                        freq_window = st.selectbox("Window", ['hann', 'hamming', 'blackman', 'rect'],
                                                   index=['hann', 'hamming', 'blackman', 'rect'].index(cfg_obj.freq_window),
                                                   key=f"fwin_{chart_id}")
                        freq_peak = st.checkbox("Annotate Peak", value=cfg_obj.freq_peak_annotation, key=f"fpeak_{chart_id}")
                        max_freq = st.number_input("Max Freq (Hz)", min_value=0.0,
                                                   value=float(cfg_obj.max_frequency or 0.0),
                                                   help="0 = full Nyquist", key=f"fmax_{chart_id}")
                    with colf3:
                        freq_min_points = st.number_input("Min Points", min_value=4, max_value=2048,
                                                          value=cfg_obj.freq_min_points, key=f"fminp_{chart_id}")
                        freq_irregular_tol = st.number_input("Irregular Tol (CV)", min_value=0.0, max_value=0.5,
                                                             value=float(cfg_obj.freq_irregular_tol), step=0.01,
                                                             key=f"firtol_{chart_id}")
                        highpass_cut = st.number_input("High-pass (Hz)", min_value=0.0,
                                                       value=float(cfg_obj.highpass_cutoff or 0.0),
                                                       help="0 = none", key=f"fhp_{chart_id}")

                    # Welch / PSD parameters (shown regardless; applied only if PSD)
                    colw1, colw2 = st.columns(2)
                    with colw1:
                        welch_nperseg = st.number_input("Welch nperseg", min_value=32, max_value=65536,
                                                        value=int(cfg_obj.welch_nperseg), step=32,
                                                        help="Power of two recommended (e.g. 1024, 2048).",
                                                        key=f"wnps_{chart_id}")
                    with colw2:
                        welch_overlap = st.slider("Overlap %", 0, 90, int(cfg_obj.welch_overlap * 100),
                                                  help="Percentage overlap between segments", key=f"wov_{chart_id}") / 100.0

                    band_rms_str = st.text_input("Band RMS (e.g. 0-20;20-50;50-120)",
                                                 value=";".join(
                                                     f"{b[0]}-{b[1]}" for b in cfg_obj.band_rms
                                                 ),
                                                 help="Integrate PSD in each band; only PSD mode.",
                                                 key=f"brms_{chart_id}")
                    parsed_bands = []
                    if band_rms_str.strip():
                        for token in band_rms_str.split(";"):
                            token = token.strip()
                            if not token:
                                continue
                            if "-" in token:
                                try:
                                    lo_s, hi_s = token.split("-", 1)
                                    lo_v = float(lo_s)
                                    hi_v = float(hi_s)
                                    if hi_v > lo_v > 0:
                                        parsed_bands.append([lo_v, hi_v])
                                except Exception:
                                    pass

                    if x_param not in ("Elapsed Time (s)", "Timestamp"):
                        st.info("Frequency charts derive sampling from time columns regardless of selected X.")

                else:
                    # (existing non-frequency branch unchanged)
                    freq_type = cfg_obj.freq_type
                    freq_detrend = cfg_obj.freq_detrend
                    freq_window = cfg_obj.freq_window
                    freq_log = cfg_obj.freq_log_scale
                    freq_peak = cfg_obj.freq_peak_annotation
                    freq_min_points = cfg_obj.freq_min_points
                    freq_irregular_tol = cfg_obj.freq_irregular_tol
                    override_fs = cfg_obj.override_sample_rate or 0.0
                    max_freq = cfg_obj.max_frequency or 0.0
                    highpass_cut = cfg_obj.highpass_cutoff or 0.0
                    welch_nperseg = cfg_obj.welch_nperseg
                    welch_overlap = cfg_obj.welch_overlap
                    parsed_bands = cfg_obj.band_rms

                y_options = [c for c in numeric_cols if (chart_type == 'frequency' or c != x_param)]
                y_default = [p for p in cfg_obj.y_params if p in y_options]
                y_params = st.multiselect("Primary Y Parameters", y_options, default=y_default, key=f"y_{chart_id}")

                # >>> UPDATED <<< Dual axis / unit detection UI for non-frequency charts
                secondary_y_params = list(cfg_obj.secondary_y_params)
                synchronize_scales = cfg_obj.synchronize_scales
                auto_detect_units = cfg_obj.auto_detect_units
                force_unit_detection = cfg_obj.force_unit_detection
                show_units_in_legend = cfg_obj.show_units_in_legend
                unit_annotation_style = cfg_obj.unit_annotation_style
                manual_y_unit = cfg_obj.manual_y_unit
                manual_secondary_y_unit = cfg_obj.manual_secondary_y_unit

                if chart_type != 'frequency':
                    enable_secondary = st.checkbox("Enable Secondary Y Axis", value=bool(secondary_y_params),
                                                   key=f"sec_enable_{chart_id}")
                    if enable_secondary:
                        available_secondary = [p for p in y_options if p not in y_params]
                        secondary_y_params = st.multiselect(
                            "Secondary Y Parameters",
                            available_secondary,
                            default=[p for p in secondary_y_params if p in available_secondary],
                            key=f"sec_params_{chart_id}"
                        )
                    else:
                        secondary_y_params = []

                    st.markdown("**Unit / Axis Options**")
                    colu1, colu2, colu3 = st.columns(3)
                    with colu1:
                        auto_detect_units = st.checkbox("Auto Detect Units", value=auto_detect_units,
                                                        key=f"auto_units_{chart_id}")
                        show_units_in_legend = st.checkbox("Units in Legend", value=show_units_in_legend,
                                                           key=f"units_leg_{chart_id}")
                    with colu2:
                        force_unit_detection = st.checkbox("Force Dual-Axis Split", value=force_unit_detection,
                                                           key=f"force_unit_{chart_id}")
                        synchronize_scales = st.checkbox("Sync Scales", value=synchronize_scales,
                                                         key=f"sync_{chart_id}")
                    with colu3:
                        unit_annotation_style = st.selectbox("Unit Style",
                                                             ["parentheses", "bracket", "suffix"],
                                                             index=["parentheses", "bracket", "suffix"].index(unit_annotation_style),
                                                             key=f"ustyle_{chart_id}")

                    if not auto_detect_units:
                        colm1, colm2 = st.columns(2)
                        with colm1:
                            manual_y_unit = st.text_input("Primary Unit Override", value=manual_y_unit or "",
                                                          key=f"munit_{chart_id}")
                        with colm2:
                            manual_secondary_y_unit = st.text_input("Secondary Unit Override",
                                                                    value=manual_secondary_y_unit or "",
                                                                    key=f"munit2_{chart_id}")
                else:
                    secondary_y_params = []
                    synchronize_scales = False
                    auto_detect_units = True
                    force_unit_detection = False
                    show_units_in_legend = True
                    unit_annotation_style = "parentheses"
                    manual_y_unit = None
                    manual_secondary_y_unit = None

                y_label = st.text_input("Primary Y Axis Label", value=cfg_obj.y_axis_label, key=f"ylab_{chart_id}")
                if chart_type != 'frequency':
                    secondary_y_axis_label = st.text_input("Secondary Y Axis Label",
                                                           value=cfg_obj.secondary_y_axis_label or "",
                                                           key=f"ylab2_{chart_id}")
                else:
                    secondary_y_axis_label = ""

                color_scheme = st.selectbox(
                    "Color Scheme",
                    ['viridis', 'plasma', 'inferno', 'magma', 'cividis', 'blues', 'reds', 'greens', 'purples'],
                    index=['viridis', 'plasma', 'inferno', 'magma', 'cividis', 'blues', 'reds', 'greens', 'purples'].index(cfg_obj.color_scheme),
                    key=f"color_{chart_id}"
                )

                sort_x = cfg_obj.sort_x
                if chart_type == "line" and x_param not in ("Elapsed Time (s)", "Timestamp"):
                    if not df[x_param].is_monotonic_increasing:
                        sort_x = st.checkbox("Sort X for line continuity", value=cfg_obj.sort_x, key=f"sort_{chart_id}")
                        if not sort_x:
                            st.info("Non-monotonic X → will fallback to scatter.")
                    else:
                        sort_x = False

                updated = ChartConfig(
                    id=chart_id,
                    title=title,
                    chart_type=chart_type,
                    x_param=x_param,
                    y_params=y_params,
                    secondary_y_params=secondary_y_params,
                    y_axis_label=y_label,
                    secondary_y_axis_label=secondary_y_axis_label,
                    color_scheme=color_scheme,
                    freq_type=freq_type,
                    sort_x=sort_x,
                    show_x_range_slider=cfg_obj.show_x_range_slider,
                    enable_x_filter=enable_x_filter,
                    x_filter_min_value=x_filter_min_value,
                    x_filter_max_value=x_filter_max_value,
                    ts_filter_start=ts_filter_start,
                    ts_filter_end=ts_filter_end,
                    auto_detect_units=auto_detect_units,
                    force_unit_detection=force_unit_detection,
                    synchronize_scales=synchronize_scales,
                    show_units_in_legend=show_units_in_legend,
                    unit_annotation_style=unit_annotation_style,
                    manual_y_unit=manual_y_unit or None,
                    manual_secondary_y_unit=manual_secondary_y_unit or None,
                    freq_detrend=freq_detrend,
                    freq_window=freq_window,
                    freq_log_scale=freq_log,
                    freq_peak_annotation=freq_peak,
                    freq_min_points=freq_min_points,
                    freq_irregular_tol=freq_irregular_tol,
                    override_sample_rate=override_fs or None,
                    max_frequency=max_freq or None,
                    welch_nperseg=welch_nperseg,
                    welch_overlap=welch_overlap,
                    highpass_cutoff=highpass_cut or None,
                    band_rms=parsed_bands
                )
                st.session_state.charts[chart_id] = updated.as_dict()

                if st.button("🗑️ Remove", key=f"del_{chart_id}"):
                    del st.session_state.charts[chart_id]
                    st.rerun()

        st.subheader("📤 Export")
        export_debug = st.checkbox("Enable export debug info", value=False,
                                   help="Include detailed notes & config dump in HTML export.")
        if st.button("Export HTML Dashboard"):
            html_content = export_manager.export_dashboard_html(
                st.session_state.charts,
                df,
                debug=export_debug
            )
            if html_content:
                st.download_button(
                    "Download HTML",
                    data=html_content,
                    file_name=f"flight_dashboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
                    mime="text/html"
                )

        if st.button("Export Charts as HTML Zip"):
            blob = export_charts_as_html_zip(st.session_state.charts, df, chart_manager)
            st.download_button("Download HTML Zip", data=blob, file_name="charts_html.zip")
        
        st.subheader("📊 Generate Report")
        st.markdown("Generate a comprehensive analysis report with parameter limit compliance and statistical analysis.")
        
        # Flight information inputs (optional)
        with st.expander("✈️ Flight Information (Optional)", expanded=False):
            flight_id = st.text_input("Flight ID", placeholder="e.g., FL001-2024")
            aircraft = st.text_input("Aircraft", placeholder="e.g., Boeing 737-800")
            flight_date = st.date_input("Flight Date")
            pilot = st.text_input("Pilot", placeholder="e.g., John Doe")
        
        if st.button("🔍 Generate Parameter Limit Analysis Report", use_container_width=True):
            with st.spinner("Generating comprehensive flight analysis report..."):
                try:
                    from components.report_generator import FlightReportGenerator
                    
                    # Prepare flight info
                    flight_info = {
                        'flight_id': flight_id if flight_id else 'N/A',
                        'aircraft': aircraft if aircraft else 'N/A',
                        'date': flight_date.strftime('%Y-%m-%d') if flight_date else 'N/A',
                        'pilot': pilot if pilot else 'N/A'
                    }
                    
                    # Generate report
                    report_generator = FlightReportGenerator()
                    html_report = report_generator.generate_comprehensive_report(df, flight_info)
                    
                    # Offer download
                    st.download_button(
                        "📥 Download Analysis Report",
                        data=html_report,
                        file_name=f"flight_analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
                        mime="text/html",
                        use_container_width=True
                    )
                    
                    st.success("✅ Report generated successfully! Click the download button above.")
                    
                except Exception as e:
                    st.error(f"❌ Error generating report: {str(e)}")
                    st.error("Please ensure all required components are properly installed.")
    else:
        st.info("📁 Upload a flight data file to begin.")

if st.session_state.data is not None:
    df = st.session_state.data
    non_param = {'Timestamp', 'Elapsed Time (s)'}
    param_count = sum(1 for c in df.columns if c not in non_param)
    # Fix duration calculation - use the actual elapsed time range, not just max value
    if 'Elapsed Time (s)' in df.columns:
        elapsed_time = df['Elapsed Time (s)']
        duration_min = (elapsed_time.max() - elapsed_time.min()) / 60
    else:
        duration_min = 0

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"<div class='metric-card'><h3>{len(df)}</h3><p>Data Points</p></div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div class='metric-card'><h3>{param_count}</h3><p>Parameters</p></div>", unsafe_allow_html=True)
    with c3:
        st.markdown(f"<div class='metric-card'><h3>{duration_min:.1f}</h3><p>Duration (min)</p></div>", unsafe_allow_html=True)
    with c4:
        st.markdown(f"<div class='metric-card'><h3>{len(st.session_state.charts)}</h3><p>Active Charts</p></div>", unsafe_allow_html=True)

    if st.session_state.charts:
        st.header("📊 Flight Data Dashboard")
        layout_manager.create_layout_grid(
            st.session_state.layout_config['type'],
            list(st.session_state.charts.values()),
            chart_manager,
            df
        )
    else:
        st.info("👆 Add charts using the sidebar to start visualizing your flight data!")

    st.header("🔬 Advanced Analysis")
    tabs = st.tabs(["Parameter Correlation", "Statistical Summary", "Data Quality"])

    with tabs[0]:
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        numeric_for_corr = [c for c in numeric_cols if c != 'Elapsed Time (s)']
        if len(numeric_for_corr) > 1:
            corr = compute_corr(df[numeric_for_corr])
            import plotly.express as px
            fig_corr = px.imshow(corr, title="Parameter Correlation Matrix",
                                 color_continuous_scale='RdBu_r', aspect='auto')
            fig_corr.update_xaxes(rangeslider_visible=True)
            # Add gridlines to correlation chart
            fig_corr.update_layout(
                xaxis=dict(showgrid=True, gridwidth=.5, gridcolor='black'),
                yaxis=dict(showgrid=True, gridwidth=.5, gridcolor='black')
            )
            st.plotly_chart(fig_corr, use_container_width=True)
        else:
            st.info("Need at least 2 numeric parameters (excluding time) for correlation.")

    with tabs[1]:
        numeric_data = df.select_dtypes(include=[np.number])
        if numeric_data.empty:
            st.info("No numeric data available.")
        else:
            st.subheader("Statistical Summary")
            st.dataframe(numeric_data.describe())

    with tabs[2]:
        st.subheader("Data Quality Report")
        missing = df.isnull().sum()
        if missing.sum() > 0:
            st.warning("Missing Values Detected:")
            st.dataframe(pd.DataFrame({
                'Parameter': missing.index,
                'Missing Count': missing.values,
                'Missing %': (missing.values / len(df) * 100).round(2)
            }).query("`Missing Count` > 0"))
        else:
            st.success("✅ No missing values detected")

        st.subheader("Parameter Ranges")
        rows = []
        for col in df.select_dtypes(include=[np.number]).columns:
            if col != 'Elapsed Time (s)':
                rows.append({
                    'Parameter': col,
                    'Min': df[col].min(),
                    'Max': df[col].max(),
                    'Mean': df[col].mean(),
                    'Std Dev': df[col].std()
                })
        if rows:
            st.dataframe(pd.DataFrame(rows))

    if st.session_state.data is not None:
        create_statistics_section()

    if st.session_state.data is not None:
        if st.sidebar.button("🔧 Optimize Memory"):
            optimize_memory_usage()

else:
    st.info("📁 Please upload a flight data file to begin analysis")

st.markdown("---")
st.markdown("""
<div style='text-align:center;color:#666;padding:20px;'>
Enhanced Flight Data Analyzer Pro v2.4.0-dev
</div>
""", unsafe_allow_html=True)
