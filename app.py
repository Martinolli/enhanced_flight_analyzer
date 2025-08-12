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



import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import uuid

from components.chart_manager import ChartManager
from components.data_processor import DataProcessor
from components.layout_manager import LayoutManager
from components.export_manager import ExportManager
from components.config_models import migrate_chart_dict, ChartConfig

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

# Session
if 'charts' not in st.session_state:
    st.session_state.charts = {}
if 'layout_config' not in st.session_state:
    st.session_state.layout_config = {'type': '2x2', 'charts': []}
if 'data' not in st.session_state:
    st.session_state.data = None
if 'schema_version' not in st.session_state:
    st.session_state.schema_version = 2  # bumped for sort_x field

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

st.markdown("""
<div class="main-header">
  <h1>✈️ Enhanced Flight Data Analyzer Pro</h1>
  <p>Advanced multi-chart flight test data analysis with customizable visualizations</p>
</div>
""", unsafe_allow_html=True)

# Sidebar
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

                if chart_type == 'frequency':
                    freq_type = st.selectbox(
                        "Frequency Analysis Type",
                        ['fft', 'psd'],
                        index=0 if cfg_obj.freq_type == 'fft' else 1,
                        key=f"freq_{chart_id}"
                    )
                    if x_param not in ("Elapsed Time (s)", "Timestamp"):
                        st.info("Frequency charts ignore custom X and use time sampling.")
                else:
                    freq_type = cfg_obj.freq_type

                y_options = [c for c in numeric_cols if (chart_type == 'frequency' or c != x_param)]
                y_default = [p for p in cfg_obj.y_params if p in y_options]
                y_params = st.multiselect("Y Parameters", y_options, default=y_default, key=f"y_{chart_id}")

                y_label = st.text_input("Y Axis Label", value=cfg_obj.y_axis_label, key=f"ylab_{chart_id}")
                color_scheme = st.selectbox(
                    "Color Scheme",
                    ['viridis', 'plasma', 'inferno', 'magma', 'cividis', 'blues', 'reds', 'greens', 'purples'],
                    index=['viridis', 'plasma', 'inferno', 'magma', 'cividis', 'blues', 'reds', 'greens', 'purples'].index(cfg_obj.color_scheme),
                    key=f"color_{chart_id}"
                )

                sort_x = cfg_obj.sort_x
                if chart_type == "line" and x_param not in ("Elapsed Time (s)", "Timestamp"):
                    if not df[x_param].is_monotonic_increasing:
                        sort_x = st.checkbox("Sort X to keep line plot (else fallback to scatter)", value=cfg_obj.sort_x, key=f"sort_{chart_id}")
                        if not sort_x:
                            st.info("ℹ️ Non-time X not monotonic; will show scatter unless sorting enabled.")
                    else:
                        sort_x = False  # monotonic already; no need

                updated = ChartConfig(
                    id=chart_id,
                    title=title,
                    chart_type=chart_type,
                    x_param=x_param,
                    y_params=y_params,
                    y_axis_label=y_label,
                    color_scheme=color_scheme,
                    freq_type=freq_type,
                    sort_x=sort_x
                )
                st.session_state.charts[chart_id] = updated.as_dict()

                if st.button("🗑️ Remove", key=f"del_{chart_id}"):
                    del st.session_state.charts[chart_id]
                    st.rerun()

        st.subheader("📤 Export")
        export_debug = st.checkbox("Enable export debug info", value=False, help="Include detailed notes & config dump in HTML export.")
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

        if st.button("Export Charts as PNG Zip"):
            try:
                blob = export_manager.export_charts_as_images_zip(st.session_state.charts, df, fmt="png")
                st.download_button("Download PNG Zip", data=blob, file_name="charts_png.zip")
            except Exception as e:
                st.error(f"Image export failed (install 'kaleido'): {e}")
    else:
        st.info("📁 Upload a flight data file to begin.")

# Main area
if st.session_state.data is not None:
    df = st.session_state.data
    non_param = {'Timestamp', 'Elapsed Time (s)'}
    param_count = sum(1 for c in df.columns if c not in non_param)
    duration_min = (df['Elapsed Time (s)'].max() / 60) if 'Elapsed Time (s)' in df.columns else 0

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
        st.header("🚀 Quick Start Templates")
        col_q1, col_q2, col_q3 = st.columns(3)

        def add_template(title, keywords, label, scheme):
            params = [c for c in df.columns if any(k in c.lower() for k in keywords)]
            if params:
                cid = f"chart_{uuid.uuid4().hex[:8]}"
                st.session_state.charts[cid] = ChartConfig(
                    id=cid,
                    title=title,
                    chart_type='line',
                    x_param='Elapsed Time (s)',
                    y_params=params[:4],
                    y_axis_label=label,
                    color_scheme=scheme
                ).as_dict()
                st.experimental_rerun()

        with col_q1:
            if st.button("🎯 Control Surfaces Analysis", use_container_width=True):
                add_template("Control Surfaces", ['aileron', 'elevator', 'rudder', 'flap'], "Deflection (deg)", 'viridis')
        with col_q2:
            if st.button("📐 Angle Analysis", use_container_width=True):
                add_template("Flight Angles", ['angle', 'alpha', 'beta'], "Angle (deg)", 'plasma')
        with col_q3:
            if st.button("⚖️ Force Analysis", use_container_width=True):
                add_template("Force Measurements", ['force', 'strain', 'load'], "Force (kg)", 'inferno')

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

else:
    st.info("📁 Please upload a flight data file to begin analysis")
    with st.expander("📋 Expected Data Format", expanded=True):
        st.markdown("""
        **File Format Requirements:**
        - CSV with two header rows (names, units)
        - Timestamp format: `day:hour:minute:second.millisecond`
        - Numeric parameters afterwards
        """)
    st.header("✨ Enhanced Features")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("""
        **🎯 Multi-Chart Dashboard**
        - Arbitrary X vs Y plotting
        - Multiple grid layouts
        - Real-time configuration
        """)
    with c2:
        st.markdown("""
        **📤 Export & Analysis**
        - HTML & PNG exports
        - Correlation, stats, quality checks
        - Frequency (FFT/PSD) analysis
        """)

st.markdown("---")
st.markdown("""
<div style='text-align:center;color:#666;padding:20px;'>
Enhanced Flight Data Analyzer Pro v2.2.0
</div>
""", unsafe_allow_html=True)