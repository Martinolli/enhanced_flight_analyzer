import os
import sys
import streamlit

# Import key modules so PyInstaller includes them in the bundle
# These imports ensure dependencies used by the Streamlit app are collected.

try:
    import components.chart_manager  # noqa: F401
    import components.data_processor  # noqa: F401
    import components.layout_manager  # noqa: F401
    import components.export_manager  # noqa: F401
    import components.statistical_analysis  # noqa: F401
    import components.large_dataset_handler  # noqa: F401
    import components.config_models  # noqa: F401
    import components.plotly_ui  # noqa: F401
    import components.export_html_zip  # noqa: F401
except Exception:
    # If imports fail in source mode, it's fine — Streamlit will import from app.py
    pass


def resource_path(rel_path: str) -> str:
    """Resolve a path that works in both source and PyInstaller onefile modes."""
    if hasattr(sys, "_MEIPASS"):
        # Running from a PyInstaller bundle
        base = sys._MEIPASS  # type: ignore[attr-defined]
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, rel_path)


def main() -> int:
    # Use Streamlit's CLI programmatically to run the app
    try:
        from streamlit import cli as stcli  # Try older location first for compatibility
    except ImportError:
        from streamlit.web import cli as stcli  # Use newer location if available

    app_path = resource_path("app.py")

    # Default args; you can add flags here (e.g., port) if desired
    sys.argv = [
        "streamlit",
        "run",
        app_path,
        "--server.headless=true",
    ]
    return stcli.main()


if __name__ == "__main__":
    sys.exit(main())

