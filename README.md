# ✈️ Enhanced Flight Data Analyzer Pro

Advanced, modular, Streamlit-based platform for exploratory and comparative analysis of flight test data.  
Create multi-chart dashboards, correlate control inputs with aerodynamic response, perform frequency (FFT / PSD) investigations, inspect data quality, and export professional artifacts (HTML dashboard & batch chart images).

Status: v2.2.0 (Foundational feature set complete – next phase will add dual Y‑axes, derived parameters, anomaly detection, richer reports.)

---

## 🔑 Key Capabilities

### Interactive Visualization

- Multiple chart types: Line, Scatter, Bar, Area, Frequency (FFT / PSD)
- Arbitrary X–Axis selection: Plot any numeric parameter vs any other (e.g., Stick Position vs Stick Force)
- Optional X sorting for non-time axes to retain line plots
- Automatic fallback to scatter for non-monotonic unsorted X in line mode (prevents misleading zig-zag lines)
- Color palette selection (9 professional sequential schemes)
- Quick-start chart templates (Control Surfaces, Angles, Forces)
- Configurable multi-layout dashboard: 1x1, 1x2, 2x2, 3x2, 2x3, Vertical Stack

### Analytical Tools

- Correlation matrix (cached for performance) excluding time columns
- Statistical summaries (describe)
- Data quality report:
  - Missing value overview
  - Basic range statistics (min, max, mean, std)
- Frequency analysis (FFT / Welch PSD) over time-based sampling

### Export & Reporting

- HTML dashboard export (interactive, all charts, metadata, notes)
- Robust fallback export strategy (avoids Plotly serialization edge cases)
- Batch PNG image export (ZIP) (requires `kaleido`)
- Skipped/failed charts logged in Export Notes (HTML)
- Deterministic export ordering

### Architecture & Extensibility

- Modular components:
  - `ChartManager`: Unified chart generation & X-axis logic
  - `DataProcessor`: Data ingestion & preprocessing (legacy compatibility)
  - `LayoutManager`: Grid layout orchestration
  - `ExportManager`: Hardened export flows
  - `config_models`: Strongly-typed chart configuration (dataclass)
- Idempotent migration for legacy chart configs → new schema
- Clean session state management
- Caching layer for correlation matrix
- Ready for future plugin & derived parameter systems

---

## 🗂 Directory Structure (Conceptual)

```bash
enhanced_flight_analyzer/
├── app.py
├── components/
│   ├── chart_manager.py
│   ├── data_processor.py
│   ├── layout_manager.py
│   ├── export_manager.py
│   ├── config_models.py
├── tests/
│   └── test_chart_manager_custom_x.py
├── requirements.txt
├── README.md
└── CHANGELOG.md
```

---

## 🧪 Data Format Requirements

The analyzer expects CSVs with two header rows:

Row 1: Parameter names / descriptions  
Row 2: Units (e.g., `EU`, `deg`, `N`, etc.)

First data column: Timestamps in format  
`day:hour:minute:second.millisecond` (e.g., `198:09:40:00.100`)

Example:

```bash
Description,ANGLE OF ATTACK - ALPHA (AOA),ELEVATOR DEFLECTION
EU,deg,deg
198:09:40:00.000,30.73,-19.52
198:09:40:00.100,30.73,-19.19
```

The app auto-derives "Elapsed Time (s)" if possible.

---

## 🚀 Getting Started

### 1. Install Dependencies

```bash
python -m venv venv
source venv/bin/activate  # (Windows: venv\Scripts\activate)
pip install -r requirements.txt
# Optional (for PNG export):
pip install kaleido
```

### 2. Run the App

```bash
streamlit run app.py
```

### 3. Upload Data

- Use the sidebar “Upload Flight Data File”
- Once processed, available parameters populate chart builders

### 4. Build Charts

1. Click “➕ Add New Chart”
2. Select:
   - Chart Type (line / scatter / bar / area / frequency)
   - X Parameter (any numeric column or time)
   - Y Parameters
   - Color palette
   - (Frequency mode: choose FFT or PSD)
3. (Optional) If non-time X is not monotonic and you want a line: enable “Sort X …” checkbox

### 5. Export

