"""`casmd-ui` — launch the Streamlit web app."""
from __future__ import annotations
import argparse
import os
import subprocess
import sys
from pathlib import Path


def _ensure_streamlit_credentials() -> None:
    """Write a blank credentials file so Streamlit skips the email prompt."""
    creds = Path.home() / ".streamlit" / "credentials.toml"
    if not creds.exists():
        creds.parent.mkdir(parents=True, exist_ok=True)
        creds.write_text('[general]\nemail = ""\n')


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="casmd-ui", description="Launch the CasMD Streamlit app.")
    p.add_argument("--port", type=int, default=8501)
    p.add_argument("--host", default="127.0.0.1")
    args = p.parse_args(argv)

    here = Path(__file__).resolve()
    repo_root = here.parent.parent.parent  # src/casmd/cli.py → repo root
    app_entry = repo_root / "app" / "streamlit_app.py"
    if not app_entry.exists():
        print(f"error: app/streamlit_app.py not found at {app_entry}", file=sys.stderr)
        print("CasMD's UI requires running from a dev install (`pip install -e .`).", file=sys.stderr)
        return 2

    _ensure_streamlit_credentials()

    cmd = [
        sys.executable, "-m", "streamlit", "run", str(app_entry),
        "--server.port", str(args.port),
        "--server.address", args.host,
        "--browser.gatherUsageStats", "false",
    ]
    # Put the repo root on PYTHONPATH so `from app.shared import ...` works
    # when Streamlit runs `app/streamlit_app.py` (which doesn't put the repo
    # root on sys.path automatically).
    env = os.environ.copy()
    existing_pp = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = (
        f"{repo_root}{os.pathsep}{existing_pp}" if existing_pp else str(repo_root)
    )

    # Ensure the Python interpreter's bin/ directory is on PATH so the build
    # subprocesses (pdb4amber, tleap, gmx) are findable even when the user
    # invokes `casmd-ui` from a shell without conda activated. `sys.executable`
    # points at e.g. /opt/miniconda3/envs/foo/bin/python3.11 — its parent
    # holds the AmberTools + GROMACS binaries installed alongside it.
    python_bin_dir = str(Path(sys.executable).resolve().parent)
    existing_path = env.get("PATH", "")
    if python_bin_dir not in existing_path.split(os.pathsep):
        env["PATH"] = (
            f"{python_bin_dir}{os.pathsep}{existing_path}"
            if existing_path
            else python_bin_dir
        )
    print(f"Launching: {' '.join(cmd)}")
    return subprocess.call(cmd, env=env)


if __name__ == "__main__":
    raise SystemExit(main())
