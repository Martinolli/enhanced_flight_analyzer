# CHANGELOG

All notable changes will be documented in this file.  
Format loosely follows [Keep a Changelog](https://keepachangelog.com/) and Semantic Versioning.

## [Unreleased]

- Dual Y-axis plotting
- Derived parameter engine
- Anomaly detection overlay
- Dashboard save/load
- Plugin system skeleton

## [2.2.1] - 2025-01-15

### Added

- **Export-safe styling** with professional formatting for high-DPI and vector outputs
- **Multi-format image export** (PNG, SVG, PDF, JPEG) with configurable scaling
- **Vector format support** (SVG, PDF) for presentations and publications
- **Enhanced HTML export** with print/PDF-optimized CSS and responsive grid layout
- **High-DPI scaling** support (2x, 3x, 4x) for retina displays and professional printing
- Export-optimized chart styling with consistent fonts, colors, and layouts

### Changed

- Updated export workflow to apply format-specific styling optimizations
- Enhanced HTML dashboard with professional CSS Grid layout and print media queries
- Improved chart default styling for better export compatibility
- Enhanced documentation with comprehensive export workflow guidance

### Fixed

- Export compatibility across different output formats and display densities
- Professional appearance consistency in exported materials

## [2.2.0] - 2025-08-12

### Added

- Arbitrary X-axis selection (any numeric parameter)
- Sorting option for non-time X to preserve line continuity
- Hardened HTML export (two-path system: standard + JSON fallback)
- Detailed export notes & optional debug dump
- Batch PNG ZIP export with per-chart error logging
- Correlation matrix caching for performance
- Quick-start templates now use new `ChartConfig` schema
- Extensive README refresh
- License: Apache-2.0 (adds explicit patent grant).

### Changed

- Unified chart generation flow via `ChartManager` with migration abstraction
- Layout rendering delegated fully to `LayoutManager`
- Improved user messaging for frequency charts & non-monotonic X handling
- Metrics calculation now excludes only recognized non-parameter columns (`Elapsed Time (s)`, `Timestamp`)

### Fixed

- Eliminated intermittent "unhashable type: 'dict'" export exceptions via fallback embedding
- Prevented silent skipping of charts by surfacing explicit export notes

## [2.1.0] - 2025-08-10

### Added 2.1.0

- Initial migration to structured `ChartConfig` dataclass
- Frequency chart mode (FFT / PSD option)
- Basic HTML export (pre-hardened)
- Quick-start chart templates (Control Surfaces, Angles, Forces)

### Changed 2.1.0

- Refactored chart creation to support future multi-axis
- Standardized color schemes and legend formatting

## [2.0.0] - 2025-08-05

### Added 2.0.0

- Multi-chart dashboard (line, scatter, bar, area)
- Data quality summary (missing values, basic ranges)
- Statistical summary (describe)
- Correlation matrix (initial version)
- Session-based chart configuration
- Base Export Manager implementation

### Notes

- This was the foundational release establishing modular components.

## [1.0.0] - 2025-07-25

### Added 1.0.0

- Prototype single-page analyzer
- Basic CSV ingestion & elapsed time calculation
- Simple line plotting
- Minimal documentation (superseded)

---

## Versioning Policy

- Increment PATCH (x.y.Z) for bug fixes / internal improvements
- Increment MINOR (x.Y.z) for backward-compatible feature additions
- Increment MAJOR (X.y.z) only upon intentional breaking API or schema changes

---

## Migration Summary

| Change | Introduced | Impact |
|--------|------------|--------|
| ChartConfig schema | 2.1.0 | Legacy configs auto-migrated each run |
| Hardened export fallback | 2.2.0 | Prevents export failure; adds notes |
| Arbitrary X-axis | 2.2.0 | Backward compatible; existing time-based charts unchanged |

---

## Upgrade Guidance

From ≤ 2.0.0 → 2.2.0:

- No manual action; chart dicts auto-migrate.
- (Optional) Remove obsolete “parameters/x_axis/type” reliance in any custom scripts and adopt new schema keys if you integrate programmatically.

---

## Planned (Short-Term) Milestones

| Target | Focus |
|--------|-------|
| 2.3.0 | Dual Y-axis + anomaly detection |
| 2.4.0 | Derived expressions + dashboard persistence |
| 2.5.0 | Enhanced HTML/PDF reporting |

---

Contributions & feedback welcome. Open an issue for proposals before large features.
