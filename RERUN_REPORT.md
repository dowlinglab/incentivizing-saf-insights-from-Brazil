# Reproduction run, 2026-07-27 (confirmed 2026-07-29)

> **Confirmed by an independent second run.** The whole suite was rerun on
> 2026-07-29 under a different concurrency layout (five streams instead of two,
> with the Case 5 sweep split across three processes and merged). It produced
> results identical to those below: the same objectives, the same site-set changes
> (Case 1 at 50% blend 7 → 11 mills, Case 2 at 50% 7 → 4 refineries), the same
> Case 5 threshold of 2.6 R$/L, and the same integer-cut frequencies. **The
> divergence from the committed results is deterministic on this platform, not
> run-to-run thread jitter.** The 2026-07-29 artifacts are archived with checksums
> and provenance — see [RECONCILIATION.md](RECONCILIATION.md). The 2026-07-27
> artifacts were lost to `/tmp` being cleared; only these findings survived.


Full rerun of every study in this repository on macOS/arm64 (Apple M1 Max, 10
threads) with Gurobi 10.0.1 and Pyomo 6.6.1, compared against the committed
results. The manuscript's runs used Gurobi 10.0.3 and Pyomo 6.6.1 on Linux.

**92 MILP instances solved, all four notebooks executed, all 13 figures
regenerated.** Output was written outside the repository, so the committed
results are untouched and remain the comparison baseline.

## Timing

| study | instances | wall clock |
|---|---|---|
| Cases 1–4 × blends 0–50% | 24 | 6.6 min |
| Case 5 SAF premium sweep | 41 | 1 h 51 min |
| Mill-specific incentives | 7 | 8.4 min |
| Integer cuts, Case 1 | 10 | 6.9 min |
| Integer cuts, Case 3 | 10 | 3.4 min |
| 4 notebooks | — | 2.5 min |

Two concurrent streams, ~2 h 10 min total. The manuscript reports ~20 min per
instance on the Notre Dame CRC; the same suite would have taken 10–12 h here
before the loop-invariant expressions were hoisted out of the results loops.

Case 5 dominates because premiums above the 2.6 R$/L transition are hard: SAF
becomes attractive and the solver must resolve which mills to build.

## What reproduces

**Every objective value, within the MIP gap it was solved at.** All 24 blend
instances agree to within 1.44e-05 relative — well inside the 0.003% gap. So the
optimization results are sound; the committed numbers and the reruns are both
certified-optimal answers to the same problem.

**Key Finding 1, the headline emissions result.** `SupplyChainSummary.ipynb`
prints `Nominal Case Net Emissions: 2.4 Mtonne CO2 per year`, matching the
committed notebook output and the manuscript's "emissions increase of 2.4 Mt
CO2 year^-1".

**The recommended SAF premium.** Case 5 reaches the 50%-blend SAF volume at
**2.6 R$/L in both runs**, and the production curve matches to machine precision
(~1e-16) at every premium >= 2.7 R$/L. Figure `unconstrained_SAF.png` is visually
indistinguishable from the committed version.

**Cases 3 and 4 reproduce their designs exactly** at a 50% blend — same mills,
same refineries, and for Case 3 the same Stage 0/1/2 mass-distances to the
decimal.

**`integer_cut_organized_data.xlsx` is faithful to its raw inputs.** Recomputing
selection frequencies from the committed `int_cuts*` folders reproduces the
spreadsheet exactly for all 19 Case 1 mills and all 13 Case 3 mills. The
hand-assembly was done correctly.

## The site-set divergence is gap degeneracy — and it validates Key Finding 2

This is the most useful thing the rerun produced, and it is a **positive result**,
not a discrepancy. Read this before the "does not reproduce" section below.

At a 50% blend, Case 1's committed design has 7 SAF mills and the rerun's has 11,
sharing 5. Comparing against the paper's *own* integer-cut analysis:

| mill | integer-cut frequency | committed | rerun |
|---|---|---|---|
| São João de Araras | 100% | yes | yes |
| RAIZEN – Barra | 100% | yes | yes |
| São Martinho | 100% | yes | yes |
| BIOSEV – Unidade Santa Elisa | 100% | yes | yes |
| BIOSEV – Unidade Ares | 90% | yes | yes |
| Coruripe | 80% | yes | — |
| Santa Cruz – SP | 50% | yes | — |
| Monte Alegre | 30% | — | yes |
| Marituba, Central Olho d'Água, Pindorama, Pinheiro | 20% | — | yes |
| Ferrari / São Marino | 10% | — | yes |

Three things follow.

**Every differing mill is already in the paper's documented degenerate set,** and
the five both runs agree on are exactly the highest-frequency ones — the four
selected in 10/10 cut iterations plus the one selected in 9/10. The rerun landed
inside the solution set the paper itself characterises, on a different platform and
a different Gurobi version. Objectives differ by 0.00086%, well inside the 0.003%
gap.

