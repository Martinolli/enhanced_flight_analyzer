import os, sys, struct, platform, subprocess, textwrap, time
from multiprocessing import Process, Queue

def render_worker(q: Queue):
    try:
        import plotly.graph_objects as go
        from plotly.io import to_image
        fig = go.Figure(data=[go.Scatter(x=list(range(1000)), y=[(i*i) % 97 for i in range(1000)])])
        png = to_image(fig, format="png", scale=2, engine="kaleido")
        q.put(("ok", len(png)))
    except Exception as e:
        q.put(("err", repr(e)))

def main():
    print("=== Environment ===")
    print(sys.version)
    print("bitness:", struct.calcsize("P")*8)
    print("platform:", platform.platform())
    print("TMP:", os.environ.get("TMP"))
    print("TEMP:", os.environ.get("TEMP"))

    try:
        import plotly, kaleido
        print("plotly:", plotly.__version__)
        print("kaleido:", getattr(kaleido, "__version__", "unknown"))
    except Exception as e:
        print("Import error:", e)
        return 1

    print("\n=== Kaleido CLI check ===")
    # Try to find kaleido.exe in venv Scripts
    exe_candidates = []
    scripts_dir = os.path.join(sys.prefix, "Scripts")
    exe_candidates.append(os.path.join(scripts_dir, "kaleido.exe"))
    exe_candidates.append("kaleido")  # fallback to PATH
    for exe in exe_candidates:
        try:
            print(f"Trying: {exe}")
            p = subprocess.run([exe, "--help"], capture_output=True, text=True, timeout=10)
            print("Return code:", p.returncode)
            print("Stdout (first 200 chars):", (p.stdout or "")[:200])
            print("Stderr (first 200 chars):", (p.stderr or "")[:200])
            if p.returncode == 0:
                print("CLI OK")
                break
        except subprocess.TimeoutExpired:
            print("Timeout running kaleido CLI (10s).")
        except FileNotFoundError:
            print("Not found:", exe)
        except Exception as e:
            print("CLI error:", e)

    print("\n=== Programmatic render (15s timeout) ===")
    q = Queue()
    proc = Process(target=render_worker, args=(q,))
    proc.start()
    proc.join(timeout=15)
    if proc.is_alive():
        print("Result: TIMEOUT — Kaleido render did not finish in 15s.")
        proc.terminate()
        proc.join(3)
        return 2
    else:
        try:
            status, info = q.get_nowait()
        except Exception:
            print("No result from worker.")
            return 3
        if status == "ok":
            print(f"Result: OK — rendered {info} bytes.")
            return 0
        else:
            print("Result: ERROR —", info)
            return 4

if __name__ == "__main__":
    sys.exit(main())