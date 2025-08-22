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
from datetime import datetime
import uuid

from components.chart_manager import ChartManager
from components.data_processor import DataProcessor
from components.layout_manager import LayoutManager
from components.config_models import migrate_chart_dict, ChartConfig
from components.export_html_zip import export_charts_as_html_zip
from components.plotly_ui import download_config, sanitize_filename
from components.export_manager import ExportManager

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
    st.session_state.schema_version = 3  # >>> UPDATED <<< bumped for new freq fields / dual axis UI

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
                    with colf2:
                        freq_window = st.selectbox("Window", ['hann', 'hamming', 'blackman', 'rect'],
                                                   index=['hann', 'hamming', 'blackman', 'rect'].index(cfg_obj.freq_window),
                                                   key=f"fwin_{chart_id}")
                        freq_peak = st.checkbox("Annotate Peak", value=cfg_obj.freq_peak_annotation, key=f"fpeak_{chart_id}")
                    with colf3:
                        freq_min_points = st.number_input("Min Points", min_value=4, max_value=2048,
                                                          value=cfg_obj.freq_min_points, key=f"fminp_{chart_id}")
                        freq_irregular_tol = st.number_input("Irregular Tol (CV)", min_value=0.0, max_value=0.5,
                                                             value=float(cfg_obj.freq_irregular_tol), step=0.01,
                                                             key=f"firtol_{chart_id}")
                    if x_param not in ("Elapsed Time (s)", "Timestamp"):
                        st.info("Frequency charts derive sampling from time columns regardless of selected X.")
                else:
                    freq_type = cfg_obj.freq_type
                    freq_detrend = cfg_obj.freq_detrend
                    freq_window = cfg_obj.freq_window
                    freq_log = cfg_obj.freq_log_scale
                    freq_peak = cfg_obj.freq_peak_annotation
                    freq_min_points = cfg_obj.freq_min_points
                    freq_irregular_tol = cfg_obj.freq_irregular_tol

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
                    freq_irregular_tol=freq_irregular_tol
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
    else:
        st.info("📁 Upload a flight data file to begin.")

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

st.markdown("---")
st.markdown("""
<div style='text-align:center;color:#666;padding:20px;'>
Enhanced Flight Data Analyzer Pro v2.3.0-dev
</div>
""", unsafe_allow_html=True)