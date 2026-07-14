# Running MD on your HPC

The bundle zip CasMD produces contains:

| File | Role |
|---|---|
| `system.top`, `system.gro` | GROMACS topology + coordinates |
| `step1_minimization.mdp` | Energy-minimization config |
| `step2_nvt.mdp` | NVT equilibration |
| `step3_npt.mdp` | NPT equilibration |
| `step4_production.mdp` | Production run |
| `run_md.sh` | Re-entrant 4-step pipeline |
| `submit.sh` | SLURM submission wrapper |
| `analyze.py` | Post-MD analysis script |

## Steps

1. **scp** the zip to your HPC home directory.
2. **Unzip**: `unzip <job_name>.zip && cd <job_name>`
3. **Edit `submit.sh`** — update SLURM directives (account, partition, time)
   if your cluster differs from HKUST `gpu-l20`.
4. **Submit**: `sbatch submit.sh`
5. **Wait** — production length / GPU = approximate wall time.
6. When complete, **run analyze.py**: `python analyze.py --tpr md.tpr --xtc md.xtc -o analysis/`
7. Bring `analysis/` back to your machine and zip it for upload to Stage 2.

## Common failure modes

- **`gmx grompp` warns about missing groups** — usually safe; raise `-maxwarn`
  if needed.
- **`mdrun` segfault on first step** — typically a starting-structure issue;
  rerun energy minimization first.
- **Job killed by walltime** — extend `--time` in `submit.sh` and resubmit;
  GROMACS will pick up from the last checkpoint.
