# Provenance of the published results

What was actually run, taken from the ten CRC solver logs
(`run_sc_model.o*` in the private repository) rather than restated from the
manuscript. Where the two disagree, the logs are authoritative and the difference
is noted.

## Software versions — three are on record, and the paper names none of them

| source | Gurobi | Pyomo |
|---|---|---|
| manuscript, Data availability | 10.0.3 | 6.6.1 |
| private CRC job script (`module load`) | 11.0.2 | — |
| **CRC solver logs (what ran)** | **12.0.2** | — |
| reproduction on macOS/arm64, 2026-07-29 | 10.0.1 | 6.6.1 |

The logs report:

```
Gurobi Optimizer version 12.0.2 build v12.0.2rc0 (linux64 - "Red Hat Enterprise Linux 9.7 (Plow)")
```

The job script loads `gurobi/11.0.2`, so the module and the runtime disagree even
within the private repo. **A reader following the paper would install 10.0.3, which
is not what produced the results.** `environment.yml` in this repository pins
Pyomo 6.6.1 and leaves Gurobi to the system install, because Pyomo's
`SolverFactory('gurobi')` is the LP-file shell interface and needs `gurobi.sh` on
`PATH` (see [REPRODUCE.md](REPRODUCE.md)).

## Model size

The manuscript reports 124,711 continuous / 3,784 binary / 5,949 equality / 9,246
inequality in three places (`main_jcp.tex` lines 485, 498, 512). **Those numbers
match no code in either repository.** The logs report, consistently across every
solve:

```
Optimize a model with 15597 rows, 150826 columns and 443436 nonzeros
Variable types: 147507 continuous, 3319 integer (3319 binary)
```

`model_statistics.py` in this repository reproduces all of that exactly:

| quantity | this code | CRC log | manuscript |
|---|---|---|---|
| continuous variables | **147,507** | 147,507 | 124,711 |
| binary variables | **3,319** | 3,319 | 3,784 |
| equality constraints | **6,727** | (no split given) | 5,949 |
| inequality constraints | **8,870** | (no split given) | 9,246 |
| rows | **15,597** | 15,597 | 15,195 |

Three counts legitimately differ and all three are correct answers to different
questions: 149,102 continuous as declared, 148,767 after the run scripts fix
`m.z`/`m.y_ref`/`m.s`, and 147,507 as Pyomo's LP writer emits — the last dropping
1,260 variables that appear in no active constraint and not in the objective
(`v` 464, `x` 335, `vol_eth_sold`'s diagonal 335, `x_ref` 126).

Cases 2 and 4 fix `m.y` instead of `m.y_ref` and so carry 2,993 binaries.

## MIP gap, per study

Set in each run script, not uniform as the manuscript's single "0.003%" implies:

| study | script | MIPGap |
|---|---|---|
| Cases 1–4, blends 0–50% | `run_blend_and_opt_sensitivity.py` | 3e-5 (0.003%) |
| Integer cuts, Cases 1 and 3 | `run_integer_cuts.py` | 3e-5 (0.003%) |
| Mill-specific incentives | `run_mill_specific_incentives.py` | 3e-4 (0.03%) |
| Case 5 and the tornado scenarios | `run_unconstrained_SAF_prem_sensitivity.py`, `run_tornado_sensitivity.py` | 5e-4 (0.05%) |

## Solve time — the "~20 minutes per instance" claim is wrong both ways

The manuscript states "Each model instance was solved in approximately 20
minutes." Measured from the logs (each is a 41-premium Case 5 sweep):

| log | solves | total solver time | worst single solve | median solve |
|---|---|---|---|---|
| o1002444 | 41 | **85.6 h** | **7.69 h** | 4.2 s |
| o1060285 | 41 | 0.60 h | 3 min | 4.2 s |
| o1061601 | 41 | 0.09 h | 2 min | 1.5 s |
| o1062076 | 41 | 0.76 h | 11 min | 45.5 s |
| o1062861 | 41 | 0.13 h | 1 min | 1.5 s |
| o1063072 | 41 | 0.44 h | 2 min | 46.9 s |
| o1063636 | 41 | 0.91 h | 3 min | 110.0 s |
| o1099149 | 41 | 0.03 h | 1 min | 1.4 s |
| o1099157 | 41 | 0.26 h | 1 min | 1.6 s |
| o1099272 | 41 | 0.22 h | 1 min | 1.6 s |
| **total** | **410** | **89.0 h** | | |

Median solve time is **1.4 to 110 seconds**, far below 20 minutes; the worst single
solve is **7.7 hours**, far above it. The distribution is extremely skewed —
premiums below the ~2.6 R$/L threshold solve almost instantly because no SAF is
built, while premiums just above it are the hard ones.

## Hardware

| run | machine |
|---|---|
| published results | Notre Dame CRC: dual 12-core Intel Xeon E5-2680 v3 @ 2.50 GHz, or dual 32-core AMD EPYC 7543 @ 2.80 GHz, 256 GB RAM |
| reproduction 2026-07-29 | Apple M1 Max, 10 cores, 32 GB, macOS 26.6 |

Submission used Sun Grid Engine via `run_sc_model_job.py` (queue `long`); a
sanitized copy is in `crc_job_scripts/`.

## Reproduction

A full independent rerun of all 92 MILP instances took 1 h 22 min on the M1 Max
across five concurrent streams, after loop-invariant expressions were hoisted out
of the results-writing loops (they had cost ~10 min per instance, more than the
solve). Every objective value reproduced within the MIP gap it was solved at. See
[RERUN_REPORT.md](RERUN_REPORT.md) for the comparison and
[RECONCILIATION.md](RECONCILIATION.md) for what the private repository added.

Artifacts, checksummed, with the driver scripts and full environment capture:
`~/DowlingLab/Papers/incentivizing-saf-repro-archive/2026-07-29/`.

## Figures

Not every figure in the manuscript comes from a notebook. See the README section
"Figure provenance" for which are generated, which are composed in PowerPoint from
generated panels, and which are hand-drawn schematics with no generating script.
