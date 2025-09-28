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
Utility functions for vibration analysis.
"""

# Required imports
import numpy as np
from dataclasses import dataclass
from typing import Iterable, List, Dict, Tuple, Optional

from scipy.signal import butter, filtfilt, find_peaks


@dataclass
class BandRMSResult:
    band: str
    f_low: float
    f_high: float
    rms: float  # in original data units (e.g. g)
    power: float  # integrated spectral density (unit^2)


def apply_highpass(y: np.ndarray, fs: float, cutoff: Optional[float]) -> np.ndarray:
    """
    Apply a 4th-order Butterworth high-pass if cutoff is valid.

    Parameters
    ----------
    y : input signal
    fs : sampling frequency (Hz)
    cutoff : cutoff frequency (Hz); if None or invalid, no filtering is applied
    Returns
    -------
    filtered signal

    """
    if cutoff is None or cutoff <= 0 or cutoff >= fs / 2:
        return y
    nyq = 0.5 * fs
    wn = cutoff / nyq
    b, a = butter(4, wn, btype="highpass")
    return filtfilt(b, a, y)


def compute_band_rms(f: np.ndarray,
                     psd: np.ndarray,
                     bands: Iterable[Tuple[float, float]],
                     unit_scale: float = 1.0) -> List[BandRMSResult]:
    """
    Integrate PSD over frequency bands.
    Parameters
    ----------
    f : frequency bins (Hz)
    psd : power spectral density values (unit^2/Hz)
    bands : iterable of (low, high)
    unit_scale : multiply RMS by this (e.g. convert g->m/s^2)

    Returns
    -------
    List[BandRMSResult]
    """
    results = []
    for (lo, hi) in bands:
        if hi <= lo:
            continue
        mask = (f >= lo) & (f <= hi)
        if not np.any(mask):
            continue
        power = np.trapz(psd[mask], f[mask])  # unit^2
        rms = np.sqrt(power) * unit_scale
        results.append(BandRMSResult(
            band=f"{lo}-{hi} Hz",
            f_low=lo,
            f_high=hi,
            rms=rms,
            power=power
        ))
    return results


def detect_psd_peaks(f: np.ndarray,
                     psd: np.ndarray,
                     prominence: float = 0.0,
                     max_peaks: int = 10) -> List[Dict]:
    """
    Basic peak detection for PSD curve.
    Returns list of dict with frequency & amplitude.

    Parameters
    ----------
    f : frequency bins (Hz)
    psd : power spectral density values (unit^2/Hz)
    prominence : required prominence of peaks
    max_peaks : maximum number of peaks to return

    Returns
    -------
    List[Dict]
    """
    if len(f) < 3:
        return []
    peaks, props = find_peaks(psd, prominence=prominence)
    peak_list = []
    for idx in peaks:
        peak_list.append({"frequency": float(f[idx]),
                          "value": float(psd[idx]),
                          "prominence": float(props.get("prominences", [np.nan])[peaks.tolist().index(idx)]
                                              if "prominences" in props else 0.0)})
    # Sort by amplitude descending
    peak_list.sort(key=lambda d: d["value"], reverse=True)
    return peak_list[:max_peaks]
