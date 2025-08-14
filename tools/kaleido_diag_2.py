import os, sys, glob, subprocess, struct, platform, textwrap, time

def main():
    print("=== Environment ===")
    print(sys.version)
    print("bitness:", struct.calcsize("P")*8)
    print("platform:", platform.platform())
    try:
        import kaleido
        pkg_dir = os.path.dirname(kaleido.__file__)
        print("kaleido package dir:", pkg_dir)
    except Exception as e:
        print("Import error:", e)
        return 1

    exe_pattern = os.path.join(pkg_dir, "executable", "*.exe")
    candidates = glob.glob(exe_pattern)
    print("exe candidates:", candidates)
    if not candidates:
        print("No kaleido executable found in package.")
        return 2

    exe = candidates[0]
    print(f"Trying CLI: {exe} --help (10s timeout)")
    try:
        p = subprocess.run([exe, "--help"], capture_output=True, text=True, timeout=10)
        print("Return code:", p.returncode)
        print("Stdout (first 200):", (p.stdout or "")[:200])
        print("Stderr (first 200):", (p.stderr or "")[:200])
        if p.returncode == 0:
            print("CLI OK")
        else:
            print("CLI returned non-zero")
    except subprocess.TimeoutExpired:
        print("CLI TIMEOUT (likely blocked by Windows/AV)")
        return 3
    except Exception as e:
        print("CLI error:", repr(e))
        return 4

    print("\nProgrammatic test (15s timeout) via plotly.io.to_image ...")
    from multiprocessing import Process, Queue
    def worker(q):
        try:
            import plotly.graph_objects as go
            from plotly.io import to_image
            fig = go.Figure(data=[go.Scatter(x=list(range(1000)), y=[(i*i)%97 for i in range(1000)])])
            png = to_image(fig, format="png", scale=2, engine="kaleido")
            q.put(("ok", len(png)))
        except Exception as e:
            q.put(("err", repr(e)))
    q = Queue()
    proc = Process(target=worker, args=(q,))
    proc.start()
    proc.join(timeout=15)
    if proc.is_alive():
        print("Result: TIMEOUT — still blocked.")
        proc.terminate()
        proc.join(3)
        return 5
    else:
        try:
            status, info = q.get_nowait()
            print("Result:", status, info)
        except Exception:
            print("No result.")
            return 6

    return 0

if __name__ == "__main__":
    sys.exit(main())