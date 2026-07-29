# Reconciling the private repo against this public repo

Selected files were manually migrated from a private repository into this public
one. The reproduction work documented in [RERUN_REPORT.md](RERUN_REPORT.md) and
[MISSING_FILES.md](MISSING_FILES.md) turned up several results that the public
code demonstrably cannot produce, which means the migration was incomplete. This
file is the working checklist for that comparison.

## Evidence that the migrated code is not the code that produced the manuscript

Five independent signals, strongest first:

1. **The model is a different size than the manuscript reports.** The manuscript
   states three times (`main_jcp.tex` lines 485, 498, 512) that each MILP instance
   has 124,711 continuous variables, 3,784 binary variables, 5,949 equality and
   9,246 inequality constraints. Building Case 1 from `create_sc_model_full.py`
   with the exact arguments the run scripts pass gives **149,102 / 3,357 / 6,727 /
   8,870**. Not explained by variable fixing or by `breakpoints`. The private repo
   almost certainly holds the model version these counts came from.

2. **A model module referenced by the run scripts does not exist here.** Three run
   scripts opened with a commented-out import of a module that was never migrated
   (visible at commit `589440a`, before the refactor):

   ```
   run_blend_and_opt_sensitivity.py:1        # from create_sc_model_with_demand import *
   run_mill_specific_incentives.py:1         # from create_sc_model_with_demand import *
   run_unconstrained_SAF_prem_sensitivity.py:1  # from create_sc_model_with_demand import *
   ```

   **Search the private repo for `create_sc_model_with_demand.py` first** and check
   its variable counts against item 1.

3. **Committed CSVs contain columns no script writes.** The migrated results are
   downstream of code that is not here:

   | file | column present | written by public code? |
   |---|---|---|
   | `mill_specific_incentives/*/key_results_mills.csv` | `payment` | no (now derived — see below) |
   | `Case1-4/*/key_results_mills.csv` | `incentives` | yes, but absent from the committed files |
   | `unconstrained_SAF/Case5/production.csv` | `premium` | yes, but absent from the committed file |

   The last two are the reverse direction: the committed data predates columns the
   current scripts write, so the migrated *results* and migrated *code* are from
   different points in the private repo's history.

4. **Two published numbers are untraceable to any shipped code.** Table 2's
   Mt·km columns and the mill-specific objective values (see checklist items 2 and
   5 below).

5. **The model contains commented-out earlier formulations.** In
   `create_sc_model_full.py`, the active `sc_cost_expression` includes
   `+ sum(m.s[i] for i in m.MILLS)` (incentive payments) while the commented-out
   predecessor objective does not, and a commented `pos_profs` uses
   `reference_profit1b` where the active one uses `0`. The private repo likely has
   these as distinct files or commits rather than comments.

## Reconciliation checklist

Ordered by how much of the manuscript depends on it.

### 1. The model version behind the reported instance sizes — **blocking**

*Symptom:* counts in item 1 above.
*Look for:* `create_sc_model_with_demand.py`, or any `create_sc_model*.py` variant.
*Verify:* build Case 1 with `max_saf_capacity=700000, breakpoints=10,
grass_roots_factor=0.5, ref_blend=True, profit_obj=False` and count active Vars
and Constraints. Target 124,711 / 3,784 / 5,949 / 9,246. A script that does the
counting is archived alongside the reproduction results.
*Why it matters:* if the private model differs structurally, every reproduced
number in `RERUN_REPORT.md` was computed against a different formulation than the
manuscript describes, and the objective agreement found there is coincidental
rather than confirmatory.

### 2. Whatever computes Table 2's Mt·km columns — **blocking**

*Symptom:* Table 2 reports Stage 1 / Stage 2 / Total of 455/316/771 Mt·km for
Case 1. `SupplyChainSummary.ipynb` prints 5,913 / 22,529 — verifiable from the
notebook's own committed output, so this predates any rerun. Not a unit
conversion: Case 1 is off by ~37×, Case 3 by ~52×, and the Stage 1 : Stage 2
ordering is inverted. Table 2's columns are internally consistent
(Stage 1 + Stage 2 = Total for all four cases), so the values are deliberate.
*Look for:* a different version of `SupplyChainSummary.ipynb`, or a separate
distance/mass-distance script or spreadsheet.
*Verify:* it should reproduce 455/316/771, 608/446/1,054, 237/878/1,115 and
653/1,282/1,935 from the committed Case 1–4 results at 50% blend.
*Why it matters:* a published table with no derivable provenance.

### 3. The tornado diagram — **blocking**

*Symptom:* `images/tornado.png` and the ±20% sensitivity narrative at
`main_jcp.tex:641` have no counterpart in the public code at all;
`grep -ril tornado` returns nothing.
*Look for:* a script that perturbs sugar / ethanol / jet fuel prices and ATJ
production cost and conversion by ±20% and re-runs the Case 5 premium sweep for
each, plus its results folder and plotting cell.
*Verify:* it should reproduce the tornado ordering and the baseline recommended
premium of 2.6 R$/L, which the rerun confirms.
*Cost note:* this is the most compute-heavy gap — roughly ten Case 5 sweeps. Case 5
took 1 h 51 min sequentially on an M1 Max, so budget accordingly.

