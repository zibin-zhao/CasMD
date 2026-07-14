"""Package a built GROMACS system + rendered templates into a downloadable zip."""
from __future__ import annotations
import datetime as _dt
import zipfile
from pathlib import Path

from casmd.bundle.renderer import list_template_names, render
from casmd.bundle.spec import BundleSpec


_SYSTEM_FILES = ("system.top", "system.gro", "system_solvated.pdb")


def package_bundle(system_dir: Path, spec: BundleSpec, output_zip: Path) -> Path:
    """Zip a built GROMACS system + rendered MDPs + run/submit/analyze scripts.

    Top-level dir inside the zip is `<spec.job_name>/`.
    """
    system_dir = Path(system_dir)
    output_zip = Path(output_zip)
    output_zip.parent.mkdir(parents=True, exist_ok=True)

    today = _dt.date.today().isoformat()

    with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        prefix = f"{spec.job_name}/"

        # System files
        for fname in _SYSTEM_FILES:
            src = system_dir / fname
            if src.exists():
                zf.write(src, prefix + fname)

        # Rendered templates
        for tname in list_template_names():
            text = render(tname, spec, extra={"generated_date": today})
            zf.writestr(prefix + tname, text)

    return output_zip
