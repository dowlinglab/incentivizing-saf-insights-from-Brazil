# What is missing to reproduce every result

> **Status, updated 2026-07-30.** This file was written before the tornado driver,
> the integer-cut consolidation script and the `payment` column existed. **Three of
> the four gaps below are now closed**, and the sections are annotated accordingly.
> The remaining gap is the figure post-processing in §3. For the current picture see
> [RECONCILIATION.md](RECONCILIATION.md) and the figure manifest in the
> [README](README.md); for what was verified by re-running, see
> [RERUN_REPORT.md](RERUN_REPORT.md).

Audit of every file, Excel sheet, and dataframe column referenced by the five run
scripts, `create_maps.py`, `create_sc_model_full.py`, and the four notebooks,
checked against what the repository actually ships. 261 required paths were
verified present.

The headline: only **two files** are literally absent, and one of those no longer
matters. The real gaps are **three artifacts with no code path** and a set of
manual figure steps.

## 1. Absent files

| file | needed by | status |
|---|---|---|
| `ne_50m_admin_0_countries.shp` (+ `.shx`, `.dbf`) | `create_maps.py` → `run_create_maps.py` | **resolved** — Natural Earth 1:50m is not redistributable here, so `create_maps.py` now dissolves `gadm41_BRA_1.shp` to get the Brazil outline. Nothing to add. |
| `gadm41_BRA_1.prj` | shapefile CRS | **harmless** — geopandas reports `crs=None` and every caller does `set_crs(epsg=4326)` explicitly. Adding the `.prj` would be tidier but changes nothing. |

Everything else read by the code is present, including all 13 sheets of
`base_case_data_with_demands.xlsx`, the `ethanol` and `annexed` sheets of
`335MillsLatitudesLongitudes.xlsx`, the `Case 1 50%` / `Case 3 50%` sheets of
`integer_cut_organized_data.xlsx`, all 24 `Case<N>/interest_mid_blend_<pct>/`
result folders, all 100 `integer_cuts_case{1,3}/<pct>/int_cuts<i>/` folders, all
seven `mill_specific_incentives/sp*_e0_interest_mid_blend_50/` folders, and
`unconstrained_SAF/Case5/production.csv`.

## 2. Missing code — results that no script in this repo can produce

These are the substantive gaps. Each is a published result with no reproducible
path from the shipped code.

### 2a. The tornado diagram (`images/tornado.png`, manuscript Fig. `fig:tornado`)

The manuscript reports a ±20% one-at-a-time sensitivity of the *recommended SAF
premium* over sugar, ethanol, and jet fuel prices plus ATJ production cost and
conversion, defining the recommended premium as the minimum premium at which
Case 5 SAF production reaches 50% of jet fuel demand.

**CLOSED.** When this was written nothing in the repository did it — no script, no
results folder, no notebook cell; `grep -ril tornado` returned nothing. All three now
exist:

- the eleven `unconstrained_SAF/Case 5 …/production.csv` files, recovered from the
  private repository, from which all ten published thresholds reproduce
  (sugar 2.6/2.6, ATJ OPEX 2.4/2.8, jet 3.4/1.8, ethanol 1.5/3.7, conversion
  4.0/1.7, against a 2.6 R$/L base)
- `run_tornado_sensitivity.py`, which applies each ±20% perturbation
  programmatically. The parameter mapping was undocumented and had to be derived,
  then verified against all ten thresholds: `prices.sug.price`, `prices.et.price`,
  `prices.saf.price`, `prices.saf.cost` ("ATJ OPEX") and `conversions.et_to_saf`
  ("ATJ Conversion")
- `make_tornado.py`, which reads the thresholds from the CSVs rather than the
  hard-coded DataFrame the original plot used

It is still the most compute-heavy study: a full sweep of all ten scenarios is
roughly ten Case 5 sweeps, and one CRC log records 85.6 h of solver time for a
single 41-point sweep. `--bisect` finds a threshold in about six solves instead of
41.

### 2b. `integer_cut_organized_data.xlsx`

Shipped as data and cited in the manuscript's Supporting Information statement,
and it is the only input to `integercutanalysis.ipynb`. When this was written no
script built it from the raw
`integer_cuts_case{1,3}/50/int_cuts{0..9}/key_results_mills.csv` files; the
`SAF Mill` / `Percentage ` columns were assembled by hand.

**CLOSED.** `consolidate_integer_cuts.py` derives it, and `--verify` confirms the
shipped spreadsheet is faithful to its raw inputs — all 19 Case 1 mills and all 13
Case 3 mills, percentages matching exactly. So the hand assembly was done correctly;
it is simply now reproducible.

