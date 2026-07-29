"""Regenerate the tornado-diagram scenarios: Case 5 under +/-20% parameter changes.

The manuscript varies five quantities by +/-20% and reports, for each, the minimum
SAF premium at which voluntary SAF production reaches 50% of jet fuel demand
(Figure 10). Those ten runs were originally produced by editing the input workbook
by hand between runs; this script applies the perturbation programmatically.

Parameter mapping, verified by reproducing all ten published thresholds from the
committed CSVs:

  sugar     prices sheet, product 'sug', price column   2942.42 R$/t
  ethanol   prices sheet, product 'et',  price column   2284.88 R$/m3
  jet       prices sheet, product 'saf', price column   4129.45 R$/m3
            (SAF sells at the conventional jet fuel price plus the premium)
  cost      prices sheet, product 'saf', cost column     870.00 R$/m3  ("ATJ OPEX")
  conv      conversions sheet, code 'et_to_saf'            0.410 m3 SAF / m3 ethanol

Output folders match the published naming, e.g. "Case 5 High Jet".

    # one scenario, full 41-point sweep
    python run_tornado_sensitivity.py --parameter jet --multiplier 1.2

    # threshold only, by bisection -- about 6 solves instead of 41
    python run_tornado_sensitivity.py --parameter jet --multiplier 1.2 --bisect

    # all ten scenarios by bisection
    python run_tornado_sensitivity.py --all --bisect

A full sweep writes production.csv into the published folders, overwriting them.
Pass --results-dir to regenerate side by side instead.

A full sweep of all ten scenarios is expensive: the base Case 5 sweep alone took
1 h 51 min on an M1 Max, because premiums above the threshold are the hard ones.
Prefer --bisect unless the whole production curve is needed.
"""
import argparse
import os
import tempfile

import numpy as np
import pandas as pd

from create_sc_model_full import *

#Parameter name -> (sheet, row key, column). Verified against the ten published
#thresholds; see the module docstring.
PARAMETERS = {
    "sugar":   ("prices", "sug", "price"),
    "ethanol": ("prices", "et", "price"),
    "jet":     ("prices", "saf", "price"),
    "cost":    ("prices", "saf", "cost"),
    "conv":    ("conversions", "et_to_saf", "rate"),
}
#Folder-name fragment used by the published results
LABEL = {"sugar": "Sugar", "ethanol": "Ethanol", "jet": "Jet", "cost": "Cost", "conv": "Conv"}

parser = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
parser.add_argument("--parameter", choices=sorted(PARAMETERS),
                    help="quantity to perturb")
parser.add_argument("--multiplier", type=float,
                    help="scale factor, e.g. 0.8 for -20%% or 1.2 for +20%%")
parser.add_argument("--all", action="store_true",
                    help="run all five parameters at 0.8 and 1.2")
parser.add_argument("--bisect", action="store_true",
                    help="find the threshold premium by bisection instead of sweeping")
parser.add_argument("--premiums", type=float, nargs="+", default=None,
                    help="premiums to sweep, R$/L (default: 0 to 4 in 41 steps)")
parser.add_argument("--tolerance", type=float, default=0.1,
                    help="bisection resolution in R$/L (default: 0.1, the sweep step)")
parser.add_argument("--results-dir", default="unconstrained_SAF")
parser.add_argument("--data", default="base_case_data_with_demands.xlsx")
parser.add_argument("--max-saf-capacity", type=float, default=700000)
parser.add_argument("--mip-gap", type=float, default=0.0005)
parser.add_argument("--quiet", action="store_true")
args = parser.parse_args()

if not args.all and (args.parameter is None or args.multiplier is None):
    parser.error("give --parameter and --multiplier, or --all")

this_file_path = os.path.dirname(os.path.realpath(__file__))
data = args.data if os.path.isabs(args.data) else os.path.join(this_file_path, args.data)
results_dir1 = os.path.join(this_file_path, args.results_dir)


def perturbed_workbook(parameter, multiplier, dest):
    """Write a copy of the workbook with one quantity scaled. Every sheet is
    round-tripped so the model reads an otherwise identical file."""
    sheet, key, column = PARAMETERS[parameter]
    sheets = pd.read_excel(data, sheet_name=None)
    df = sheets[sheet]
    keycol = "product" if sheet == "prices" else "conversion_codes"
    mask = df[keycol] == key
    if not mask.any():
        raise SystemExit(f"{key!r} not found in sheet {sheet!r}")
    before = df.loc[mask, column].iloc[0]
    df.loc[mask, column] = before * multiplier
    print(f"  {sheet}.{key}.{column}: {before:g} -> {before * multiplier:g} "
          f"({multiplier:+.0%} of base)".replace("+1", "1"), flush=True)
    with pd.ExcelWriter(dest, engine="openpyxl") as writer:
        for name, frame in sheets.items():
            frame.to_excel(writer, sheet_name=name, index=False)
    return dest