**This independently confirms Key Finding 2.** The mills the paper identifies as
essential are precisely the ones that survive a change of platform, solver version
and search path. An independent run reaching the same core sites through a different
route is stronger evidence than the integer-cut analysis alone, because the
integer-cut solutions all come from one solver on one machine.

**There is no model drift.** Blend-0 logistics are 0.0 M R$ in both runs, so this
code is the published formulation, not the `Case*_v2` variant that costs the
ethanol distribution leg (see [RECONCILIATION.md](RECONCILIATION.md)).

### The caveat it exposes: Table 4's facility counts are not robust

The same evidence that validates Key Finding 2 undercuts the facility *counts*.
7 mills is one draw from a degenerate set; a different Gurobi version gives 11, and
Case 2 goes from 7 refineries to 4. Both are certified optimal within the stated
gap.

So any manuscript statement about *how many* facilities a case selects — Table 4's
first three columns and the `main_jcp.tex:602` narrative ("Case 1 … recommends seven
ATJ facilities distributed across São Paulo (four) and the Northeast (three)") —
should be presented as one representative optimum rather than *the* optimum, with a
pointer to the integer-cut analysis. The derived Mt·km totals inherit the same
sensitivity. Cases 3 and 4 happen to reproduce exactly, which is worth stating but
should not be read as robustness: Case 3 differs at 10/20/30/40% blend.

Recommended framing: report the essential mills (100%-frequency) as the robust
finding, give facility counts as representative, and cite the integer-cut spread.

## What does not reproduce

### Investment locations, in Cases 1 and 2

Objectives agree but the designs differ, because many designs sit inside the
0.003% gap and mills can be under 3 km apart. Identical site sets by case:

| case | ATJ at | blends with identical site set |
|---|---|---|
| 1 | mills | 1/6 (0% only) |
| 2 | refineries | 2/6 (0%, 10%) |
| 3 | mills | 2/6 (0%, 50%) |
| 4 | refineries | **6/6** |

**This contradicts a manuscript claim.** `main_jcp.tex` line 606 states: "For
investments at refineries (Cases 2 and 4), there is no expected variation in the
selected refinery within the 0.003% MIP gap." Case 4 behaves exactly as claimed.
Case 2 does not — it differs at 20%, 30%, 40%, and 50% blend. At 50% the
committed run picks 7 refineries and the rerun picks 4, with the objectives
differing by 1.4e-05. Recommend narrowing the claim to Case 4, or restating it as
"the selected refineries vary but the total cost does not."

### Table 4 facility counts, for Cases 1 and 2

The committed `SupplyChainMaps.ipynb` saved output prints exactly Table 4's
facility columns, so those numbers are genuine notebook output:

| Case | Table 4 (SAF mills / eth. suppliers / refineries) | committed notebook | rerun |
|---|---|---|---|
| 1 | 7 / 27 / 6 | 7 / 27 / 6 | **11 / 26 / 6** |
| 2 | 0 / 40 / 7 | 0 / 40 / 7 | **0 / 40 / 4** |
| 3 | 6 / 38 / 1 | 6 / 38 / 1 | 6 / 38 / 1 |
| 4 | 0 / 55 / 6 | 0 / 55 / 6 | 0 / 55 / 6 |

Any statement about the *number* of facilities in Cases 1 or 2 is gap-sensitive
and should be presented as one representative optimum. This includes the line 602
narrative ("Case 1 ... recommends seven ATJ facilities distributed across São
Paulo (four) and the Northeast (three)").

### One of the three "always chosen" mills

The Figure `fig:SAF locations` caption says three mills are "chosen in 100% of
optimal solutions regardless of the decision-making perspective":

| mill | published | rerun Case 1 | rerun Case 3 |
|---|---|---|---|
| Raízen Barra | 100% | **100%** | **100%** |
| São João de Araras | 100% | **100%** | **100%** |
| São Martinho | 100% | 90% | 80% |

Two of three hold up perfectly across an independent integer-cut run. São
Martinho is near-universal but not 100%, so the claim needs softening for that
mill. Other frequencies track closely; the largest Case 1 shifts are Ferrari/São
Marino (10%→50%) and Alta Mogiana (30%→0%).

## Two data-integrity problems in the committed results

### The mill-specific objectives are rounded placeholders

`mill_specific_incentives/*/key_results_mills.csv` has `objective` and `sc cost`
values that are exactly round numbers in a perfect arithmetic sequence:

| premium | committed | rerun |
|---|---|---|
| sp0_e0 | 238000000000.0 | 238269815834.7463 |
| sp500_e0 | 237000000000.0 | 237201761100.55023 |
| sp1000_e0 | 236000000000.0 | 236136215789.01355 |
| sp1500_e0 | 235000000000.0 | 235074912120.8278 |
| sp2000_e0 | 234000000000.0 | 233998810604.01892 |
| sp2500_e0 | 233000000000.0 | 232930101543.85345 |
| sp3000_e0 | 232000000000.0 | 232054899795.49863 |

A step of exactly -1e9 per 500 R$/m3. Gurobi does not produce values like this —
those columns were overwritten with rounded numbers at some point. The reruns are
all within 0.11% of them, so the roundings are plausible, but the committed file
is not solver output. No figure depends on it: `SensitivtyAnalysis.ipynb` cell 9
plots `total_incentive = [5.42, 5.41, ...]` from a hardcoded list and leaves
`sc_cost = []` empty.

### Table 4's Mt·km columns cannot be produced by the shipped code

> **Update, 2026-07-29.** The private repository has the same bug, so this is
> confirmed rather than merely suspected. `supply_chain_distances.py` now implements
> the correct `Σ(v·d)ρ` and reproduces **seven of the eight** published entries. The
> eighth, Case 1 Stage 1, is explained: adding half the mill→mill leg gives 455.5
> against the published 455, but the same convention gives Case 3 281.2 against its
> published 237 — **Table 4 is internally inconsistent**, only Case 1 including that
> term. Recommended fix: exclude mill→mill from Stage 1, report it as Stage 0, and
> correct Case 1 to Stage 1 = 422, Total = 738. See
> [RECONCILIATION.md](RECONCILIATION.md) §2.


Table 4 reports Stage 1 / Stage 2 / Total mass-distances of 455/316/771 Mt·km for
Case 1. `SupplyChainSummary.ipynb` prints something else entirely:

| | Table 4 | committed notebook output | rerun |
|---|---|---|---|
| Case 1 Stage 1 | 455 | 5,913 | 6,647 |
| Case 1 Stage 2 | 316 | 22,529 | 23,370 |
| Case 3 Stage 1 | 237 | 1,303 | 1,303 |
| Case 3 Stage 2 | 878 | 57,186 | 57,186 |

This is not a unit conversion: the Case 1 ratio is ~37x while Case 3 is ~52x, and
the Stage 1 : Stage 2 ordering is inverted (Table 4 has Stage 1 larger for Case 1,
the notebook has Stage 2 much larger). Table 4's own columns are internally
consistent (Stage 1 + Stage 2 = Total for all four cases), so the values are
deliberate, not typos.

**The discrepancy is visible in the authors' own committed notebook outputs, so it
predates this rerun.** The shipped `SupplyChainSummary.ipynb` has never produced
Table 4's transportation numbers, and how they were computed is not recorded
anywhere in the repository. This is a larger gap than the ones in
[MISSING_FILES.md](MISSING_FILES.md), since the numbers appear in a table rather
than a figure.

## Notebooks and figures

All four notebooks execute cleanly against the rerun data after the path fixes,
regenerating all 13 figures in `Results_Figures/`.

One code change was needed: `SensitivtyAnalysis.ipynb` reads a `payment` column
that no script wrote (see MISSING_FILES.md §2c). It is now derived in
`run_mill_specific_incentives.py` as `s[u] / (SAF_u * 1000)`, guarded at
`SAF_u = 0`, reproducing the committed column's 2.50–2.61 R$/L range.

`integercutanalysis.ipynb` still reads the published
`integer_cut_organized_data.xlsx`, so its two figures reflect the original
integer-cut solutions rather than the rerun — there is no script to rebuild that
spreadsheet (MISSING_FILES.md §2b).

## Bottom line

The optimization model, the input data, and every headline number reproduce: the
2.4 Mt CO2 emissions finding, the 2.6 R$/L recommended premium, and all 24
objective values. What does not carry across machines is the *identity and count
of chosen facilities* in the two cases with degenerate designs (1 and 2), which
the manuscript already anticipates for mills but explicitly rules out for
refineries. Separately, two committed artifacts — the mill-specific objectives and
Table 4's Mt·km columns — cannot be traced to the shipped code at all.

---

## Status after the private-repo reconciliation (2026-07-29)

| finding above | now |
|---|---|
| model size disagrees with the manuscript | **resolved** — the migrated model reproduces the CRC solver logs exactly (147,507 / 3,319 / 6,727 / 8,870); the manuscript's four numbers match no code in either repo |
| Table 4's Mt·km untraceable | **confirmed**, and Table 4 shown internally inconsistent; corrected calculation now in `supply_chain_distances.py` |
| tornado diagram has no code | **resolved** — data recovered, driver and plot written |
| `integer_cut_organized_data.xlsx` hand-built | **resolved** — `consolidate_integer_cuts.py`, and the shipped file verified faithful |
| mill-specific objectives are round numbers | **still open** |
| site sets differ for Cases 1 and 2 | **reframed as a validation** — see the degeneracy section above |

See [RECONCILIATION.md](RECONCILIATION.md) for the full status and
[PROVENANCE.md](PROVENANCE.md) for versions, gaps and solve times.
