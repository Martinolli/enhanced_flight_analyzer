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
Plotly UI configuration helpers.
"""

import re

def sanitize_filename(name: str) -> str:
    """Sanitize a string to be a safe filename for Plotly downloads.
    Replaces unsafe characters with underscores and ensures it doesn't start or end with an underscore.
    Args:
        name: The desired filename (without extension).
    Returns:
        A sanitized filename string.
    """
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", (name or "chart")).strip("_") or "chart"

def download_config(filename_base: str, img_format: str = "png", scale: int = 2) -> dict:
    """
    Returns a Plotly config dict that enables the built-in 'Download plot as png' button
    with a clean filename and sensible defaults. Works without Kaleido.
    Args:
        filename_base: The base filename without extension.
        img_format: The desired image format for the download button.
        scale: The scale factor for the downloaded image.
    Returns:
        A dict suitable for passing to the `config` argument of a Plotly figure.

    """
    return dict(
        displaylogo=False,
        responsive=True,
        toImageButtonOptions=dict(
            format=img_format,  # "png", "svg", "jpeg", "webp"
            filename=sanitize_filename(filename_base),
            scale=scale
        ),
        modeBarButtonsToRemove=["lasso2d", "select2d"]  # optional cleanup
    )