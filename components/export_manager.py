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

from .chart_manager import ChartManager
from .config_models import migrate_chart_dict, ChartConfig


def _sanitize_html_id(raw: str) -> str:
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
<title>Flight Data Analysis Dashboard</title>
<style>
body {{ font-family: Arial, sans-serif; margin: 20px; }}
.grid {{ display: flex; flex-wrap: wrap; gap: 20px; }}
.chart-container {{
  flex: 1 1 45%; 
  min-width: 420px;
  border:1px solid #ddd;
  padding:10px;
  border-radius:6px;
  box-shadow:0 2px 4px rgba(0,0,0,.05);
}}
h1 {{ text-align:center; }}
pre.metadata {{ background:#f7f7f7; padding:10px; border-radius:4px; }}
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
        fmt: str = "png"
    ) -> bytes:
        """
        Export charts as images zipped. Each failed chart produces an ERROR_ file in the zip.
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
                    safe_base = _sanitize_html_id(cfg_obj.title.replace(' ', '_')) or _sanitize_html_id(cfg_obj.id)
                    img_bytes = fig.to_image(format=fmt, scale=2)
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
        Returns (html_div, js_code).
        """
        fig_json = fig.to_plotly_json()
        # Minimal container
        div_html = f"<div class='chart-container'><div id='chart_{safe_id}'></div></div>"
        # Load plotly if first fallback and not already included
        loader = "https://cdn.plot.ly/plotly-latest.min.js"
        load_script = f"var ensurePlotly=window._fallbackPlotlyLoaded; if(!ensurePlotly){{var s=document.createElement('script');s.src='{loader}';s.onload=function(){{window._fallbackPlotlyLoaded=true;Plotly.newPlot('chart_{safe_id}', {json.dumps(fig_json.get('data', []))}, {json.dumps(fig_json.get('layout', {}))});}};document.head.appendChild(s);}} else {{Plotly.newPlot('chart_{safe_id}', {json.dumps(fig_json.get('data', []))}, {json.dumps(fig_json.get('layout', {}))});}}"
        js_code = load_script
        return div_html, js_code

    def _escape_html(self, text: str) -> str:
        return (text.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;"))
    