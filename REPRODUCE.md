# Reproducing the results

Notes for re-running this repository on a machine other than the one used for the
manuscript (Notre Dame CRC, Linux). Written while reproducing on macOS / Apple
Silicon (arm64).

## 1. Environment

```bash
conda env create -f environment.yml
conda activate saf-brazil
python -m ipykernel install --user --name saf-brazil --display-name "Python (saf-brazil)"
```

`environment.yml` pins Pyomo to **6.6.1** (the version reported in the manuscript)
and holds the scientific stack at the same era — importantly **numpy < 2**, since
Pyomo 6.6.1 predates the numpy 2 ABI break.

Verified working versions on osx-arm64:

| package | version |
|---|---|
| python | 3.11.15 |
| pyomo | 6.6.1 |
| numpy | 1.26.4 |
| pandas | 2.0.3 |
| openpyxl | 3.1.5 |
| matplotlib | 3.8.4 |
| geopandas | 0.14.4 |
| shapely | 2.0.7 |
| folium | 0.14.0 |

`openpyxl` is a hard requirement — every input file is `.xlsx` and pandas needs it
as the read engine. It was not listed in the original README dependencies.

## 2. Gurobi

The run scripts call `pyo.SolverFactory('gurobi')`. In Pyomo this resolves to the
**`GUROBISHELL`** interface, which writes an LP file and shells out to the
`gurobi.sh` executable. Consequences:

* Gurobi must be installed **system-wide** (or otherwise have `gurobi.sh` on
  `PATH`). `pip install gurobipy` alone is *not* enough — it ships `gurobi_cl`
  but not `gurobi.sh`. Gurobi is deliberately not a conda dependency in
  `environment.yml` for this reason.
* A **full license** is required. The size-limited license bundled with
  `pip install gurobipy` caps out at 2,000 variables; these instances have
  ~149,000.

Check the interface before running anything expensive:

```bash
python -c "import pyomo.environ as pyo; s=pyo.SolverFactory('gurobi'); print(s.available(False), s.executable())"
```

The manuscript used Gurobi **10.0.3**. Reproduction here used the Gurobi
**10.0.1** already installed at `/usr/local/bin/gurobi.sh` with an academic
license at `~/gurobi.lic`.

## 3. Which script produces which result

| Script | Manuscript output |
|---|---|
| `run_blend_and_opt_sensitivity.py` | Cases 1–4 × blends 0–50% (24 instances) → `Case1/`…`Case4/` |
| `run_integer_cuts.py` | Ten alternate optima for Cases 1 and 3 at 50% blend → `integer_cuts_case1/`, `integer_cuts_case3/` |
| `run_mill_specific_incentives.py` | Mill-specific incentive study → `mill_specific_incentives/` |
| `run_unconstrained_SAF_prem_sensitivity.py` | Case 5, SAF premium sweep → `unconstrained_SAF/` |
| `run_create_maps.py` | Interactive folium HTML maps (`mill_airport_map.html`) |
| `SupplyChainSummary.ipynb` | Figs. `ninepanelproductsummary_pos_v2`, `fourpanelcostsummary`, `emissions_sensitivity` |
| `SupplyChainMaps.ipynb` | Figs. `optimalsclocationszoom`, `fourpanelinputdata`, legends |
| `SensitivtyAnalysis.ipynb` | Figs. `additionalSAFcost`, `unconstrained_SAF`, `millspecficincentivestudy` |
| `integercutanalysis.ipynb` | Figs. `integercutlocations`, `integercutlocationszoom` |

## 4. The run scripts are not parameterized — edit them per case

`run_blend_and_opt_sensitivity.py` reproduces **one** case per invocation. To get
all 24 instances it has to be edited and re-run four times:

| Case | Perspective | ATJ investment | `results_dir1` (line 10) | `profit_obj` (line 25) | fix investments |
|---|---|---|---|---|---|
| 1 | central planner | mills | `"Case1"` | `False` | `m.y_ref[i].fix(0)` (lines 44–45 active) |
| 2 | central planner | refineries | `"Case2"` | `False` | `m.y[i].fix(0)` (uncomment lines 48–49, comment 44–45) |
| 3 | investor | mills | `"Case3"` | `True` | `m.y_ref[i].fix(0)` |
| 4 | investor | refineries | `"Case4"` | `True` | `m.y[i].fix(0)` |

Same pattern elsewhere:

* `run_integer_cuts.py` — line 9 `results_dir1` and line 25 `profit_obj`
  (`False` → Case 1, `True` → Case 3).
* `run_mill_specific_incentives.py` — line 22 `saf_prem` and line 33 the output
  folder name must be changed together, once per premium in
  {0, 500, 1000, 1500, 2000, 2500, 3000}.

The scripts write into the committed results folders, so **back up or redirect
`results_dir1` before re-running** if you want to keep the original numbers for
comparison.

## 5. Portability issues found on macOS

These are real blockers, not warnings.

1. **Windows path separators in three notebooks.** `SensitivtyAnalysis.ipynb`,
   `SupplyChainMaps.ipynb`, and `SupplyChainSummary.ipynb` build paths as
   `this_file_path + '\\Case1\\interest_mid_blend_0\\key_results_mills.csv'`
   where `this_file_path = os.getcwd()`. On macOS/Linux this yields a single
   filename containing backslashes and raises `FileNotFoundError`. Every
   `pd.read_csv` in those notebooks needs its `'\\'`/`'\'` replaced with `'/'`
   (or `os.path.join`). `integercutanalysis.ipynb` is unaffected — it reads
   `integer_cut_organized_data.xlsx` by relative path.

