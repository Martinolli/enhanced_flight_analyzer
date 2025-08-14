import re

def sanitize_filename(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", (name or "chart")).strip("_") or "chart"

def download_config(filename_base: str, img_format: str = "png", scale: int = 2) -> dict:
    """
    Returns a Plotly config dict that enables the built-in 'Download plot as png' button
    with a clean filename and sensible defaults. Works without Kaleido.
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