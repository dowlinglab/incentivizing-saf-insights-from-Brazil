# Reconciling the private repo against this public repo

Selected files were manually migrated from a private repository
(`C2C_Project`, branch `Maddie_branch`) into this public one. The reproduction work
in [RERUN_REPORT.md](RERUN_REPORT.md) found published results the public code could
not produce; this file tracks what the private repo explained and what it did not.

**Status: two of three blockers closed, one confirmed and worse than first thought.**
Everything the audit's Section 10 lists as "promised but absent" is now present.

| # | item | status |
|---|---|---|
| 1 | model version behind the reported instance sizes | **closed** — the migrated model is correct; the manuscript is wrong |
| 2 | whatever computes Table 4's Mt·km columns | **confirmed missing**, and the table is internally inconsistent |
| 3 | the tornado diagram | **closed** — data recovered, driver and plot written |
| 4 | script for `integer_cut_organized_data.xlsx` | **closed** — written, and the shipped file verified faithful |
| 5 | the mill-specific objective values | **closed** — the private copies carry the same round numbers, so this is not a migration artefact; no result depends on them |
| 6 | the `payment` post-processing step | **closed** — derived in the script |
| 7 | `ne_50m_admin_0_countries.shp` | **closed** — dependency removed |
| 8 | the 20 SI maps and figure post-processing | **documented** as manual steps |

---

## 1. Model size — closed. The migrated model is right; the manuscript is wrong.

The manuscript reports 124,711 continuous / 3,784 binary / 5,949 equality / 9,246
inequality in three places (`main_jcp.tex` lines 485, 498, 512). **No module in
either repository produces those numbers**, and the search for a module that does
is over: declared binaries are `entity_count × (breakpoints − 1)`, and none of the
five candidates lands on 3,784.

| module | continuous | binary |
|---|---|---|
| `Supply_Chain_Model/create_sc_model.py` | 132,325 | 3,015 |
| `Supply_Chain_Model/create_sc_model_full.py` | 152,117 | 3,357 |
| `Supply_Chain_Model/create_sc_model_with_demand.py` | 142,943 | 3,276 |
| `…_with_demand_no_airports.py` | 132,329 | 3,015 |
| public / paper-folder `create_sc_model_full.py` | 149,102 | 3,357 |
| **manuscript** | **124,711** | **3,784** |

The ten CRC solver logs (`run_sc_model.o*`) are authoritative, and **the migrated
model reproduces them exactly** — see `model_statistics.py`:

| quantity | this code | CRC log | manuscript |
|---|---|---|---|
| continuous | **147,507** | 147,507 | 124,711 |
| binary | **3,319** | 3,319 | 3,784 |
| equality | **6,727** | (no split) | 5,949 |
| inequality | **8,870** | (no split) | 9,246 |
| rows | **15,597** | 15,597 | 15,195 |

The log gives no equality/inequality split, but the split measured here sums
exactly to its 15,597 rows, so all four numbers now have a source. Three counts
legitimately differ — 149,102 declared, 148,767 after fixing `m.z`/`m.y_ref`/`m.s`,
147,507 as the LP writer emits — and the 1,260 gap between the last two is fully
accounted for: `v` 464, `x` 335, `vol_eth_sold`'s diagonal 335, `x_ref` 126.

**Action:** replace the manuscript's four numbers with 147,507 / 3,319 / 6,727 /
8,870, stating they are as-solved. Cases 2 and 4 fix `m.y` instead of `m.y_ref` and
carry 2,993 binaries, so the "every instance" phrasing needs care.

One arithmetic note, in case anyone revisits this: 3,784 = 344 × 11 exactly, where
344 = 335 mills + 9 refineries and 11 = breakpoints − 1 at 12 breakpoints. That is
the only decomposition that fits, and no module builds that entity set — but it
would be where to look if the number ever needs attributing rather than replacing.

## 2. Table 4's Mt·km columns — confirmed missing, and the table is inconsistent

The `(Σd)(Σv)ρ` bug is present in **both** repositories, unchanged, so Table 4 was
not produced by either notebook and how it *was* produced remains unknown.