2. **`ne_50m_admin_0_countries.shp` is missing from the repo.** `create_maps.py`
   line 44–45 does `gpd.read_file("ne_50m_admin_0_countries.shp")`, so
   `run_create_maps.py` fails immediately. This is the Natural Earth 1:50m Admin 0
   Countries shapefile (not redistributed here). Either add it, or substitute the
   copy bundled with geopandas 0.14:
   `gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))` — note the
   bundled copy is 1:110m and its country-name column is `name`, not `NAME`.
   Only the interactive HTML maps depend on this; **no manuscript figure does.**
   `SupplyChainMaps.ipynb` and `integercutanalysis.ipynb` assign
   `shapefile_path = 'ne_50m_admin_0_countries.shp'` but never read it — the
   static maps use `gadm41_BRA_1.shp`, which is present.

3. **`gadm41_BRA_1.prj` is absent**, so geopandas reports `crs=None`. Harmless —
   both notebooks call `set_crs(epsg=4326)` explicitly before
   `to_crs(epsg=5880)`.

4. **Output-folder name mismatch for Case 5.**
   `run_unconstrained_SAF_prem_sensitivity.py` line 16 writes to
   `unconstrained_SAF/Case 5/` (with a space), but the committed folder is
   `unconstrained_SAF/Case5/` and `SensitivtyAnalysis.ipynb` reads
   `unconstrained_SAF\Case5\production.csv`. Re-running the script creates a
   second folder the notebook will not find.

## 6. Model size does not match the manuscript

The manuscript (Sections "Central Planner"/"Investor", and again for Case 5)
reports each MILP instance as **124,711 continuous variables, 3,784 binary
variables, 5,949 equality constraints, 9,246 inequality constraints**.

Building Case 1 from the committed `create_sc_model_full.py` with the exact
arguments in `run_blend_and_opt_sensitivity.py` (`max_saf_capacity=700000`,
`breakpoints=10`, `grass_roots_factor=0.5`, `ref_blend=True`) gives:

| | manuscript | this code |
|---|---|---|
| continuous variables | 124,711 | **149,102** |
| binary variables | 3,784 | **3,357** |
| equality constraints | 5,949 | **6,727** |
| inequality constraints | 9,246 | **8,870** |

Counts after fixing `z`, `y_ref`, and `s` to 0 as Case 1 does: 148,767 continuous
and 3,319 binary. The differences are not explained by variable fixing or by
`breakpoints`, so the reported counts appear to come from an earlier revision of
the model. Worth reconciling before publication. The binaries here are
`y` (335) + `z` (29) + `y_ref` (9) + `aux` (2,680) + `aux_air` (232) +
`aux_ref` (72) = 3,357.

## 7. What actually happened on re-run (macOS/M1 Max, 10 threads, Gurobi 10.0.1)

| instance | committed objective | re-run objective | rel. diff | mill set |
|---|---|---|---|---|
| Case 1, 0% blend | 2.18685178e+11 | 2.18685178e+11 | −2.8e−16 | identical (empty) |
| Case 1, 50% blend | 2.21149364e+11 | 2.21151272e+11 | +8.6e−06 | **differs** (11 vs 7) |
| Case 3, 50% blend | 1.24560684e+11 | 1.24560518e+11 | −1.3e−06 | identical (6 mills) |

**Objective values reproduce.** All three agree to well inside the 0.003% MIP gap
the analysis was run at, i.e. the re-runs and the committed results are both
certified-optimal answers to the same problem.

**Case 3 reproduces exactly**, including the six selected mills — BIOSEV Santa
Elisa, Iracema, RAIZEN Barra, Santa Cruz-SP, São João de Araras, São Martinho —
matching the manuscript's "Case 3 recommends six ATJ facilities, all located in
São Paulo."

**Case 1's mill locations do not reproduce, and this is expected.** At 50% blend:

* committed (7 mills): BIOSEV Ares, BIOSEV Santa Elisa, Coruripe, RAIZEN Barra,
  Santa Cruz-SP, São João de Araras, São Martinho
* re-run (11 mills): BIOSEV Ares, BIOSEV Santa Elisa, Central Olho D'Água,
  Ferrari/São Marino, Marituba, Monte Alegre, Pindorama, Pinheiro, RAIZEN Barra,
  São João de Araras, São Martinho

This is exactly the degeneracy the manuscript documents (Section "Integer Cut
Analysis"): many designs lie within the 0.003% gap and mills can be <3 km apart,
so Gurobi version, platform, and thread count change tie-breaking. Reassuringly,
all three mills the manuscript identifies as chosen in 100% of optimal solutions —
**RAIZEN Barra, São João de Araras, São Martinho** — appear in both sets.

Note the asymmetry: Case 3 (investor, concentrated in São Paulo) is well
determined, while Case 1 (central planner, spread across São Paulo and the
Northeast) is not. Two caveats this raises for the text:

* The manuscript states Case 1 "recommends seven ATJ facilities distributed across
  São Paulo (four) and the Northeast (three)." The facility *count*, not just the
  identities, moves within the MIP gap — 11 here. Any claim about the number of
  facilities (and the derived Mt·km transportation totals in Table
  `tab:map summary`) is gap-sensitive and should be stated as one representative
  optimum rather than *the* optimum.
* Reproducing the exact committed design would require the original solver
  version and thread count, which is not achievable in general. Compare objective
  values and aggregate flows, not location sets.

**Solve times are much shorter than reported.** The manuscript reports ~20 min per
instance on the CRC. On an M1 Max with 10 threads: <1 s at 0% blend, 40 s (Case 1)
and 12 s (Case 3) at 50% blend. Model construction in Pyomo takes ~5 s. Set
`solver.options['Threads']` if you want more deterministic comparisons across
machines.
