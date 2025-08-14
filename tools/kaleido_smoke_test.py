import plotly.graph_objects as go
from plotly.io import to_image
import sys

def main():
    print("Plotly/Kaleido smoke test starting...")
    fig = go.Figure(data=[go.Scatter(x=list(range(1000)), y=[i*i % 97 for i in range(1000)])])
    try:
        png = to_image(fig, format="png", scale=2, engine="kaleido")
        print(f"Rendered {len(png)} bytes OK")
        return 0
    except Exception as e:
        print("Kaleido render failed:", e)
        return 1

if __name__ == "__main__":
    sys.exit(main())