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
Manages export functionality for charts, dashboards, and data.
Hardened HTML export with:
  - Per-figure try/except
  - Fallback JSON + Plotly.newPlot embedding
  - Detailed error notes
  - Optional debug section
"""
# Required imports
import streamlit as st
import pandas as pd
import plotly.io as pio
from datetime import datetime
import json
from typing import Dict, Any, List
import io
import zipfile
import re
import traceback
# Local imports
from .chart_manager import ChartManager
from .config_models import migrate_chart_dict, ChartConfig


def _sanitize_html_id(raw: str) -> str:
    """
    Sanitize a string to be safe for HTML element IDs.
    Replace unsafe characters with underscores.
        Args:
        raw: Input string
    Returns: Sanitized string
    """
    return re.sub(r'[^A-Za-z0-9_\-]', '_', str(raw))


class ExportManager:
    """
    Manages export functionality for charts, dashboards, and data.
    Hardened HTML export with:
      - Per-figure try/except
      - Fallback JSON + Plotly.newPlot embedding
      - Detailed error notes
      - Optional debug section
    """

    def __init__(self):
        self.chart_manager = ChartManager()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def export_dashboard_html(
        self,
        charts: Dict[str, Dict[str, Any]],
        df: pd.DataFrame,
        debug: bool = False
    ) -> str:
        """
        Export all charts to a single self-contained HTML document.
        Args:
            charts: chart configuration dict (chart_id -> config dict)
            df: DataFrame
            debug: if True, embed extra diagnostics
        Returns:
            Full HTML string (or "" on catastrophic failure).
        """
        chart_html_blocks: List[str] = []
        notes: List[str] = []
        js_payloads: List[str] = []  # fallback JS code segments

        # Sort for determinism
        for chart_id in sorted(charts.keys()):
            cfg_raw = charts[chart_id]
            cfg_obj = migrate_chart_dict(cfg_raw)
            safe_id = _sanitize_html_id(cfg_obj.id or chart_id)

            fig = None
            try:
                fig = self.chart_manager.create_chart(df, cfg_obj)
                if fig is None:
                    notes.append(f"{chart_id}: skipped (no figure generated).")
                    continue

                # Attempt primary export path
                chart_div = self._figure_to_html(fig, safe_id, include_plotlyjs=(len(chart_html_blocks) == 0))
                if chart_div is None:
                    # Fallback to manual embedding
                    fallback_html, fallback_js = self._figure_fallback_json(fig, safe_id, first=(len(chart_html_blocks) == 0))
                    chart_html_blocks.append(fallback_html)
                    js_payloads.append(fallback_js)
                    notes.append(f"{chart_id}: used fallback embedding.")
                else:
                    chart_html_blocks.append(chart_div)

            except Exception as e:
                tb = traceback.format_exc()
                notes.append(f"{chart_id}: FAILED export ({e}).")
                if debug:
                    notes.append(f"{chart_id} traceback:\n{tb}")
                # Attempt minimal fallback if fig exists
                if fig is not None:
                    try:
                        fallback_html, fallback_js = self._figure_fallback_json(fig, safe_id, first=(len(chart_html_blocks) == 0))
                        chart_html_blocks.append(fallback_html)
                        js_payloads.append(fallback_js)
                        notes.append(f"{chart_id}: fallback after exception.")
                    except Exception as inner_fallback_exc:
                        notes.append(f"{chart_id}: fallback also failed: {inner_fallback_exc}")

        metadata = {
            "export_date": datetime.now().isoformat(),
            "data_points": int(len(df)),
            "parameters": int(len(df.columns)),
            "charts_count": int(len(charts)),
            "rendered_charts": len(chart_html_blocks),
            "notes_count": len(notes)
        }

        notes_block = ""
        if notes:
            notes_block = "<h2>Export Notes</h2><ul>" + "".join(
                f"<li><pre style='white-space:pre-wrap'>{self._escape_html(n)}</pre></li>" for n in notes
            ) + "</ul>"

        debug_block = ""
        if debug:
            # Add a summary of chart config raw JSON (sanitized)
            debug_block = "<h2>Debug Config Dump</h2><pre style='white-space:pre-wrap;font-size:12px;'>"
            try:
                dumped = json.dumps(charts, indent=2)
            except TypeError:
                dumped = "Could not serialize charts dict (TypeError)."
            debug_block += self._escape_html(dumped) + "</pre>"

        # Combine fallback JS if any
        fallback_js_block = ""
        if js_payloads:
            fallback_js_block = "<script>\n" + "\n".join(js_payloads) + "\n</script>"

        html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>Flight Data Analysis Dashboard</title>
<style>
/* Base styles with export-safe typography */
body {{ 
  font-family: 'Arial', 'Helvetica', sans-serif; 
  margin: 20px; 
  line-height: 1.4;
  color: #333;
  background: white;
}}

/* Grid layout with improved responsiveness */
.grid {{ 
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(480px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}}

/* Chart containers with export-optimized styling */
.chart-container {{
  border: 1px solid #ccc;
  padding: 15px;
  border-radius: 8px;
  background: white;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
  min-height: 400px;
  page-break-inside: avoid; /* PDF export optimization */
}}

/* Typography optimizations */
h1 {{ 
  text-align: center; 
  font-size: 28px;
  margin-bottom: 30px;
  color: #2c3e50;
  page-break-after: avoid;
}}

h2 {{ 
  font-size: 20px;
  margin-top: 30px;
  margin-bottom: 15px;
  color: #34495e;
  page-break-after: avoid;
}}

/* Metadata and notes styling */
pre.metadata {{ 
  background: #f8f9fa; 
  padding: 15px; 
  border-radius: 6px;
  border: 1px solid #e9ecef;
  font-size: 12px;
  overflow-x: auto;
  page-break-inside: avoid;
}}

/* Export notes styling */
ul {{ 
  margin: 10px 0;
  padding-left: 20px;
}}

li {{ 
  margin-bottom: 8px;
}}

li pre {{
  background: #f8f9fa;
  border: 1px solid #e9ecef;
  padding: 8px;
  border-radius: 4px;
  font-size: 11px;
  margin: 5px 0;
}}

/* Print/PDF optimizations */
@media print {{
  body {{ 
    margin: 0; 
    font-size: 12pt;
  }}
  
  .grid {{
    grid-template-columns: 1fr;
    gap: 15px;
  }}
  
  .chart-container {{
    margin-bottom: 20px;
    border: 2px solid #333;
    box-shadow: none;
    min-height: 350px;
  }}
  
  h1 {{ 
    font-size: 24pt;
    margin-bottom: 20px;
  }}
  
  h2 {{ 
    font-size: 16pt;
    margin-top: 20px;
  }}
  
  /* Ensure charts don't break across pages */
  .chart-container, pre.metadata {{
    page-break-inside: avoid;
  }}
}}

/* High-DPI display optimizations */
@media (-webkit-min-device-pixel-ratio: 2), (min-resolution: 192dpi) {{
  .chart-container {{
    border-width: 0.5px;
  }}
}}
</style>
</head>
<body>
<h1>Flight Data Analysis Dashboard</h1>
<div class="grid">
{''.join(chart_html_blocks)}
</div>
<h2>Metadata</h2>
<pre class="metadata">{self._escape_html(json.dumps(metadata, indent=2))}</pre>
{notes_block}
{debug_block}
{fallback_js_block}
</body>
</html>"""
        return html

    def export_charts_as_images_zip(
        self,
        charts: Dict[str, Dict[str, Any]],
        df: pd.DataFrame,
        fmt: str = "png",
        scale: float = 2.0,
        width: int = 1200,
        height: int = 800,
        export_safe_styling: bool = True
    ) -> bytes:
        """
        Export charts as images zipped with export-safe styling.
        
        Args:
            charts: Chart configuration dictionary
            df: DataFrame with data
            fmt: Export format ('png', 'svg', 'pdf', 'jpg', 'jpeg', 'webp', 'eps')
            scale: Scale factor for high-DPI output (affects raster formats)
            width: Image width in pixels
            height: Image height in pixels
            export_safe_styling: Apply export-optimized styling
        
        Returns:
            ZIP file bytes containing exported charts
        """
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for chart_id in sorted(charts.keys()):
                cfg_raw = charts[chart_id]
                try:
                    cfg_obj = migrate_chart_dict(cfg_raw)
                    fig = self.chart_manager.create_chart(df, cfg_obj)
                    if not fig:
                        zf.writestr(f"SKIPPED_{chart_id}.txt", "No figure generated.")
                        continue
                    
                    # Apply export-safe styling
                    if export_safe_styling:
                        fig = self._apply_export_safe_styling(fig, fmt)
                    
                    safe_base = _sanitize_html_id(cfg_obj.title.replace(' ', '_')) or _sanitize_html_id(cfg_obj.id)
                    
                    # Configure export parameters based on format
                    export_params = {
                        'format': fmt,
                        'width': width,
                        'height': height
                    }
                    
                    # Scale factor only applies to raster formats
                    if fmt.lower() in ['png', 'jpg', 'jpeg', 'webp']:
                        export_params['scale'] = scale
                    
                    img_bytes = fig.to_image(**export_params)
                    zf.writestr(f"{safe_base}.{fmt}", img_bytes)
                except Exception as e:
                    zf.writestr(f"ERROR_{chart_id}.txt", f"{e}\n{traceback.format_exc()}")
        buf.seek(0)
        return buf.read()

    # ------------------------------------------------------------------
    # Internal Helpers
    # ------------------------------------------------------------------
    def _figure_to_html(self, fig, safe_id: str, include_plotlyjs: bool) -> Any:
        """
        Try standard pio.to_html route. Return HTML string or None if failure.
        Args:
            fig: Plotly figure object
            safe_id: Sanitized unique ID for HTML element
            include_plotlyjs: If True, include Plotly.js in output
        Returns:
            HTML div string or None on failure
        """
        try:
            return pio.to_html(
                fig,
                include_plotlyjs=('cdn' if include_plotlyjs else False),
                full_html=False,
                div_id=f"chart_{safe_id}"
            )
        except Exception:
            return None

    def _figure_fallback_json(self, fig, safe_id: str, first: bool = False):
        """
        Fallback method: embed figure JSON + Plotly.newPlot.
        Args:
            fig: Plotly figure object
            safe_id: Sanitized unique ID for HTML element
            first: If True, include Plotly.js loader
        Returns:
            (html_div, js_code).
        """
        fig_json = fig.to_plotly_json()
        # Minimal container
        div_html = f"<div class='chart-container'><div id='chart_{safe_id}'></div></div>"
        # Load plotly if first fallback and not already included
        loader = "https://cdn.plot.ly/plotly-latest.min.js"
        load_script = f"var ensurePlotly=window._fallbackPlotlyLoaded; if(!ensurePlotly){{var s=document.createElement('script');s.src='{loader}';s.onload=function(){{window._fallbackPlotlyLoaded=true;Plotly.newPlot('chart_{safe_id}', {json.dumps(fig_json.get('data', []))}, {json.dumps(fig_json.get('layout', {}))});}};document.head.appendChild(s);}} else {{Plotly.newPlot('chart_{safe_id}', {json.dumps(fig_json.get('data', []))}, {json.dumps(fig_json.get('layout', {}))});}}"
        js_code = load_script
        return div_html, js_code

    def _apply_export_safe_styling(self, fig, export_format: str):
        """
        Apply export-safe styling optimizations for different formats.
        
        Args:
            fig: Plotly figure object
            export_format: Target export format ('png', 'svg', 'pdf', etc.)
        
        Returns:
            Modified figure with export-optimized styling
        """
        # Create a copy to avoid modifying the original
        fig_copy = fig
        
        # Font optimizations for export
        export_font_family = "Arial, sans-serif"  # Widely supported font
        export_font_size = 14 if export_format.lower() in ['svg', 'pdf'] else 12
        
        # Title font size should be larger
        title_font_size = export_font_size + 4
        
        # Axis and legend font sizes
        axis_font_size = export_font_size - 1
        legend_font_size = export_font_size - 1
        
        # Color and line optimizations
        if export_format.lower() in ['pdf', 'svg']:
            # Vector formats: use crisp lines and ensure good contrast
            line_width = 2.5
            marker_size = 8
            grid_color = "rgba(128, 128, 128, 0.3)"
        else:
            # Raster formats: slightly thicker for better visibility at various scales
            line_width = 2.0
            marker_size = 6
            grid_color = "rgba(128, 128, 128, 0.2)"
        
        # Apply layout optimizations
        fig_copy.update_layout(
            # Font settings
            font=dict(
                family=export_font_family,
                size=export_font_size,
                color="black"
            ),
            title=dict(
                font=dict(
                    family=export_font_family,
                    size=title_font_size,
                    color="black"
                )
            ),
            # Axis improvements
            xaxis=dict(
                title_font=dict(size=axis_font_size, family=export_font_family),
                tickfont=dict(size=axis_font_size-1, family=export_font_family),
                gridcolor=grid_color,
                linecolor="black",
                linewidth=1
            ),
            yaxis=dict(
                title_font=dict(size=axis_font_size, family=export_font_family),
                tickfont=dict(size=axis_font_size-1, family=export_font_family),
                gridcolor=grid_color,
                linecolor="black",
                linewidth=1
            ),
            # Legend optimizations
            legend=dict(
                font=dict(size=legend_font_size, family=export_font_family),
                bgcolor="rgba(255, 255, 255, 0.8)",
                bordercolor="black",
                borderwidth=1
            ),
            # Background and margins for export
            plot_bgcolor="white",
            paper_bgcolor="white",
            margin=dict(l=80, r=80, t=100, b=80)  # Adequate margins for export
        )
        
        # Apply trace-level optimizations
        for trace in fig_copy.data:
            if hasattr(trace, 'line') and trace.line:
                trace.line.width = line_width
            if hasattr(trace, 'marker') and trace.marker:
                if hasattr(trace.marker, 'size'):
                    trace.marker.size = marker_size
                # Ensure markers have good contrast
                if hasattr(trace.marker, 'line'):
                    trace.marker.line = dict(width=1, color="white")
        
        return fig_copy

    def _escape_html(self, text: str) -> str:
        """
        Escape HTML special characters in a string.
        Args:
            text: Input string to escape
        Returns: Escaped string
        """
        return (text.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;"))
    