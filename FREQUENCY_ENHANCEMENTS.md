# Advanced Frequency Analysis Options

| Option | Description |
|--------|-------------|
| Override fs | Forces sample rate if timestamps have been quantized. |
| Max Freq | Limits display to given frequency (zoom). |
| Welch nperseg | Segment length for PSD (power of two recommended). |
| Overlap % | Segment overlap percentage for Welch. |
| High-pass (Hz) | 4th-order Butterworth HP filter before spectral computation. |
| Band RMS | Semicolon-separated frequency bands (lo-hi) for PSD RMS integration. |
| Peak Annotation | Marks dominant peak (first trace only). |
| Log Scale Y | Logarithmic y-axis for amplitude/PSD. |

Subtitle diagnostics now show: fs, N, Nyquist, Δf (bin spacing), nperseg, overlap, and applied filters.
