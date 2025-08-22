import numpy as np
import pandas as pd
from components.chart_manager import ChartManager
from components.config_models import ChartConfig

def synth_sine(fs=50.0, f0=5.0, seconds=4.0, noise=0.0):
    t = np.arange(0, seconds, 1/fs)
    y = np.sin(2*np.pi*f0*t) + noise * np.random.randn(len(t))
    return t, y

def test_fft_peak_detection():
    t, y = synth_sine()
    df = pd.DataFrame({"Elapsed Time (s)": t, "Signal (unit)": y})
    cm = ChartManager()
    cfg = ChartConfig(
        id="freq",
        title="FFT Test",
        chart_type="frequency",
        y_params=["Signal (unit)"],
        freq_type="fft",
        freq_detrend=True,
        freq_window="hann",
        freq_peak_annotation=True
    )
    fig = cm.create_chart(df, cfg)
    assert fig is not None
    # Find annotated peak text
    texts = [a.text for a in fig.layout.annotations] if fig.layout.annotations else []
    assert any("Peak" in t for t in texts), "Expected peak annotation"

def test_psd_generation():
    t, y = synth_sine()
    df = pd.DataFrame({"Elapsed Time (s)": t, "Signal (unit)": y})
    cm = ChartManager()
    cfg = ChartConfig(
        id="psd",
        title="PSD Test",
        chart_type="frequency",
        y_params=["Signal (unit)"],
        freq_type="psd",
        freq_window="hamming",
        freq_detrend=True
    )
    fig = cm.create_chart(df, cfg)
    assert fig is not None
    assert len(fig.data) == 1
    assert "PSD" in fig.data[0].name