### 4. The script that builds `integer_cut_organized_data.xlsx`

*Symptom:* the spreadsheet is shipped and cited in the SI, and
`integercutanalysis.ipynb` depends on it, but nothing builds it from the raw
`integer_cuts_case{1,3}/50/int_cuts{0..9}/` folders.
*Good news:* the spreadsheet is **verified faithful** — recomputing selection
frequencies from the committed raw folders reproduces its `SAF Mill` /
`Percentage ` columns exactly for all 19 Case 1 and 13 Case 3 mills. So this is a
missing convenience script, not a data-integrity problem.
*Look for:* the aggregation script or notebook cell.

### 5. Whatever produced the mill-specific objective values

*Symptom:* `mill_specific_incentives/*/key_results_mills.csv` has `objective` and
`sc cost` equal to exactly 238.0e9, 237.0e9, … 232.0e9 — a perfect arithmetic
sequence stepping by −1e9. Gurobi does not emit values like that. Reruns land
within 0.11% of them.
*Look for:* whether the private repo's copies contain real solver output, or
whether a spreadsheet or manual edit produced the round numbers.
*Mitigation already in place:* no figure depends on these columns —
`SensitivtyAnalysis.ipynb` cell 9 plots `total_incentive = [5.42, 5.41, ...]` from
a hardcoded list with `sc_cost = []` left empty. Check whether the private version
computes that list from data.

### 6. The `payment` post-processing step

*Symptom:* `SensitivtyAnalysis.ipynb` reads a `payment` column that no migrated
script wrote.
*Resolved here:* derived in `run_mill_specific_incentives.py` as
`s[u] / (SAF_u * 1000)` (R$/L), guarded at `SAF_u = 0`, reproducing the committed
column's 2.50–2.61 R$/L range.
*Verify:* confirm the private repo uses the same formula rather than a different
normalisation.

### 7. `ne_50m_admin_0_countries.shp`

*Symptom:* `create_maps.py` read this Natural Earth 1:50m shapefile, which is not
in the public repo, so `run_create_maps.py` could never run.
*Resolved here:* the Brazil outline is now dissolved from `gadm41_BRA_1.shp`,
which does ship. No action needed unless the private version differs
cartographically.

### 8. The 20 SI supply chain maps and the figure post-processing

*Symptom:* `images/case1_10.png` … `case4_50.png` are screen captures of the
folium HTML with no automated path. Separately, the manuscript uses
`emissions_v6.png`, `inputmaps_v4.png`, `fourpanelcostsummary_v2.png`,
`incentivestudy.png` and `figure{5,6,7}_format.eps`, which are composited or
relabelled versions of the notebook outputs.
*Look for:* any scripted figure assembly, or confirm these are manual steps and
document them as such.

## Claims to re-check once the private code is in hand

Two manuscript statements that the rerun contradicts. Both may resolve differently
against the private model, so re-test rather than edit yet:

- **`main_jcp.tex:606`**: "For investments at refineries (Cases 2 and 4), there is
  no expected variation in the selected refinery within the 0.003% MIP gap." Holds
  for Case 4 (6/6 blends identical) but fails for Case 2 (differs at 20/30/40/50%;
  7 refineries → 4 at 50% blend, objectives within 1.4e-05).
- **Figure `fig:SAF locations` caption**: three mills "chosen in 100% of optimal
  solutions regardless of the decision-making perspective." Raízen Barra and São
  João de Araras hold at 100% in both cases on an independent integer-cut run; São
  Martinho drops to 90% (Case 1) and 80% (Case 3).

Also gap-sensitive, and quoted in the text: the facility counts at
`main_jcp.tex:602` and in Table 2 for Cases 1 and 2 (7→11 mills, 7→4 refineries).
Cases 3 and 4 reproduce exactly.

## The archived reproduction results

Kept **outside** this repository, so ~145 MB of regenerated CSVs do not enter the
published artifact:

```
~/DowlingLab/Papers/incentivizing-saf-repro-archive/2026-07-29/
  results/      all regenerated CSVs (Cases 1-4, integer cuts, mill-specific, Case 5)
  figures/      all 13 regenerated figures
  notebooks/    the four notebooks as executed, outputs inline
  provenance/   RUN_INFO.txt, conda-list.txt, environment-frozen.yml
  logs/         the exact driver scripts and their stdout
  MANIFEST.sha256
  README.md
```

An earlier run on 2026-07-27 produced equivalent artifacts but was written to
`/private/tmp`, which macOS cleared before they could be archived. Its findings
survive in `RERUN_REPORT.md` because they were committed; the raw files did not.
**Do not stage reproduction output under `/tmp`.**
