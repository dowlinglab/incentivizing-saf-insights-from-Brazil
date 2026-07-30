"""Generate an interactive folium map of an optimal supply chain design.

Reads the CSV results in <case folder>/<blend folder>/ and writes
mill_airport_map.html into that same folder.

Examples:
    python run_create_maps.py --case 1 --blend 0.5
    python run_create_maps.py --case-folder integer_cuts_case1/50 --blend-folder int_cuts0
"""
import argparse

from create_maps import *

parser = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
parser.add_argument("--case", type=int, choices=[1, 2, 3, 4], default=None,
                    help="case study number; shorthand for --case-folder Case<N>")
parser.add_argument("--blend", type=float, default=None,
                    help="blend requirement as a fraction; shorthand for "
                         "--blend-folder interest_mid_blend_<pct>")
parser.add_argument("--case-folder", default=None,
                    help="results folder the solution comes from (default: Case1)")
parser.add_argument("--output", default="mill_airport_map_regenerated.html",
                    help="output filename inside the results folder (default: \r\n                         mill_airport_map_regenerated.html; the committed\r\n                         mill_airport_map.html files are the published artefacts)")
parser.add_argument("--blend-folder", default=None,
                    help="blend subfolder the solution comes from "
                         "(default: interest_mid_blend_50)")
args = parser.parse_args()

case_folder = args.case_folder
if case_folder is None:
    case_folder = "Case" + str(args.case) if args.case is not None else "Case1"

blend_folder = args.blend_folder
if blend_folder is None:
    if args.blend is not None:
        blend_folder = "interest_mid_blend_" + str(int(round(args.blend * 100)))
    else:
        blend_folder = "interest_mid_blend_50"

create_model_map(case_folder, blend_folder, args.output)
