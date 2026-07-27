# What is missing to reproduce every result

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

**Nothing in the repository does this.** There is no script, no results folder,
and no notebook cell — `grep -ril tornado` over the code returns nothing. It is
also the most compute-heavy missing piece: ~5 parameters × 2 directions, each
requiring its own premium sweep (i.e. roughly ten more runs of
`run_unconstrained_SAF_prem_sensitivity.py` with perturbed prices in
`base_case_data_with_demands.xlsx`).

A `run_tornado_sensitivity.py` plus a `tornado/` results folder and a plotting
cell would close this.

### 2b. `integer_cut_organized_data.xlsx`

Shipped as data and cited in the manuscript's Supporting Information statement,
and it is the only input to `integercutanalysis.ipynb` — but **no script builds
it** from the raw `integer_cuts_case{1,3}/50/int_cuts{0..9}/key_results_mills.csv`
files that `run_integer_cuts.py` writes. The `SAF Mill` / `Percentage ` columns
were assembled by hand.

Without that script, `integercutanalysis.ipynb` cannot be regenerated from a
fresh integer-cut run — and since alternative optima are platform-dependent (see
[REPRODUCE.md](REPRODUCE.md) §7), a rerun *will* produce different mills.

### 2c. The `payment` column in `mill_specific_incentives/*/key_results_mills.csv`

`SensitivtyAnalysis.ipynb` cell 9 plots `results[i]['payment']`, but
`run_mill_specific_incentives.py` writes only `incentives`. The committed CSVs
contain both, so `payment` was added by an undocumented post-processing step.

Reverse-engineered from the committed files:

```
payment = incentives / (SAF * 1000)      # R$/L of SAF
```

(e.g. 1,770,488,524 / (700,000 × 1000) = 2.5293, matching BIOSEV Santa Elisa in
`sp0_e0`.) Verified against `sp0_e0` and `sp1500_e0`. **Regenerating this folder
today produces CSVs without `payment`, so the notebook raises `KeyError`.** Either
add the column to the script's `key_results` dict or compute it in the notebook.

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
| `emissions_v6.png` | `Results_Figures/emissions_sensitivity.png` |
| `inputmaps_v4.png` | `fourpanelinputdata.png` + `fourpanelinputdata_legend.png` |
| `fourpanelcostsummary_v2.png` | `fourpanelcostsummary.png` |
| `incentivestudy.png` | `millspecficincentivestudy.png` |
| `ninepanelproductsummary_pos_v2.eps` | `ninepanelproductsummary_pos_v2.png` |
| `figure5_format.eps`, `figure6_format.eps`, `figure7_format.eps` | reformatted exports; source figure for each is not recorded |

The `_v2`/`_v4`/`_v6`/`_format` suffixes mean panels were composited, relabelled,
or converted to EPS outside the notebooks. That editing step is not captured
anywhere, so the manuscript figures cannot be regenerated end-to-end even though
the underlying plots can.

**Hand-drawn, no code expected:** `problemstatement.png`, `mill_pfd.png`,
`ref_pfd.png`, `graphic_toc.png`.

## 4. Stray files in the results folders

Not missing, but worth knowing they are not script output: `Case2/.../costpie.png`,
`Case2/.../productpie.png`, `Case2/.../ef_to_air_vol_saf.csv` (typo for
`ref_to_air_vol_saf.csv`, which is also present), and the `map_still_*.png`
screenshots in `Case2/` and `Case4/`.

## 5. Priority if you want a fully reproducible release

1. Add the tornado sensitivity script and its results (§2a) — the only *published
   result* with no code at all.
2. Add `payment` to `run_mill_specific_incentives.py` (§2c) — one line, and
   without it a notebook is broken against fresh results.
3. Add a script that builds `integer_cut_organized_data.xlsx` from the raw
   integer-cut folders (§2b).
4. Record the figure post-processing steps in §3, or move the panel compositing
   into the notebooks.
