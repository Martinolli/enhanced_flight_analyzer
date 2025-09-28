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

"""
Export charts as a ZIP file containing HTML files.
Each chart is saved as an individual HTML file within the ZIP archive.

"""
# Import necessary libraries
import io, zipfile
from typing import Dict, Any
import pandas as pd
import plotly.io as pio

def export_charts_as_html_zip(charts: Dict[str, Dict[str, Any]], df: pd.DataFrame, chart_manager) -> bytes:
    """
    Export charts as a ZIP file containing individual HTML files.
    Each chart is saved as an individual HTML file within the ZIP archive.
    Args:
        charts (Dict[str, Dict[str, Any]]): A dictionary of chart configurations.
        df (pd.DataFrame): The DataFrame containing the data for the charts.
        chart_manager: An instance of the chart manager to create charts.
    Returns:
        bytes: The ZIP file content as bytes.
    """
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for chart_id in sorted(charts.keys()):
            cfg = charts[chart_id]
            fig = chart_manager.create_chart(df, cfg)
            if not fig:
                zf.writestr(f"SKIPPED_{chart_id}.txt", "No figure generated.")
                continue
            base = (getattr(cfg, "title", None) or getattr(cfg, "id", chart_id)).replace(" ", "_")
            html = pio.to_html(fig, include_plotlyjs="cdn", full_html=True)
            zf.writestr(f"{base}.html", html)
    buf.seek(0)
    return buf.read()