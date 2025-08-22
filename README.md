# ✈️ Enhanced Flight Data Analyzer Pro

Version: v2.3.0-dev (Dual Y-axis + enhanced frequency analysis introduced)

... (retain prior sections up to Key Capabilities, then update/additions below) ...

## 🔑 Key Capabilities (Highlights Added in v2.3.0-dev)

- Dual Y-axis plotting with:
  - Automatic unit detection & grouping
  - Optional manual overrides
  - Forced axis splitting
  - Scale synchronization (compatible units)
  - Legend unit styling (parentheses / bracket / suffix)
- Enhanced frequency domain tools:
  - FFT & Welch PSD
  - Detrend option
  - Multiple windows: Hann, Hamming, Blackman, Rectangular
  - Log scale toggle
  - Peak annotation
  - Irregular sampling detection (coefficient of variation warning)
- Improved UI for secondary axis parameter selection

(Add a new section “Dual Axis & Units”)

## 🎯 Dual Axis & Unit Detection

| Feature | Behavior |
|---------|----------|
| Auto Detect Units | Parses units in parentheses or trailing tokens |
| Axis Assignment | Dominant unit group → primary axis, others → secondary |
| Forced Split | Enable “Force Dual-Axis Split” to separate a homogeneous unit group |
| Manual Override | Disable auto detection to specify primary / secondary units directly |
| Sync Scales | When units are compatible, align min/max ranges |
| Legend Formatting | Toggle units, select annotation style |

Usage:

1. Configure a chart (non-frequency).
2. Toggle “Enable Secondary Y Axis” to manually pick secondary parameters OR rely on auto detection by mixing distinct units.
3. Adjust unit display & sync options as needed.

## 🔊 Frequency Analysis Enhancements

| Option | Effect |
|--------|--------|
| Detrend | Removes linear trend / mean before spectral calc |
| Window | Applies selected window (energy-corrected amplitude) |
| Log Scale | Logarithmic Y axis (useful for PSD) |
| Peak Annotation | Marks dominant non-DC frequency |
| Irregular Sampling Warning | Displays if timestamp interval CV > threshold |

...

## 📄 License

Licensed under the Apache License 2.0 – see LICENSE.