Note that alternative optima are platform-dependent (see [REPRODUCE.md](REPRODUCE.md)
§7), so consolidating a *fresh* integer-cut run will legitimately give different
mills — see the degeneracy discussion in [RERUN_REPORT.md](RERUN_REPORT.md).

### 2c. The `payment` column in `mill_specific_incentives/*/key_results_mills.csv`

`SensitivtyAnalysis.ipynb` cell 9 plots `results[i]['payment']`, but
`run_mill_specific_incentives.py` writes only `incentives`. The committed CSVs
contain both, so `payment` was added by an undocumented post-processing step.

Reverse-engineered from the committed files:

```
payment = incentives / (SAF * 1000)      # R$/L of SAF
```

(e.g. 1,770,488,524 / (700,000 × 1000) = 2.5293, matching BIOSEV Santa Elisa in
`sp0_e0`.) Verified against `sp0_e0` and `sp1500_e0`.

**CLOSED.** `run_mill_specific_incentives.py` now derives the column, guarded at
`SAF = 0`, reproducing the committed values' 2.50–2.61 R$/L range. Regenerating the
folder no longer breaks `SensitivtyAnalysis.ipynb`.

Related, cosmetic: the committed `Case1`–`Case4` CSVs have no `incentives` column
even though the current script writes one, so those files predate that addition.
Harmless — no notebook reads it.

## 3. Missing figures — manual steps with no automated path

The manuscript's `images/` folder does not correspond 1:1 to `Results_Figures/`.

**20 SI maps with no code path:** `case1_10.png` … `case4_50.png` (each case ×
10/20/30/40/50% blend, showing full supply chain connections). These are screen
captures of the interactive `mill_airport_map.html` that `run_create_maps.py`
produces — the same provenance as the stray `map_still_2a_50.png` and
`map_still_2b_50.png` committed inside `Case2/` and `Case4/`. Reproducing them
means opening 20 HTML maps and screenshotting each.

**Renamed / post-processed in the manuscript:**

| manuscript | produced by |
|---|---|
| ~~`emissions_v6.png`~~ → now `emissions_v7.png` | **`make_emissions_figure.py`** — generated end to end, including the dashed 0.65 bound and the A–E point labels that previously existed in neither repository. Its output is byte-identical to `images/emissions_v7.png`, making Figure 6 the only manuscript figure that is bit-reproducible from a script here. |
| `inputmaps_v4.png` | `fourpanelinputdata.png` + `fourpanelinputdata_legend.png` |
| `fourpanelcostsummary_v2.png` | `fourpanelcostsummary.png` |
| `incentivestudy.png` | `millspecficincentivestudy.png` |
| `ninepanelproductsummary_pos_v2.eps` | `ninepanelproductsummary_pos_v2.png` |
| `figure5_format.eps`, `figure6_format.eps`, `figure7_format.eps` | reformatted exports; source figure for each is not recorded |

The `_v2`/`_v4`/`_format` suffixes mean panels were composited, relabelled, or
converted to EPS outside the notebooks. That editing step is not captured anywhere,
so those manuscript figures cannot be regenerated end to end even though the
underlying plots can. Figures 6 and 10 and SI Figures S21–S22 are the exceptions —
see the figure manifest in the [README](README.md), which carries an explicit
"end to end?" column for every figure.

**Hand-drawn, no code expected:** `problemstatement.png`, `mill_pfd.png`,
`ref_pfd.png`, `graphic_toc.png`.

## 4. Stray files in the results folders

Not missing, but worth knowing they are not script output: `Case2/.../costpie.png`,
`Case2/.../productpie.png`, `Case2/.../ef_to_air_vol_saf.csv` (typo for
`ref_to_air_vol_saf.csv`, which is also present), and the `map_still_*.png`
screenshots in `Case2/` and `Case4/`.

## 5. Priority if you want a fully reproducible release

Items 1–3 of the original list are done. What remains:

1. **Record or automate the figure post-processing** (§3). Figures 1, 7, 8 and 9 are
   composed in PowerPoint from generated panels and Figure 5 is converted to EPS
   outside the notebooks; none of those steps is captured. The README manifest now
   at least says which figures this affects.
2. **The 20 SI maps** (§3) are browser screen captures of the
   `mill_airport_map.html` files. `run_create_maps.py` produces the HTML but cannot
   capture it; automating this needs a headless-browser step.
3. **Curate `Results_Figures/`** — it mixes notebook output with PowerPoint-composed
   figures and some files are superseded. A curation decision rather than a code fix.

Closed since this file was written: the tornado driver and its data (§2a), the
integer-cut consolidation script (§2b), the `payment` column (§2c), and Figure 6,
which is now scripted end to end.