def build(workbook):
    m = create_supply_chain_model(workbook, 0, 0, 0, args.max_saf_capacity,
                                  profit_obj=True, grass_roots_factor=0.5,
                                  breakpoints=10, ref_blend=True)
    for i in m.AIRPORTS:
        m.z[i].fix(0)
    for i in m.REFINERIES:
        m.y_ref[i].fix(0)
    for i in m.MILLS:
        m.s[i].fix(0)
    return m


def total_saf(m):
    return (sum(pyo.value(m.x[i, 'saf']) for i in m.MILLS)
            + sum(pyo.value(m.x_ref[i, 'saf']) for i in m.REFINERIES))


def solve_at(m, solver, premium_per_litre):
    m.saf_premium = premium_per_litre * 1000   # R$/L -> R$/m3
    solver.solve(m, tee=not args.quiet)
    return total_saf(m)


#The threshold volume: SAF equal to 50% of jet fuel demand, which is exactly what
#the mandated 50% blend produces. Read from the committed Case 1 results so the
#definition cannot drift.
def threshold_volume():
    base = os.path.join(this_file_path, "Case1", "interest_mid_blend_50")
    mills = pd.read_csv(os.path.join(base, "key_results_mills.csv"))["SAF"].sum()
    refs = pd.read_csv(os.path.join(base, "key_results_ref.csv"))["SAF"].sum()
    return mills + refs


def run_scenario(parameter, multiplier):
    tag = f"{'High' if multiplier > 1 else 'Low'} {LABEL[parameter]}"
    out = os.path.join(results_dir1, f"Case 5 {tag}")
    os.makedirs(out, exist_ok=True)
    print(f"\n=== Case 5 {tag}", flush=True)
    #Keep the perturbed workbook out of the results folder so a --bisect run leaves
    #the published CSVs untouched.
    tmp = tempfile.mkdtemp(prefix="saf_perturbed_")
    workbook = perturbed_workbook(parameter, multiplier,
                                  os.path.join(tmp, "perturbed_input.xlsx"))
    m = build(workbook)
    solver = pyo.SolverFactory('gurobi')
    solver.options['MIPGap'] = args.mip_gap
    target = threshold_volume()

    if args.bisect:
        lo, hi = 0.0, 4.0
        if solve_at(m, solver, hi) < target:
            print(f"  threshold not reached by {hi} R$/L", flush=True)
            return tag, float("nan")
        while hi - lo > args.tolerance + 1e-9:
            mid = round((lo + hi) / 2, 4)
            reached = solve_at(m, solver, mid) >= target
            print(f"  premium {mid:.3f} R$/L -> "
                  f"{'reaches' if reached else 'below'} target", flush=True)
            lo, hi = (lo, mid) if reached else (mid, hi)
        thresh = round(hi, 1)
        print(f"  threshold: {thresh} R$/L", flush=True)
        return tag, thresh

    prem_range = np.linspace(0, 4, 41) if args.premiums is None else args.premiums
    result = {k: [] for k in
              ['SAF Production', 'eth market', 'Total Cost', 'Total Profit', 'premium']}
    for j in prem_range:
        saf = solve_at(m, solver, j)
        result['SAF Production'].append(saf)
        result['eth market'].append(sum(pyo.value(m.x[i, 'etmk']) for i in m.MILLS))
        result['Total Cost'].append(pyo.value(m.sc_cost_expression))
        result['Total Profit'].append(pyo.value(m.profit_expression))
        result['premium'].append(j)
        print(f"  premium {j:.1f} R$/L -> SAF {saf:,.0f} m3", flush=True)
    df = pd.DataFrame.from_dict(result)
    df.to_csv(os.path.join(out, "production.csv"))
    hit = df.loc[df['SAF Production'] >= target, 'premium']
    thresh = round(hit.min(), 1) if len(hit) else float("nan")
    print(f"  threshold: {thresh} R$/L", flush=True)
    return tag, thresh


scenarios = ([(p, mult) for p in sorted(PARAMETERS) for mult in (0.8, 1.2)]
             if args.all else [(args.parameter, args.multiplier)])

print(f"threshold volume (50% blend SAF): {threshold_volume():,.0f} m3")
found = [run_scenario(p, mult) for p, mult in scenarios]

print("\n" + "=" * 52)
print("RECOMMENDED SAF PREMIUM (R$/L)")
print("=" * 52)
for tag, thresh in found:
    print(f"  {tag:<18} {thresh}")
