"""Convert AMBER prmtop/inpcrd to GROMACS top/gro via parmed."""
from __future__ import annotations
import re
from pathlib import Path

import parmed as pmd


def _patch_cmap_format(top_path: Path, values_per_line: int = 10) -> None:
    """Rewrite parmed's CMAP section to be GROMACS-2024-compatible.

    parmed 4.x writes CMAP tables with backslash-continuation lines where
    each line holds 10 high-precision floats (15+ decimals). The long lines
    (up to ~200 chars) overflow gmx grompp 2024.3's 4095-char line buffer,
    causing a SIGABRT crash.

    Fix: re-emit each CMAP entry using the same backslash-continuation
    format as GROMACS's own charmm27.ff/cmap.itp — 10 values per line at
    8 decimal places (max ~130 chars/line, safely under the 4095 limit).
    """
    text = top_path.read_text()
    m = re.search(r"\[\s*cmaptypes\s*\]", text)
    if not m:
        return  # no CMAP, nothing to do
    start = m.end()
    end_m = re.search(r"\n\[\s*\w+\s*\]", text[start:])
    end = start + end_m.start() if end_m else len(text)
    cmap_section = text[start:end]

    # Step 1: join backslash-continuation lines into one flat token stream
    joined = re.sub(r"\\\n\s*", " ", cmap_section)

    # Step 2: reformat each CMAP entry with 8-decimal-place floats and
    # backslash-continuation lines of values_per_line values each.
    out_lines: list[str] = []
    for line in joined.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith(";"):
            out_lines.append(line)
            continue
        tokens = stripped.split()
        # Detect a CMAP entry: 5 atom-types + functype + nrow + ncol + values
        try:
            nrow = int(tokens[6])
            ncol = int(tokens[7])
        except (IndexError, ValueError):
            out_lines.append(line)
            continue
        n_vals = nrow * ncol
        floats_raw = tokens[8:]
        if len(floats_raw) != n_vals:
            # Unexpected token count — emit unchanged to avoid data corruption
            out_lines.append(line)
            continue
        # Header line with trailing backslash (matches GROMACS cmap.itp style)
        header = " ".join(tokens[:8])
        floats_8dp = [f"{float(v):.8f}" for v in floats_raw]
        chunks = [
            floats_8dp[i : i + values_per_line]
            for i in range(0, n_vals, values_per_line)
        ]
        out_lines.append(header + "\\")
        for chunk in chunks[:-1]:
            out_lines.append(" ".join(chunk) + "\\")
        out_lines.append(" ".join(chunks[-1]))

    cleaned = "\n".join(out_lines) + "\n"
    top_path.write_text(text[:start] + cleaned + text[end:])


def amber_to_gromacs(
    prmtop: Path,
    inpcrd: Path,
    output_dir: Path,
    *,
    prefix: str = "system",
) -> tuple[Path, Path]:
    """Read AMBER prmtop+inpcrd, write GROMACS top+gro. Return (top, gro)."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    structure = pmd.load_file(str(prmtop), xyz=str(inpcrd))

    top_path = output_dir / f"{prefix}.top"
    gro_path = output_dir / f"{prefix}.gro"

    structure.save(str(top_path), overwrite=True)
    structure.save(str(gro_path), overwrite=True)

    _patch_cmap_format(top_path)

    return top_path, gro_path
