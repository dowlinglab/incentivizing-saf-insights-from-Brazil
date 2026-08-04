# incentivizing-saf-insights-from-brazil

Supporting codes for "Incentivizing Sustainable Aviation Fuel: Supply Chain and
Policy Insights from Brazil."

## Quick start

```bash
conda env create -f environment.yml
conda activate saf-brazil
python -m ipykernel install --user --name saf-brazil --display-name "Python (saf-brazil)"
```

Then reproduce any study — every script takes command-line arguments, so nothing
needs to be hand-edited:

```bash
for c in 1 2 3 4; do python run_blend_and_opt_sensitivity.py --case $c; done
python run_integer_cuts.py --case 1
python run_integer_cuts.py --case 3
python run_mill_specific_incentives.py
python run_unconstrained_SAF_prem_sensitivity.py
python run_tornado_sensitivity.py --all --bisect
```

Use `--results-dir` to write somewhere other than the committed result folders.
[REPRODUCE.md](REPRODUCE.md) covers the environment in detail;
[PROVENANCE.md](PROVENANCE.md) records what the original runs actually used.

## Read this before comparing your results to ours

**The optimal designs are degenerate. If you rerun these case studies you should
expect a different set of ATJ facilities than the committed results and the
manuscript report, and that is not an error.**

Many designs lie within the MIP gap at essentially the same cost, and some
candidate mills are less than 3 km apart. Which one the solver returns depends on
the tie-breaking, and therefore on:

- the Gurobi version (three are on record for the published results — see below),
- the platform and operating system,
- the thread count, and
- Gurobi's own heuristics and search path, which are not guaranteed stable across
  versions.

Rerunning Case 1 at a 50% blend on macOS/M1 with Gurobi 10.0.1 selected **11 mills
where the committed result has 7**, sharing 5. Case 2 went from 7 refineries to 4.
Both are certified optimal within the stated gap, and the objectives agree to
0.00086% — well inside the 0.003% gap.

### What is and is not robust

| quantity | robust? |
|---|---|
| objective values, costs, profits | **yes** — agree to well within the MIP gap |
| SAF production volumes, blend-level trends | **yes** |
| the threshold SAF premium (2.6 R$/L) and the tornado rankings | **yes** |
| *which* mills are selected | **no** — but the highest-frequency mills recur |
| *how many* facilities are selected | **no** — this moves with the solver |
| Table 4's Mt·km totals, which are derived from the chosen sites | **no** |

The divergence is a **validation, not a defect**. Every mill that differed is
already inside the degenerate set the paper's own integer-cut analysis
characterizes, and the mills both runs agree on are exactly the highest-frequency
ones — the four selected in 10 of 10 cut iterations plus the one selected in 9.
That an independent run on a different platform and solver version reaches the same
core sites by a different route is stronger evidence for those sites than the
integer-cut analysis alone, which used one solver on one machine.

So treat the committed designs as **one representative optimum**, not *the*
optimum. If you need the exact committed design, you need the original solver
version and platform; see [PROVENANCE.md](PROVENANCE.md).

