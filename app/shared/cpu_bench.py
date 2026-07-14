"""Stage-1 'Measure this hardware's speed' benchmark panel (guardrailed).

Runs a short GROMACS minimization on the built system to report a *measured*
ns/day, refining the size-agnostic estimate. Guardrails for the shared public
Space:
- shown only when GROMACS is on PATH;
- **one attempt per session** (consumed on success *or* failure, so a bundle
  that reliably fails/times out can't be re-triggered to pin the shared CPUs);
- the benchmark leaves a core free for the web process and shares a single
  wall-clock budget (see casmd.run.benchmark);
- the extracted bundle is always cleaned up (no ephemeral-disk leak);
- an explicit note that it briefly loads the shared app.

The measured number is a conservative rough lower bound (a short EM run carries
fixed setup cost), which is fine for its purpose: telling the user a real run
is slow here.
"""
from __future__ import annotations
from pathlib import Path

_SESSION_KEY = "_cpu_bench_result"


def render_cpu_benchmark(*, out_zip: Path, production_ns: float) -> None:
    """Render the benchmark button / result below the run-time estimate."""
    import streamlit as st

    from casmd.run.benchmark import gmx_available
    from casmd.run.gpu_check import format_eta

    if not gmx_available():
        return  # no GROMACS here (e.g. a dev box without gmx) — estimate only

    existing = st.session_state.get(_SESSION_KEY)
    if existing is not None:
        if existing.get("failed"):
            st.info(
                "Couldn't benchmark this system quickly here — the estimate "
                f"above applies. ({existing['failed']})"
            )
            return
        hours = production_ns * 24 / max(existing["ns_per_day"], 0.01)
        st.success(
            f"📏 **Measured (rough lower bound):** ~{existing['ns_per_day']:g} ns/day "
            f"for your {existing['n_atoms']:,}-atom system "
            f"({existing['steps']} min steps in {existing['wall']:.0f}s) → "
            f"{production_ns:g} ns ≈ **{format_eta(hours)}**."
        )
        return

    st.caption(
        "Want a measured number instead of an estimate? Run a short minimization "
        "to gauge this hardware's real speed (leaves a core free for the app). "
        "**Note:** this runs real GROMACS on the shared Space and may briefly "
        "slow it for others — **one attempt per session**."
    )
    if not st.button("▶ Measure this hardware's speed (~30–60s)",
                     key="cpu_bench_btn", use_container_width=True):
        return

    import shutil
    import tempfile
    import zipfile

    from casmd.run.benchmark import run_cpu_benchmark

    bench_root = Path(tempfile.mkdtemp(prefix="casmd_bench_"))
    with st.status("Running a short minimization to measure speed…",
                   expanded=True) as status:
        try:
            with zipfile.ZipFile(out_zip) as zf:
                zf.extractall(bench_root)
            bench_dir = bench_root
            kids = [p for p in bench_root.iterdir() if p.is_dir()]
            if len(kids) == 1:
                bench_dir = kids[0]
            res = run_cpu_benchmark(bench_dir)
            st.session_state[_SESSION_KEY] = {
                "ns_per_day": res.ns_per_day, "n_atoms": res.n_atoms,
                "steps": res.steps, "wall": res.wall_seconds,
            }
            status.update(label="✓ Benchmark complete", state="complete",
                          expanded=False)
        except Exception as exc:
            # Consume the one-per-session allowance even on failure so a failing
            # bundle can't be re-triggered to keep pinning the shared CPUs.
            st.session_state[_SESSION_KEY] = {"failed": str(exc)}
            status.update(label="✗ Benchmark unavailable", state="error",
                          expanded=True)
        finally:
            shutil.rmtree(bench_root, ignore_errors=True)
    st.rerun()
