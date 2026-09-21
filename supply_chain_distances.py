"""Mass-distance (Mt.km) transported in each supply chain stage.

Replaces the calculation in SupplyChainSummary.ipynb cell 10, which computed
(sum of distances) x (sum of volumes) x density instead of sum(volume x distance)
x density. Those agree only if every flow travels the same distance, so the
notebook's numbers are inflated by roughly the number of active links -- Case 1
Stage 2 came out as 22,529 Mt.km against 316 published.

Stage naming follows the manuscript:

  stage 0   mill -> mill      ethanol moved between mills
  stage 1   mill -> refinery  ethanol (ATJ at refineries) or SAF (ATJ at mills)
  stage 2   refinery -> airport   blended SAF

Manuscript Table 4 reports only "Stage 1" and "Stage 2". Its Stage 1 appears to
include the mill -> mill leg; see `table4_conventions` and the CLI output, which
reports every candidate convention so the published numbers can be checked.

    python supply_chain_distances.py                 # Table 4, both conventions
    python supply_chain_distances.py --results DIR   # against a rerun tree
    python supply_chain_distances.py --self-test     # unit tests, no data needed
"""
import argparse
import os

import pandas as pd

ETHANOL_DENSITY = 789.0   # kg/m3
SAF_DENSITY = 800.0       # kg/m3
#m3 x kg/m3 = kg; /1000 -> tonne; /1e6 -> Mt
KG_TO_MT = 1.0 / 1000.0 / 1_000_000.0


def mass_distance(volumes, distances, density, threshold=0.5):
    """Sum over links of volume x distance x density, in Mt.km.

    volumes   DataFrame; column = origin label, row position = destination index
    distances DataFrame indexed the same way as volumes (see resolve_* helpers)
    density   kg/m3 of the material moved
    threshold m3 below which a link is treated as inactive, matching the
              >0.5 filter the original notebook used

    Both frames must already be aligned so that volumes[o][d] pairs with
    distances[o][d]. Use the helpers below rather than aligning by hand.
    """
    total = 0.0
    for origin in volumes.columns:
        vcol = volumes[origin]
        dcol = distances[origin]
        for d in range(len(vcol)):
            v = vcol.iloc[d]
            if v > threshold:
                total += v * dcol.iloc[d]
    return total * density * KG_TO_MT


def mill_to_mill(results_dir, workbook, halve=False):
    """Stage 0. `halve` reproduces the original notebook's assumption that the
    flow matrix is symmetric and each shipment is therefore counted twice. It is
    not symmetric -- vol_eth_sold[i,j] and [j,i] are independent variables -- so
    the default is False."""
    vol = pd.read_csv(os.path.join(results_dir, "mill_to_mill_volumes.csv"))
    mills = vol["volumes"].tolist()
    dist = pd.read_excel(workbook, sheet_name="mill_distances")
    v = vol[mills]
    d = dist[mills]
    total = mass_distance(v, d, ETHANOL_DENSITY)
    return total / 2 if halve else total


def mill_to_refinery(results_dir, workbook, at_refineries):
    """Stage 1. Ethanol moves if ATJ capacity is at refineries, SAF if at mills."""
    fname = "mill_to_ref_vol_eth.csv" if at_refineries else "mill_to_ref_vol_saf.csv"
    vol = pd.read_csv(os.path.join(results_dir, fname))
    refs = vol["volumes"].tolist()
    mills = [c for c in vol.columns if c not in ("Unnamed: 0", "volumes")]
    dist = pd.read_excel(workbook, sheet_name="mill_ref_distances")
    # volumes: column = mill, row = refinery.  distances: column = refinery, row = mill.
    v = vol[mills]
    d = pd.DataFrame({mill: [dist[r].iloc[i] for r in refs] for i, mill in enumerate(mills)})
    density = ETHANOL_DENSITY if at_refineries else SAF_DENSITY
    return mass_distance(v, d, density)


def refinery_to_airport(results_dir, workbook):
    """Stage 2. Blended SAF from refineries to airports."""
    vol = pd.read_csv(os.path.join(results_dir, "ref_to_air_vol_saf.csv"))
    refs = [c for c in vol.columns if c not in ("Unnamed: 0", "volumes")]
    dist = pd.read_excel(workbook, sheet_name="ref_air_distances")
    v = vol[refs]
    d = dist[refs]
    return mass_distance(v, d, SAF_DENSITY)


