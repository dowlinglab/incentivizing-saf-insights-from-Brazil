"""Build the tornado diagram (manuscript Figure 10) from the Case 5 scenario CSVs.

The original plot hard-coded the ten threshold premiums in a DataFrame. This reads
them from unconstrained_SAF/Case 5 {High,Low} {Sugar,Cost,Jet,Ethanol,Conv}/
production.csv, so the figure cannot drift from the data behind it.

The recommended premium for a scenario is the smallest premium at which voluntary
SAF production reaches 50% of jet fuel demand -- which is exactly the SAF volume
the mandated 50% blend produces, read from the committed Case 1 results so the
definition is fixed rather than restated.

    python make_tornado.py                  # -> Results_Figures/tornado_regenerated.png
    python make_tornado.py --print-only     # thresholds, no figure

Writes tornado_regenerated.png, not tornado.png. The committed tornado.png is the
published artefact and is byte-identical to the manuscript's images/tornado.png;
overwriting it breaks that provenance link for no gain, since the regenerated figure
is visually identical and numerically correct but differs byte-wise.
"""
import argparse
import os

import matplotlib
import pandas as pd

#Row order and labels as published
ROWS = [
    ("Sugar",   "Sugar Price\n(R\\$ t$^{-1}$)"),
    ("Cost",    "ATJ OPEX\n(R\\$ m$^{-3}$)"),
    ("Jet",     "Jet Fuel Price\n(R\\$ m$^{-3}$)"),
    ("Ethanol", "Ethanol Price\n(R\\$ m$^{-3}$)"),
    ("Conv",    "ATJ Conversion\n(m$^3$ SAF m$^{-3}$ ethanol)"),
]

parser = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
parser.add_argument("--results-dir", default="unconstrained_SAF")
#Default deliberately NOT Results_Figures/tornado.png: that file is the published
#artefact and is byte-identical to the manuscript's images/tornado.png and to the
#private repository's copy. That three-way identity is what establishes Figure 10's
#provenance, and a regenerated figure -- numerically correct but not byte-identical --
#would silently break it. Pass --out explicitly to overwrite it.
parser.add_argument("--out",
                    default=os.path.join("Results_Figures", "tornado_regenerated.png"),
                    help="output path (default: Results_Figures/tornado_regenerated.png; "
                         "tornado.png is the published artefact -- do not overwrite it)")
parser.add_argument("--print-only", action="store_true")
args = parser.parse_args()

this_file_path = os.path.dirname(os.path.realpath(__file__))
root = os.path.join(this_file_path, args.results_dir)


def threshold_volume():
    base = os.path.join(this_file_path, "Case1", "interest_mid_blend_50")
    return (pd.read_csv(os.path.join(base, "key_results_mills.csv"))["SAF"].sum()
            + pd.read_csv(os.path.join(base, "key_results_ref.csv"))["SAF"].sum())


def threshold(folder, target):
    """Smallest premium (R$/L) at which SAF production reaches `target` m3."""
    path = os.path.join(root, folder, "production.csv")
    if not os.path.exists(path):
        raise SystemExit(f"missing {path}")
    df = pd.read_csv(path)
    #The base Case5 file predates the `premium` column; row i is premium i x 0.1
    premium = df["premium"] if "premium" in df.columns else df.index * 0.1
    hit = premium[df["SAF Production"] >= target]
    if not len(hit):
        raise SystemExit(f"{folder}: target never reached")
    return round(float(hit.min()), 1)


target = threshold_volume()
base = threshold("Case5", target)
print(f"threshold volume (50% blend SAF): {target:,.0f} m3")
print(f"base case recommended premium   : {base} R$/L\n")
print(f"{'parameter':<10} {'-20%':>7} {'base':>7} {'+20%':>7}   swing")
data = []
for key, label in ROWS:
    low = threshold(f"Case 5 Low {key}", target)
    high = threshold(f"Case 5 High {key}", target)
    data.append((label, low, high))
    print(f"{key:<10} {low:>7.1f} {base:>7.1f} {high:>7.1f}   {abs(high - low):.1f}")

if args.print_only:
    raise SystemExit(0)

matplotlib.use("Agg")
import matplotlib.pyplot as plt

df = pd.DataFrame({"Variable": [d[0] for d in data],
                   "Low": [d[1] for d in data],
                   "High": [d[2] for d in data]})
df["Base"] = base
df["LowDev"] = df["Low"] - df["Base"]
df["HighDev"] = df["High"] - df["Base"]

fig, ax = plt.subplots(figsize=(8, 4))
low_bars = ax.barh(df["Variable"], df["LowDev"], left=base,
                   color="lightblue", label="Low (-20%)")
high_bars = ax.barh(df["Variable"], df["HighDev"], left=base,
                    color="lightcoral", label="High (+20%)")
ax.bar_label(low_bars, labels=[f"{x:.1f}" for x in df["Low"]],
             label_type="edge", padding=3, fontweight="bold")
ax.bar_label(high_bars, labels=[f"{x:.1f}" for x in df["High"]],
             label_type="edge", padding=3, fontweight="bold")
ax.axvline(base, color="black")
ax.set_xlabel(r"Recommended SAF Premium (R\$ L$^{-1}$)", fontsize=14, fontweight="bold")
ax.legend(fontsize=12)
ax.set_yticks(range(len(df)))
ax.set_yticklabels(df["Variable"], fontsize=12, fontweight="bold")
lo = min(df["Low"].min(), df["High"].min()) - 0.3
hi = max(df["Low"].max(), df["High"].max()) + 0.3
ax.set_xlim(left=lo, right=hi)
ax.text(base - 0.15, -0.067, f"{base:.1f}", fontweight="bold")
plt.tight_layout()
out = args.out if os.path.isabs(args.out) else os.path.join(this_file_path, args.out)
plt.savefig(out, bbox_inches="tight", dpi=500)
print(f"\nwrote {out}")
