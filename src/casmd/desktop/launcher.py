"""`casmd-desktop` — the one-click launcher installed by CasMD Desktop.

Detects the GPU, activates the matching bundled GROMACS env, enables local MD
runs, starts the Streamlit app, and opens the browser.
"""
from __future__ import annotations
import argparse
import os
import platform
import socket
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

from casmd.desktop.env_select import select_gmx, probe_gmx_ok
from casmd.run.gpu_check import detect_gpu


def find_free_port(start: int = 8501, tries: int = 50) -> int:
    for port in range(start, start + tries):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
    raise RuntimeError("no free port found near %d" % start)


def build_child_env(base_env: dict, bin_dirs) -> dict:
    """Copy base_env with bin_dirs prepended to PATH and local runs enabled."""
    env = dict(base_env)
    sep = os.pathsep
    prefix = sep.join(str(p) for p in bin_dirs)
    env["PATH"] = prefix + sep + env.get("PATH", "")
    env["CASMD_LOCAL_RUN_ENABLED"] = "1"
    return env


def install_prefix() -> Path:
    """Base-env prefix == the constructor install root."""
    return Path(sys.prefix)


def app_entry() -> Path:
    """Locate the installed streamlit_app.py.

    The installer copies `app/` to <prefix>/app via constructor extra_files;
    CASMD_APP_PATH overrides (used in dev). Dev fallback: repo layout."""
    override = os.environ.get("CASMD_APP_PATH")
    if override:
        return Path(override)
    candidate = install_prefix() / "app" / "streamlit_app.py"
    if candidate.exists():
        return candidate
    import casmd
    return Path(casmd.__file__).resolve().parents[2] / "app" / "streamlit_app.py"


def wait_until_serving(port: int, timeout: float = 30.0, sleep: float = 0.5) -> bool:
    """Poll until the Streamlit port accepts connections (or timeout)."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) == 0:
                return True
        time.sleep(sleep)
    return False


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="casmd-desktop",
        description="Launch CasMD locally with GPU-aware GROMACS + local MD runs.",
    )
    p.add_argument("--port", type=int, default=None, help="localhost port")
    p.add_argument("--no-browser", action="store_true", help="don't open a browser")
    args = p.parse_args(argv)

    gpu = detect_gpu()
    sel = select_gmx(gpu_kind=gpu.kind, system=platform.system(),
                     install_prefix=install_prefix(), probe=probe_gmx_ok)
    port = args.port or find_free_port()
    env = build_child_env(os.environ, sel.bin_dirs)
    env["CASMD_GMX_ACCEL"] = sel.accel
    if sel.fell_back:
        env["CASMD_GMX_FELL_BACK"] = "1"

    cmd = [sys.executable, "-m", "streamlit", "run", str(app_entry()),
           "--server.port", str(port), "--server.headless", "true",
           "--browser.gatherUsageStats", "false"]
    print(f"CasMD Desktop — {gpu.name} → {sel.accel.upper()} GROMACS ({sel.env_name})")
    print(f"Opening http://127.0.0.1:{port} …  (close this window to quit)")
    proc = subprocess.Popen(cmd, env=env)
    if not args.no_browser and wait_until_serving(port):
        webbrowser.open(f"http://127.0.0.1:{port}/setup")
    return proc.wait()


if __name__ == "__main__":
    raise SystemExit(main())