`supply_chain_distances.py` implements the correct `Σ(v·d)ρ` and reproduces **seven
of the eight** published entries, treating Stage 1 as the mill→refinery leg only:

| | Stage 1 | published | Stage 2 | published |
|---|---|---|---|---|
| Case 1 | 421.8 | 455 | 316.3 | 316 |
| Case 2 | 608.3 | 608 | 446.2 | 446 |
| Case 3 | 237.0 | 237 | 877.8 | 878 |
| Case 4 | 652.6 | 653 | 1282.1 | 1282 |

The eighth is now explained rather than guessed. Adding half the mill→mill ethanol
leg (33.7 Mt·km) to Case 1 gives 455.5, matching its published 455 — but the same
convention applied to Case 3 gives 281.2 against its published 237. Cases 2 and 4
have no mill→mill flow and cannot distinguish the two.

**Table 4 is internally inconsistent: only Case 1's Stage 1 includes the half
mill→mill term.**

**Action:** adopt "Stage 1 excludes mill→mill", report mill→mill separately as
Stage 0, and correct Case 1 to Stage 1 = 422, Total = 738.

## 3. The tornado diagram — closed

The ten scenario runs exist privately in
`unconstrained_SAF/Case 5 {High,Low} {Conv,Cost,Ethanol,Jet,Sugar}/` and are now
copied here. All ten published thresholds reproduce from them: sugar 2.6/2.6,
ATJ OPEX 2.4/2.8, jet 3.4/1.8, ethanol 1.5/3.7, conversion 4.0/1.7, against a base
of 2.6 R$/L. `images/tornado.png` is byte-identical to the private
`Results_Figures/tornado.png`.

What was genuinely missing is now written:

- `run_tornado_sensitivity.py` applies the ±20% perturbation programmatically
  (it was done by hand between runs). The parameter mapping was undocumented; it
  was derived and then verified against all ten thresholds:
  `prices.sug.price`, `prices.et.price`, `prices.saf.price`, `prices.saf.cost`
  ("ATJ OPEX"), `conversions.et_to_saf` ("ATJ Conversion").
- `make_tornado.py` reads the thresholds from the CSVs instead of the hand-typed
  DataFrame the private notebook used.
- `run_unconstrained_SAF_prem_sensitivity.py` now saves per-premium
  `key_results_mills.csv` / `_ref.csv`, so which mills are selected at each premium
  is recoverable without re-solving — the fix that stops this gap recurring.

## 5. The mill-specific objective values — closed

`mill_specific_incentives/*/key_results_mills.csv` has `objective` and `sc cost`
equal to exactly 238.0e9, 237.0e9 … 232.0e9 — a perfect arithmetic sequence
stepping by −1e9, which Gurobi does not emit.

**The private copies carry byte-identical round numbers**, checked 2026-07-29 across
all seven premiums. So the rounding did not happen during migration and no code in
either repository produces those values; the column was overwritten at some point
in the private repo's own history.

Consequence for replication: nothing. No published result depends on the column —
`SensitivtyAnalysis.ipynb` cell 9 plots `total_incentive = [5.42, 5.41, ...]` from a
hardcoded list with `sc_cost = []` left empty. Rerunning
`run_mill_specific_incentives.py` produces genuine solver values (238,269,815,834.7
for sp0_e0, within 0.11% of the placeholder). Treat the committed column as
untrustworthy and regenerate if it is ever needed.

## Corrections to the earlier version of this file

- **The column-provenance evidence largely dissolves.** `payment` *is* now written
  by `run_mill_specific_incentives.py`. Both repos' `mill_specific_incentives` CSVs
  contain `incentives` and `payment`. The Cases 1–4 CSVs legitimately have neither,
  because those runs fix `m.s = 0`. The only real instance is `premium` missing from
  the committed base `Case5/production.csv` while the ten tornado scenarios have
  it — the base run simply predates them. This is no longer evidence that results
  and code come from different points in history.
- **No parameter drift exists.** `base_case_data_with_demands.xlsx` is
  byte-identical between the repos.
- **Table numbering:** it is Table 4, not Table 2 (the 4th `table` environment in
  `main_jcp.tex`). Corrected throughout.