def stages(results_dir, workbook, at_refineries):
    return dict(
        stage0=mill_to_mill(results_dir, workbook),
        stage0_halved=mill_to_mill(results_dir, workbook, halve=True),
        stage1=mill_to_refinery(results_dir, workbook, at_refineries),
        stage2=refinery_to_airport(results_dir, workbook),
    )


def table4_conventions(s):
    """Candidate readings of Table 4's Stage 1 column, since the manuscript
    reports two stages where the model has three legs."""
    return {
        "excl. mill->mill": (s["stage1"], s["stage2"]),
        "incl. mill->mill": (s["stage1"] + s["stage0"], s["stage2"]),
        "incl. half mill->mill": (s["stage1"] + s["stage0_halved"], s["stage2"]),
    }


PUBLISHED = {1: (455, 316, 771), 2: (608, 446, 1054),
             3: (237, 878, 1115), 4: (653, 1282, 1935)}


def self_test():
    """Two links, different distances -- the case where the old formula fails."""
    v = pd.DataFrame({"A": [10.0, 0.0], "B": [0.0, 5.0]})
    d = pd.DataFrame({"A": [100.0, 999.0], "B": [999.0, 200.0]})
    got = mass_distance(v, d, 1000.0)
    want = (10 * 100 + 5 * 200) * 1000.0 * KG_TO_MT
    assert abs(got - want) < 1e-12, (got, want)
    print(f"  correct formula          : {got:.6g} Mt.km  (expected {want:.6g})")

    old = (100 + 200) * (10 + 5) * 1000.0 * KG_TO_MT   # (sum d)(sum v)
    print(f"  notebook formula         : {old:.6g} Mt.km  <- inflated {old / got:.1f}x")
    assert old > got

    # threshold: a link below 0.5 m3 must not contribute
    v2 = pd.DataFrame({"A": [0.4]})
    d2 = pd.DataFrame({"A": [1000.0]})
    assert mass_distance(v2, d2, 1000.0) == 0.0
    print("  sub-threshold link ignored: ok")

    # a single link is the one case where both formulas agree
    v3 = pd.DataFrame({"A": [7.0]})
    d3 = pd.DataFrame({"A": [30.0]})
    assert abs(mass_distance(v3, d3, 1000.0) - 7 * 30 * 1000.0 * KG_TO_MT) < 1e-12
    print("  single link agrees        : ok")
    print("\nself-test passed")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--results", default=None,
                   help="tree holding Case1..Case4 (default: next to this script)")
    p.add_argument("--workbook", default=None, help="input data workbook")
    p.add_argument("--blend", type=int, default=50, help="blend percentage (default: 50)")
    p.add_argument("--self-test", action="store_true", help="run unit tests and exit")
    args = p.parse_args()

    if args.self_test:
        self_test()
        raise SystemExit(0)

    here = os.path.dirname(os.path.realpath(__file__))
    root = args.results or here
    workbook = args.workbook or os.path.join(here, "base_case_data_with_demands.xlsx")

    print(f"Mass-distance at a {args.blend}% SAF blend, from {root}\n")
    print(f"{'':6} {'stage 0':>10} {'stage 1':>10} {'stage 2':>10}   "
          f"{'stage0 halved':>13}")
    allstages = {}
    for case in [1, 2, 3, 4]:
        d = os.path.join(root, f"Case{case}", f"interest_mid_blend_{args.blend}")
        s = stages(d, workbook, at_refineries=case in (2, 4))
        allstages[case] = s
        print(f"Case {case} {s['stage0']:>10.1f} {s['stage1']:>10.1f} {s['stage2']:>10.1f}   "
              f"{s['stage0_halved']:>13.1f}")

    print("\nAgainst published Table 4 (Stage 1 / Stage 2 / Total):")
    for name in ["excl. mill->mill", "incl. mill->mill", "incl. half mill->mill"]:
        print(f"\n  convention: Stage 1 {name}")
        print(f"    {'':6} {'S1':>8} {'pub':>7} {'S2':>9} {'pub':>7} {'total':>9} {'pub':>7}")
        for case in [1, 2, 3, 4]:
            s1, s2 = table4_conventions(allstages[case])[name]
            p1, p2, pt = PUBLISHED[case]
            hit = lambda a, b: "*" if abs(a - b) / b < 0.02 else " "
            print(f"    Case {case} {s1:>8.1f}{hit(s1, p1)}{p1:>6} {s2:>9.1f}{hit(s2, p2)}{p2:>6} "
                  f"{s1 + s2:>9.1f}{hit(s1 + s2, pt)}{pt:>6}")
    print("\n  * marks agreement within 2%.")
