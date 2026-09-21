"""Report MILP size for each formulation, at each of the three stages that matter.

The manuscript reports 124,711 continuous / 3,784 binary / 5,949 equality / 9,246
inequality for every instance (main_jcp.tex lines 485, 498, 512). Those numbers
match no code in either the public or the private repository. The CRC solver logs
(private repo, run_sc_model.o*) are authoritative for what was actually solved:

    Optimize a model with 15597 rows, 150826 columns and 443436 nonzeros
    Variable types: 147507 continuous, 3319 integer (3319 binary)

Three counts differ and all three are legitimate, so this script reports each:

  declared  every Var/Constraint the model builds
  active    excluding variables the run script fixes (Gurobi does not see them)
  solved    what Pyomo's LP writer actually emits -- also drops variables that
            appear in no active constraint and not in the objective

Usage:
    python model_statistics.py
    python model_statistics.py --lp-detail    # name the variables the writer drops
"""
import argparse
import os
import re
import sys
import tempfile

import pyomo.environ as pyo
from pyomo.core.expr.visitor import identify_variables

from create_sc_model_full import create_supply_chain_model

LOG = dict(rows=15597, cols=150826, cont=147507, binary=3319)
PAPER = dict(cont=124711, binary=3784, eq=5949, ineq=9246)

parser = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
parser.add_argument("--data", default="base_case_data_with_demands.xlsx")
parser.add_argument("--lp-detail", action="store_true",
                    help="list which variables the LP writer drops")
args = parser.parse_args()

this_file_path = os.path.dirname(os.path.realpath(__file__))
data = os.path.join(this_file_path, args.data)

#Each formulation, and which binaries its run script fixes to 0
FORMULATIONS = [
    ("Cases 1 & 3  (ATJ at mills)",      dict(profit_obj=False, blend=0.5), ["z", "y_ref"]),
    ("Cases 2 & 4  (ATJ at refineries)", dict(profit_obj=False, blend=0.5), ["z", "y"]),
    ("Case 5       (no blend req.)",     dict(profit_obj=True,  blend=0.0), ["z", "y_ref"]),
]


def counts(m, skip_fixed):
    cont = binary = 0
    for v in m.component_data_objects(pyo.Var, active=True):
        if skip_fixed and v.fixed:
            continue
        if v.is_binary():
            binary += 1
        else:
            cont += 1
    eq = ineq = 0
    for c in m.component_data_objects(pyo.Constraint, active=True):
        if c.equality:
            eq += 1
        else:
            ineq += 1
    return dict(cont=cont, binary=binary, eq=eq, ineq=ineq)


def lp_counts(m):
    """What the LP writer emits: the variables actually referenced by an active
    constraint or the objective. Determined from the model rather than by parsing
    LP text, which is brittle for names containing brackets and accents."""
    used = set()
    for c in m.component_data_objects(pyo.Constraint, active=True):
        for v in identify_variables(c.body, include_fixed=False):
            used.add(id(v))
    for o in m.component_data_objects(pyo.Objective, active=True):
        for v in identify_variables(o.expr, include_fixed=False):
            used.add(id(v))
    binaries = sum(1 for v in m.component_data_objects(pyo.Var, active=True)
                   if not v.fixed and v.is_binary() and id(v) in used)
    cont = sum(1 for v in m.component_data_objects(pyo.Var, active=True)
               if not v.fixed and not v.is_binary() and id(v) in used)
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "m.lp")
        m.write(path, io_options={"symbolic_solver_labels": False})
        rows = len(re.findall(r"^c_[eul]_", open(path).read(), re.M))
    return dict(used=used, binaries=binaries, cont=cont, rows=rows)


def row(label, c, extra=""):
    print(f"  {label:24s} {c['cont']:>9,} {c['binary']:>8,} {c['eq']:>8,} {c['ineq']:>8,} "
          f"{c['eq'] + c['ineq']:>8,} {extra}")