## The `_v2` trap — worse than a result-folder problem

The private repo carries `Case1_v2`–`Case4_v2`, a **different model variant**: they
cost the ethanol *distribution* leg, adding 3.74 B R$/yr at 0% blend where the
published model has exactly zero, and Case 1 selects 15 mills at entirely different
sites, none of them the three essential ones. The published results are non-`_v2`.

**The hazard is not limited to result folders and two notebooks.
`Supply_Chain_Model/create_sc_model_full.py` is itself the `_v2` model.** It adds

- `vol_eth_sold_ref_market` (335 × 9 = 3,015 continuous — exactly the
  152,117 − 149,102 delta in the table above),
- an `eth_distribution_sum` expression and a 335-row `eth_sold_distribution`
  constraint,
- and folds that variable into the mill→refinery logistic cost.

21 substantive diff lines against the public copy. The **paper-folder** copy
(`C2C_Project/Incentivizing_SAF_Insights_from_Brazil/create_sc_model_full.py`) has
none of it and matches the public one. So "the two repos agree on the model" holds
only for the paper-folder copy — and anyone restoring "the original model" would
naturally reach for the folder called `Supply_Chain_Model`, silently switching
models.

Do not sync `Supply_Chain_Model/create_sc_model_full.py`, the private
`SupplyChainMaps.ipynb`, or the private `run_create_maps.py` over the public
copies. Verified 2026-07-29: the public `create_maps.py`, `run_create_maps.py` and
all four notebooks reference non-`_v2` folders.

## Claims to re-check in the manuscript

- **`main_jcp.tex:606`** — "For investments at refineries (Cases 2 and 4), there is
  no expected variation in the selected refinery within the 0.003% MIP gap." Holds
  for Case 4 (6/6 blends identical); fails for Case 2 (differs at 20/30/40/50%;
  7 refineries → 4 at 50%, objectives within 1.4e-05). Narrow to Case 4.
- **Figure `fig:SAF locations` caption** — of the three mills said to be "chosen in
  100% of optimal solutions", Raízen Barra and São João de Araras hold at 100% in
  both cases on an independent integer-cut run; São Martinho is 90% (Case 1) and
  80% (Case 3).
- **Table 4 facility counts and `main_jcp.tex:602`** — gap-sensitive for Cases 1 and
  2 (7→11 mills, 7→4 refineries). Cases 3 and 4 reproduce exactly. See the
  degeneracy section of [RERUN_REPORT.md](RERUN_REPORT.md), which frames this as a
  validation of Key Finding 2 plus a robustness caveat.
- **Solve time** — "approximately 20 minutes" per instance is wrong in both
  directions: median 1.4–110 s, worst single solve 7.69 h. See
  [PROVENANCE.md](PROVENANCE.md).
- **Gurobi version** — the paper says 10.0.3, the job script loads 11.0.2, the logs
  report 12.0.2.

## The archived reproduction results

Kept **outside** this repository, so 69 MB of regenerated CSVs do not enter the
published artifact:

```
~/DowlingLab/Papers/incentivizing-saf-repro-archive/2026-07-29/
  README.md           provenance, timings, and how to use the tools
  results/            all regenerated CSVs, 615 files
  figures/            all 13 regenerated figures
  notebooks/          the four notebooks as executed, outputs inline
  provenance/         RUN_INFO.txt, conda-list.txt, environment-frozen.yml
  logs/               the driver scripts verbatim, their stdout, comparison.txt
  tools/              count_model_size.py, compare_to_committed.py, merge_case5.py
  MANIFEST.sha256     669 files, all verifying
```

**The archive is a stable baseline, not a single sample.** It is the second full
rerun; an earlier one on 2026-07-27 used a different concurrency layout and
produced identical results, including the same site-set changes and integer-cut
frequencies. The divergence from the committed results is reproducible rather than
thread jitter.

That earlier run's raw artifacts were staged in `/private/tmp`, which macOS cleared
before they could be archived; its findings survived only because they were
committed to git. **Do not stage reproduction output under `/tmp`.**
