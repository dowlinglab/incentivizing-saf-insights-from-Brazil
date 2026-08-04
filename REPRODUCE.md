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

## 4. Running the studies

Every run script takes command-line arguments; nothing needs to be hand-edited.
Use `--help` on any of them for the full list.

> **Expect different facility locations than the committed results.** The designs
> are degenerate: many lie within the MIP gap and some candidate mills are under
> 3 km apart, so the Gurobi version, platform and thread count change which optimum
> is returned. Objectives will agree to well within the gap; the selected sites and
> their *count* will not. This is expected rather than a failed reproduction —
> section 7 below documents what a rerun actually produced, and the README's
> "Read this before comparing your results to ours" summarises what is and is not
> robust. Use `--results-dir` to avoid overwriting the committed results while you
> compare.

```bash
# Cases 1-4, blends 0-50% (the 24 manuscript instances)
for c in 1 2 3 4; do python run_blend_and_opt_sensitivity.py --case $c; done

# Ten alternative optima at 50% blend for Cases 1 and 3
python run_integer_cuts.py --case 1
python run_integer_cuts.py --case 3

# Mill-specific incentives, all seven SAF premiums in one invocation
python run_mill_specific_incentives.py

# Case 5, SAF premium sweep with no blend requirement
python run_unconstrained_SAF_prem_sensitivity.py

# Interactive map of one solved design
python run_create_maps.py --case 1 --blend 0.5
```

| Case | Perspective | ATJ investment | invocation |
|---|---|---|---|
| 1 | central planner (min cost) | mills | `--case 1` |
| 2 | central planner (min cost) | refineries | `--case 2` |
| 3 | investor (max mill profit) | mills | `--case 3` |
| 4 | investor (max mill profit) | refineries | `--case 4` |

By default the scripts write into the committed results folders. To keep the
original numbers for comparison, redirect the output:

```bash
python run_blend_and_opt_sensitivity.py --case 1 --results-dir /tmp/rerun/Case1
```

`--results-dir` accepts an absolute path or a name relative to the script.

Note that the per-mill results loop is slow — it re-evaluates the full
`objective`, `profit_expression`, and `sc_cost_expression` for each of the 335
mills, so writing `key_results_mills.csv` takes ~10 min, considerably longer than
the solve itself on a fast machine.

## 5. Portability

The scripts and notebooks now use `os.path.join` or forward slashes throughout and
resolve input data relative to the script, so they run on Windows, macOS, and
Linux from any working directory. What had to be fixed:

1. **Windows path separators in three notebooks.** `SensitivtyAnalysis.ipynb`,
   `SupplyChainMaps.ipynb`, and `SupplyChainSummary.ipynb` built paths as
   `this_file_path + '\\Case1\\interest_mid_blend_0\\key_results_mills.csv'`
   with `this_file_path = os.getcwd()`. On macOS/Linux that is a single filename
   containing backslashes and raises `FileNotFoundError`. All 21 affected
   `pd.read_csv` calls now use `/`. `integercutanalysis.ipynb` was unaffected.

2. **`ne_50m_admin_0_countries.shp` was missing from the repo**, so
   `run_create_maps.py` failed immediately on
   `gpd.read_file("ne_50m_admin_0_countries.shp")`. That file is the Natural
   Earth 1:50m Admin 0 Countries shapefile, which is not redistributed here.
   Since the outline is only used to draw and bound Brazil, `create_maps.py` now
   dissolves the GADM state boundaries in `gadm41_BRA_1.shp` (already in the
   repo) instead — no external download, no deprecated
   `geopandas.datasets` call. `SupplyChainMaps.ipynb` and
   `integercutanalysis.ipynb` assigned `shapefile_path` but never read it, so
   they needed no change.

3. **`gadm41_BRA_1.prj` is absent**, so geopandas reports `crs=None`. Harmless —
   the code calls `set_crs(epsg=4326)` explicitly before `to_crs(epsg=5880)`.

4. **Output-folder name mismatch for Case 5.**
   `run_unconstrained_SAF_prem_sensitivity.py` wrote to
   `unconstrained_SAF/Case 5/` (with a space) while the notebook reads
   `unconstrained_SAF/Case5/`. Now both use `Case5`.

5. **Implicit Pyomo component replacement.**
   `run_mill_specific_incentives.py` redefined `m.pos_profs`, which
   `create_supply_chain_model` already installs as `ind_profs >= 0`. Pyomo
   silently replaced it with a warning; the replacement is now explicit via
   `del_component`/`add_component`. Behaviour is unchanged — the mill profit
   lower bound is raised from 0 to `reference_profit1b`.

See [MISSING_FILES.md](MISSING_FILES.md) for what the repository still does not
contain.

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