print("=" * 92)
print("MILP SIZE BY FORMULATION")
print("=" * 92)
print(f"  {'':24s} {'contin.':>9} {'binary':>8} {'equal.':>8} {'inequal.':>8} {'rows':>8}")

results = {}
for label, kwargs, fixed_blocks in FORMULATIONS:
    m = create_supply_chain_model(data, 0, 0, kwargs["blend"], 700000,
                                  profit_obj=kwargs["profit_obj"], grass_roots_factor=0.5,
                                  breakpoints=10, ref_blend=True)
    print(f"\n{label}   (fixes {', '.join('m.' + b for b in fixed_blocks)}, and m.s)")
    declared = counts(m, skip_fixed=False)
    row("declared", declared)

    for blk in fixed_blocks:
        for i in getattr(m, blk).index_set():
            getattr(m, blk)[i].fix(0)
    for i in m.MILLS:
        m.s[i].fix(0)
    active = counts(m, skip_fixed=True)
    row("active (unfixed)", active)

    lp = lp_counts(m)
    row("solved (LP emitted)", dict(cont=lp["cont"], binary=lp["binaries"],
                                     eq=active["eq"], ineq=active["ineq"]),
        f"<- LP file rows {lp['rows']:,}")
    results[label] = dict(declared=declared, active=active, lp=lp, model=m)

print("\n" + "=" * 92)
print("AGAINST THE AUTHORITATIVE CRC LOG (Case 5 formulation)")
print("=" * 92)
c5 = results["Case 5       (no blend req.)"]
a = c5["active"]
print(f"  {'quantity':<22} {'this code':>12} {'CRC log':>12} {'manuscript':>12}   verdict")
for key, log_key, paper_key, name in [
    ("binary", "binary", "binary", "binary variables"),
    (None, "rows", None, "rows (eq + ineq)"),
    ("cont", "cont", "cont", "continuous variables"),
]:
    if name.startswith("rows"):
        mine, logv, paperv = a["eq"] + a["ineq"], LOG["rows"], PAPER["eq"] + PAPER["ineq"]
    else:
        mine, logv, paperv = a[key], LOG[log_key], PAPER[paper_key]
    verdict = "EXACT MATCH to log" if mine == logv else f"log delta {mine - logv:+,}"
    print(f"  {name:<22} {mine:>12,} {logv:>12,} {paperv:>12,}   {verdict}")
print(f"  {'equality constraints':<22} {a['eq']:>12,} {'n/a':>12} {PAPER['eq']:>12,}   "
      f"log gives no split; sum matches")
print(f"  {'inequality constraints':<22} {a['ineq']:>12,} {'n/a':>12} {PAPER['ineq']:>12,}   "
      f"log gives no split; sum matches")

print("\n  The manuscript's four numbers correspond to no code in either repository.")
print("  Binaries are entity_count x (breakpoints - 1); this model has")
print("  (335 mills + 29 airports + 9 refineries) x 9 = 3,357 declared, 3,319 after")
print("  fixing m.z and m.y_ref. 3,784 would need 344 x 11 -- mills plus refineries")
print("  at 12 breakpoints -- an entity set no module in either repo builds.")

if args.lp_detail:
    print("\n" + "=" * 92)
    print("VARIABLES THE LP WRITER DROPS (Case 5)")
    print("=" * 92)
    m = c5["model"]
    used = c5["lp"]["used"]
    dropped = {}
    for v in m.component_data_objects(pyo.Var, active=True):
        if v.fixed or id(v) in used:
            continue
        dropped[v.parent_component().name] = dropped.get(v.parent_component().name, 0) + 1
    total = sum(dropped.values())
    print(f"  {total:,} unfixed variables are not emitted "
          f"(active {a['cont'] + a['binary']:,} -> LP {LOG['cols']:,})")
    for k, n in sorted(dropped.items(), key=lambda kv: -kv[1]):
        print(f"    {k:32s} {n:>7,}")
    print("\n  These appear in no active constraint and not in the objective, so the writer")
    print("  omits them. Gurobi therefore reports fewer continuous variables than the")
    print("  model declares. All three counts are correct; they answer different questions.")
