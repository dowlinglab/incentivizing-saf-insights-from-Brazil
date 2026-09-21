"""Build integer_cut_organized_data.xlsx from the raw integer-cut results.

integercutanalysis.ipynb reads that spreadsheet, but nothing generated it -- it was
consolidated by hand from integer_cuts_case1/ and integer_cuts_case3/. This script
derives it, so the integer-cut figures can be regenerated from a fresh run.

Layout matches the hand-built file: one sheet per case, columns

    SAF Mill      each mill selected in at least one cut iteration
    Percentage    share of the ten iterations that selected it, as a percentage
    Cut 0 .. Cut 9   the mills selected in each iteration (ragged columns)

Two notes on the existing file. Its `Percentage ` column has a trailing space,
which the notebook relies on, so that is preserved. Its `Cut *` columns contain
mojibake ("Central Olho D'Ãgua", "BIOSEV - Unidade Vale do RosÃ¡rio") from UTF-8
text pasted as Latin-1; the generated file writes them correctly. The `SAF Mill`
and `Percentage ` columns -- the only ones the notebook reads -- are byte-for-byte
reproducible, which `--verify` checks.

    python consolidate_integer_cuts.py --verify        # against the shipped file
    python consolidate_integer_cuts.py --out new.xlsx
    python consolidate_integer_cuts.py --results DIR   # from a rerun tree
"""
import argparse
import os

import pandas as pd

CASES = {1: "Case 1 50%", 3: "Case 3 50%"}
THRESHOLD = 1e-6

parser = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
parser.add_argument("--results", default=None,
                   help="tree holding integer_cuts_case1/ and _case3/ (default: here)")
parser.add_argument("--blend", type=int, default=50, help="blend percentage (default: 50)")
parser.add_argument("--iterations", type=int, default=10)
parser.add_argument("--out", default=None, help="output workbook (default: print only)")
parser.add_argument("--verify", action="store_true",
                    help="compare against the shipped integer_cut_organized_data.xlsx")
args = parser.parse_args()

this_file_path = os.path.dirname(os.path.realpath(__file__))
root = args.results or this_file_path


def selected_per_cut(case):
    """The mills selected in each cut iteration, in solver order."""
    out = []
    for it in range(args.iterations):
        f = os.path.join(root, f"integer_cuts_case{case}", str(args.blend),
                         f"int_cuts{it}", "key_results_mills.csv")
        if not os.path.exists(f):
            raise SystemExit(f"missing {f}")
        d = pd.read_csv(f)
        out.append(sorted(d.loc[d["SAF"] > THRESHOLD, "mills"].tolist()))
    return out


def sheet_for(case):
    cuts = selected_per_cut(case)
    counts = {}
    for chosen in cuts:
        for mill in chosen:
            counts[mill] = counts.get(mill, 0) + 1
    n = len(cuts)
    #Ascending by frequency, matching the hand-built file's ordering
    mills = sorted(counts, key=lambda k: (counts[k], k))
    frame = pd.DataFrame({
        "SAF Mill": mills,
        "Percentage ": [round(100 * counts[k] / n) for k in mills],
    })
    height = max(len(mills), max(len(c) for c in cuts))
    frame = frame.reindex(range(height))
    for it, chosen in enumerate(cuts):
        frame[f"Cut {it}"] = pd.Series(chosen).reindex(range(height))
    return frame, counts, n


sheets = {}
for case, name in CASES.items():
    frame, counts, n = sheet_for(case)
    sheets[name] = frame
    print(f"=== {name}: {len(counts)} distinct mills over {n} iterations")
    for mill in sorted(counts, key=lambda k: (-counts[k], k)):
        print(f"    {str(mill)[:44]:44s} {100 * counts[mill] / n:>5.0f}%")

if args.verify:
    shipped = os.path.join(this_file_path, "integer_cut_organized_data.xlsx")
    print(f"\n=== verifying against {os.path.basename(shipped)}")
    ok = True
    for name, frame in sheets.items():
        ref = pd.read_excel(shipped, sheet_name=name)
        mine = dict(zip(frame["SAF Mill"].dropna(), frame["Percentage "].dropna()))
        theirs = dict(zip(ref["SAF Mill"].dropna(), ref["Percentage "].dropna()))
        missing = set(theirs) - set(mine)
        extra = set(mine) - set(theirs)
        differing = {k: (theirs[k], mine[k]) for k in set(mine) & set(theirs)
                     if int(theirs[k]) != int(mine[k])}
        status = "MATCH" if not (missing or extra or differing) else "DIFFERS"
        print(f"  {name}: {status}  ({len(theirs)} mills in shipped, {len(mine)} generated)")
        for k in sorted(missing):
            print(f"    only in shipped : {k} ({theirs[k]}%)")
        for k in sorted(extra):
            print(f"    only in generated: {k} ({mine[k]}%)")
        for k, (t, m) in sorted(differing.items()):
            print(f"    percentage differs: {k} shipped {t}% generated {m}%")
        ok = ok and status == "MATCH"
    print("\n  " + ("the shipped spreadsheet is faithful to the raw cut results"
                    if ok else "the shipped spreadsheet does NOT match the raw results"))

if args.out:
    out = args.out if os.path.isabs(args.out) else os.path.join(this_file_path, args.out)
    with pd.ExcelWriter(out, engine="openpyxl") as writer:
        for name, frame in sheets.items():
            frame.to_excel(writer, sheet_name=name, index=False)
    print(f"\nwrote {out}")
