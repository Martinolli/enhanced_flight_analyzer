import io, zipfile
from typing import Dict, Any
import pandas as pd
import plotly.io as pio

def export_charts_as_html_zip(charts: Dict[str, Dict[str, Any]], df: pd.DataFrame, chart_manager) -> bytes:
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