- “Export HTML Dashboard” → full interactive single file
- “Export Charts as PNG Zip” → batch image export (needs kaleido)

---

## 🧭 Feature Behavior Notes

| Feature | Behavior |
|---------|----------|
| Arbitrary X-axis | Any numeric column; time-based features keep working |
| Line fallback | Non-monotonic X without sorting → scatter |
| Sorting toggle | Preserves intended line continuity for scrambled X |
| Frequency charts | Always computed vs time sampling (Elapsed Time / Timestamp) |
| Export notes | Lists skipped charts and fallback actions |
| Correlation | Excludes "Elapsed Time (s)" to avoid trivial structure |

---

## 🧱 Technical Highlights

- Dataclass: `ChartConfig` (fields: id, chart_type, x_param, y_params, color_scheme, freq_type, sort_x, etc.)
- Migration executes on each run (safe idempotent)
- Frequency analysis pathways:
  - FFT (raw amplitude spectrum)
  - PSD (Welch method, adaptive segment length)
- Hardened export:
  - Primary path: `plotly.io.to_html`
  - Fallback path: JSON + `Plotly.newPlot(...)` if serialization fails

---

## 🛠 Troubleshooting

| Issue | Cause | Resolution |
|-------|-------|-----------|
| Chart not appearing | Empty Y selection or invalid column | Re-open chart config and reselect parameters |
| Line changed to scatter | X not monotonic & sorting disabled | Enable “Sort X” or accept scatter |
| HTML layout “deformed” | External CSS constraints or container width constraints | Future iteration: dedicated flexbox / grid responsive stylesheet |
| Missing PNG | `kaleido` not installed | `pip install kaleido` |

---

## 🧪 Testing

Example test included:

- `test_chart_manager_custom_x.py` validates custom X fallback logic

Recommended future tests:

- Frequency ignores custom non-time X
- Export fallback usage
- Migration idempotence
- Sorting toggle correctness

Run tests:

```bash
pytest -q
```

---

## 🧭 Roadmap (Planned Enhancements)

Short Term (v2.3.x):

- Dual Y-axis (secondary axis assignments)
- Derived parameters (expression builder with safe sandbox)
- Anomaly / outlier detection (z-score & IQR flagging)
- Improved HTML report theming & layout grid stabilization

Mid Term (v2.4.x – v2.5.x):

- Dashboard save/load (JSON configs download & import)
- Multi-axis + shading by flight phase (climb/cruise/descend detection)
- Template library expansion
- Performance: streaming / downsampled WebGL traces

Long Term:

- Plugin architecture (custom analysis modules)
- ML-based trend detection
- 3D trajectory (Lat/Lon/Altitude) visualization
- Automated PDF report (WeasyPrint / headless browser)

---

## 🤝 Contributing (Lightweight Initial Guidance)

1. Fork & branch (`feature/<short-description>`)
2. Keep PRs focused (≤ ~400 lines diff)
3. Add/update tests for new logic
4. Update CHANGELOG increment patch/minor version
5. Use semantic commit style:
   - `feat:`, `fix:`, `perf:`, `docs:`, `refactor:`, `test:`

---

## 📄 License

(Choose one if not yet defined – e.g., MIT. Add a LICENSE file.)

---

## 🙏 Acknowledgements

- Plotly for interactive visualization
- Streamlit for rapid UI development
- SciPy (FFT / Welch PSD)
- Community contributions (future)

---

## 📌 Version

Current: v2.2.0  
See CHANGELOG for detailed history.

---

## 🧩 Future HTML Layout Improvement

Current HTML export relies on a simple flex container for grid distribution; charts may “stretch” unevenly on very narrow screens. Planned improvements:

- CSS Grid with minmax column sizing
- Per-chart width declarations
- Optional print stylesheet for PDF-friendly formatting

---

If you have suggestions or need a feature prioritized, open an issue or start a discussion.  
Happy analyzing! ✨

## License

This project is licensed under the Apache License 2.0 – see the [LICENSE.md](LICENSE.md) file for details.

If you redistribute a modified version, keep:

- LICENSE (unchanged text)
- NOTICE (if present), adding a note of your modifications

External dependencies retain their respective licenses.