Full evidence, mill by mill, is in
[RERUN_REPORT.md](RERUN_REPORT.md#the-site-set-divergence-is-gap-degeneracy--and-it-validates-key-finding-2);
[REPRODUCE.md](REPRODUCE.md) section 7 records what the rerun produced instance by
instance.

## Dependencies

Pyomo 6.6.1, and Gurobi via Pyomo's `SolverFactory('gurobi')` — which is the
LP-file *shell* interface and needs the `gurobi.sh` executable from a system Gurobi
install on `PATH`, plus a full (non size-limited) license. `pip install gurobipy`
alone is not sufficient. Pinned versions are in `environment.yml`; note that
`openpyxl` is required, since all input data is `.xlsx`.

Three Gurobi versions are on record for the published results: the manuscript names
10.0.3, the CRC job script loads 11.0.2, and the solver logs report **12.0.2**. See
[PROVENANCE.md](PROVENANCE.md).

## MIP gap, per study

The manuscript quotes a single 0.003%; the scripts do not all use it.

| study | MIPGap |
|---|---|
| Cases 1–4, blends 0–50% (`run_blend_and_opt_sensitivity.py`) | 3e-5 (0.003%) |
| Integer cuts, Cases 1 and 3 (`run_integer_cuts.py`) | 3e-5 (0.003%) |
| Mill-specific incentives (`run_mill_specific_incentives.py`) | 3e-4 (0.03%) |
| Case 5 and tornado scenarios | 5e-4 (0.05%) |

Solutions differ *within* these gaps: the set and number of chosen investment sites
is not unique, and a rerun will generally not reproduce the committed designs. This
is expected — see
[Read this before comparing your results to ours](#read-this-before-comparing-your-results-to-ours)
above. The looser the gap, the larger the set of designs that qualify, so Case 5 and
the tornado scenarios at 5e-4 admit more variation than Cases 1–4 at 3e-5.

## Case studies

| Case | Decision maker | ATJ investment | Objective |
|---|---|---|---|
| 1 | central planner | sugarcane mills | minimize total supply chain cost |
| 2 | central planner | refineries | minimize total supply chain cost |
| 3 | investor | sugarcane mills | maximize total mill profits |
| 4 | investor | refineries | maximize total mill profits |
| 5 | investor, no blend requirement | sugarcane mills | maximize total mill profits |

## Python scripts

| script | what it does |
|---|---|
| `create_sc_model_full.py` | builds and initializes the optimization model |
| `create_maps.py` | interactive folium maps of an optimal design |
| `run_blend_and_opt_sensitivity.py` | Cases 1–4 across SAF blend requirements (`--case`) |
| `run_integer_cuts.py` | integer-cut (no-good cut) enumeration of alternative optima (`--case 1|3`) |
| `run_mill_specific_incentives.py` | mill-specific incentives as decision variables, swept over SAF premium |
| `run_unconstrained_SAF_prem_sensitivity.py` | Case 5: SAF premium sweep with no blend requirement |
| `run_tornado_sensitivity.py` | Case 5 under ±20% parameter changes (Figure 10) |
| `run_create_maps.py` | runs `create_maps` for a chosen case and blend |
| `make_tornado.py` | builds Figure 10 from the scenario CSVs |
| `make_emissions_figure.py` | builds Figure 6 end to end, including the 0.65 bound, the A–E labels and the CORSIA lines |
| `model_statistics.py` | MILP size per formulation, against the manuscript and the solver logs |
| `supply_chain_distances.py` | mass-distance per stage — the corrected Table 4 calculation |
| `consolidate_integer_cuts.py` | builds `integer_cut_organized_data.xlsx` from the raw cuts |

## Jupyter notebooks

| notebook | figures |
|---|---|
| `SupplyChainSummary.ipynb` | `ninepanelproductsummary_pos_v4.png` **and `_v4.eps`**, `fourpanelcostsummary.png`, `emissions_sensitivity.png` |
| `SupplyChainMaps.ipynb` | `fourpanelinputdata.png` (+legend), `optimalsclocationszoom.png`, `optimaldesign_legend.png`, `optimaldesignmap50.png` |
| `SensitivtyAnalysis.ipynb` | `additionalSAFcost.png`, `unconstrained_SAF.png`, `millspecficincentivestudy.png` |
| `integercutanalysis.ipynb` | `integercutlocations.png`, `integercutlocationszoom.png` |

`SupplyChainSummary.ipynb` cell 10 reports the Table 4 mass-distances by calling
`supply_chain_distances.py`, so the notebook and the script cannot drift apart. It
previously computed (Σ distances)(Σ volumes)ρ instead of Σ(volume × distance)ρ and
reproduced none of Table 4's entries — Case 1 Stage 1 came out as 5,913 Mt·km
against the 455 published.

## Published artifacts that must not be overwritten

These committed figures are **byte-identical** to the manuscript's images, and that
identity is what establishes their provenance:

| file | identical to | |
|---|---|---|
| `Results_Figures/tornado.png` | `images/tornado.png` | Figure 10 |
| `Results_Figures/ninepanelproductsummary_pos_v4.png` | `images/ninepanelproductsummary_pos_v4.png` | Figure 5, the `.png` |
| `Results_Figures/ninepanelproductsummary_pos_v4.eps` | `images/ninepanelproductsummary_pos_v4.eps` | **Figure 5 as embedded** |
| `Results_Figures/emissions_v11.png` | `images/emissions_v11.png` | **Figure 6 as embedded** |
| `Results_Figures/ninepanelproductsummary_pos_v2.png` | `images/ninepanelproductsummary_pos_v2.png` | Figure 5, **superseded** |

`_v2` was Figure 5 before the emission-factor correction; the manuscript now embeds
`_v4`. Both are kept — `_v2` is the only provenance for the superseded figure, and
nothing should overwrite either. Note that `ninepanelproductsummary_pos_v2.eps`
differs between the repositories: that one was converted by hand outside the
notebook, which is exactly the step `_v4` removed.

The 22 committed `mill_airport_map.html` files are published artifacts too — the 20
SI maps (`case1_10` … `case4_50`) are screen captures of them.

Regenerated output is numerically correct but not byte-identical, so the scripts
default to distinct names and `.gitignore` covers them:

- `make_tornado.py` writes `Results_Figures/tornado_regenerated.png`
- `run_create_maps.py` writes `mill_airport_map_regenerated.html` (`--output` to change)
- `make_emissions_figure.py` writes `Results_Figures/emissions_labeled_regenerated.png` (`--output` to change)

**Executing `SupplyChainSummary.ipynb` overwrites the live Figure 5** —
`ninepanelproductsummary_pos_v4.png` *and* `_v4.eps`, both of which are currently
byte-identical to the images the manuscript embeds. The notebooks take no arguments,
so there is no default to redirect, and unlike the scripts they have no
`_regenerated` fallback. Do not execute them in this working tree.

To re-execute safely, run them in a scratch directory with
the input data and `Case1`–`Case4` symlinked in, and copy back only the `.ipynb`:

```bash
W=/tmp/nbrun; mkdir -p $W/Results_Figures && cd $W
for f in *.xlsx gadm41_BRA_1.* supply_chain_distances.py; do ln -s "$OLDPWD/$f" .; done
for d in Case1 Case2 Case3 Case4 unconstrained_SAF mill_specific_incentives; do ln -s "$OLDPWD/$d" .; done
cp "$OLDPWD/SupplyChainSummary.ipynb" . && jupyter nbconvert --to notebook --execute --inplace SupplyChainSummary.ipynb
```

## Figure provenance

Every manuscript figure, and whether this repository can regenerate it end to end.
Several are composed in PowerPoint from generated panels, some are hand-drawn, and
the 20 SI maps are browser screen captures.

| Fig. | manuscript file | source | end to end? |
|---|---|---|---|
| 1 | `inputmaps_v4.png` | **composed** from `fourpanelinputdata.png` + `fourpanelinputdata_legend.png` (`SupplyChainMaps.ipynb`) | no — manual composition |
| 2 | `problemstatement.png` | **hand-drawn schematic**, no generating script | no — by design |
| 3 | `mill_pfd.png` | **hand-drawn schematic**, no generating script | no — by design |
| 4 | `ref_pfd.png` | **hand-drawn schematic**, no generating script | no — by design |
| 5 | `ninepanelproductsummary_pos_v4.eps` | `SupplyChainSummary.ipynb`, which now writes the `.eps` directly as well as the `.png`; both committed copies are byte-identical to the manuscript's | **yes**, but not bit-reproducible — see below |
| 6 | `emissions_v11.png` | `make_emissions_figure.py` | **yes**, bit-reproducible |
| 7 | `figure5_format.eps` | **composed** from `optimaldesignmap50.png` + `optimalsclocationszoom.png` + `optimaldesign_legend.png` (`SupplyChainMaps.ipynb`) | no — manual composition |
| 8 | `figure6_format.eps` | **composed** from `integercutlocations.png` + `integercutlocationszoom.png` (`integercutanalysis.ipynb`), plus the three red arrows | no — manual composition |
| 9 | `figure7_format.eps` | **composed** from `additionalSAFcost.png` + `unconstrained_SAF.png` (`SensitivtyAnalysis.ipynb`) | no — manual composition |
| 10 | `tornado.png` | `make_tornado.py`, which reads the ten `unconstrained_SAF/` CSVs | **yes** |
| TOC | `graphic_toc.png` | hand-made table-of-contents graphic | no — by design |
| S1–S20 | `case1_10.png` … `case4_50.png` | **screen captures** of the `mill_airport_map.html` files `run_create_maps.py` produces. The data is reproducible — the folium legend counts match Table 4 — but the pan, zoom, crop and legend state are manual | no — manual capture |
| S21 | `fourpanelcostsummary_v2.png` | `SupplyChainSummary.ipynb`, which writes `fourpanelcostsummary.png` — no `_v2` is produced by any script, and neither the notebook's output nor the committed `fourpanelcostsummary_v2.png` is byte-identical to the manuscript's | panels yes, the `_v2` edit manual |
| S22 | `incentivestudy.png` | `SensitivtyAnalysis.ipynb`, which writes it as `millspecficincentivestudy.png` — same figure, renamed on the way into the manuscript | **yes**, modulo the rename |

### Notes on Figure 6

Figure 6 used to be the worst case: `emissions_v6.png` was the notebook's contour
plot with two hand-added annotations — the dashed conversion upper bound at 0.65
and labels on the five literature points — and the labels were **reference
numbers**. Those numbers came from the old alphabetical bibliography style and
became silently wrong when the manuscript moved to citation-order numbering:
`[59] [12] [51] [50] [33]` should have read `[7] [63] [64] [65] [66]`.

`make_emissions_figure.py` now produces the whole figure, and the points are
labeled **A–E** instead, with the reference mapping in the manuscript caption and
in SI Table S2. That keeps the image independent of the bibliography. **Do not
reintroduce reference numbers into any figure.**

The current version is `emissions_v11.png`. Three changes since the figure was
scripted, in order: `v9` adopted the cited emission factors (ethanol 21.3, jet fuel
89), which moved the contour field itself; `v10` added ICAO's two CORSIA default
intensities; `v11` redrew those two as dashed **vertical lines** rather than point
markers, because CORSIA publishes an emissions intensity and no ethanol-to-jet
yield — a marker would have to pair ICAO's x-value with our y-value and imply they
report a conversion they do not. Run the script with no arguments to regenerate
safely; pass `--output` to write the versioned filename.

### Notes on Figure 5's EPS

The notebook writes `ninepanelproductsummary_pos_v4.eps` itself, so Figure 5 no
longer needs the hand conversion the `_v2` EPS required. It is **not** bit-comparable
across runs, though, for two reasons worth knowing before anyone diffs it:

- matplotlib stamps a `%%CreationDate` into the EPS header, so every run differs.
- the committed file was rendered under the earlier name `_v3.eps` and renamed in
  `f5f9571`, so its internal `%%Title` still reads `ninepanelproductsummary_pos_v3.eps`.
  A fresh run writes `_v4` in that field.

The `.png` has no such fields and is bit-reproducible. So verify Figure 5 by
comparing the PNG, and treat the EPS as reproducible-in-content only.

### Suffix conventions

A `_v2`/`_v4`/`_v6`/`_format` suffix on a manuscript filename indicates editing
outside the notebooks — with the exception of
`ninepanelproductsummary_pos_v4`, where the notebook now writes the `_v4` name
itself, and `emissions_v11.png`, which `make_emissions_figure.py` produces in full.
Figures 5, 6 and 10 can now be regenerated end to end; the rest still need a manual
step, which is a composition, capture or image-edit task rather than a code gap.

## Result folders

| folder | contents |
|---|---|
| `Case1` … `Case4` | `run_blend_and_opt_sensitivity.py` output, one subfolder per blend |
| `integer_cuts_case1`, `integer_cuts_case3` | `run_integer_cuts.py` output, one subfolder per cut iteration |
| `mill_specific_incentives` | one subfolder per SAF premium |
| `unconstrained_SAF/Case5` | Case 5 base premium sweep |
| `unconstrained_SAF/Case 5 {High,Low} {Sugar,Cost,Jet,Ethanol,Conv}` | the ten ±20% tornado scenarios |
| `Results_Figures` | generated panels *and* PowerPoint-composed figures — see the table above |
| `crc_job_scripts` | how the long runs were submitted (sanitized) |

`unconstrained_SAF/Case5/production.csv` predates the `premium` column the script
now writes; row *i* corresponds to premium *i* × 0.1 R$/L.

## Data files

| file | contents |
|---|---|
| `base_case_data_with_demands.xlsx` | all model input: distances, capacities, demands, prices, conversions, costs |
| `335MillsLatitudesLongitudes.xlsx` | mill coordinates, plus `ethanol` and `annexed` mill-type sheets |
| `AirportsLatitudeLongitude.xlsx` | airport coordinates |
| `OilRefineriesLatLong.xlsx` | refinery coordinates |
| `integer_cut_organized_data.xlsx` | integer-cut results consolidated for plotting. **Was assembled by hand**; `consolidate_integer_cuts.py` now derives it and `--verify` confirms the shipped copy is faithful. Its `Cut *` columns contain mojibake from a Latin-1/UTF-8 mix-up; the `SAF Mill` and `Percentage ` columns the notebook reads are correct. |
| `gadm41_BRA_1.shp/.shx/.dbf` | GADM Brazilian state boundaries for the map figures. No `.prj`, so the code sets EPSG:4326 explicitly. |

## Reproduction and audit notes

| document | contents |
|---|---|
| [REPRODUCE.md](REPRODUCE.md) | environment setup, how to run each study, portability notes |
| [PROVENANCE.md](PROVENANCE.md) | software versions, model statistics, MIP gaps, solve times, hardware |
| [RERUN_REPORT.md](RERUN_REPORT.md) | independent rerun of all 92 instances against the committed results |
| [RECONCILIATION.md](RECONCILIATION.md) | what the private repository added, and what remains unexplained |
| [MISSING_FILES.md](MISSING_FILES.md) | audit of every file, sheet and column the code references |
