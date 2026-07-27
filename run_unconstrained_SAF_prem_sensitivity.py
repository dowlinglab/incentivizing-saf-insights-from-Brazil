"""Case 5: SAF premium sensitivity with no mandated SAF blend requirement.

Takes the investor perspective (maximize total mill profits) with no lower or
upper bound on SAF production, and sweeps the SAF premium price to find the
minimum premium at which SAF production becomes voluntarily attractive.

Results are written to unconstrained_SAF/Case5/production.csv.

Examples:
    python run_unconstrained_SAF_prem_sensitivity.py
    python run_unconstrained_SAF_prem_sensitivity.py --premiums 0 1 2 3 4 --quiet
"""
import argparse
import os

import numpy as np
import pandas as pd

from create_sc_model_full import *

parser = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
parser.add_argument("--premiums", type=float, nargs="+", default=None,
                    help="SAF premium prices to sweep, R$/L "
                         "(default: 0 to 4 in 41 steps)")
parser.add_argument("--results-dir", default="unconstrained_SAF",
                    help="output folder name (default: unconstrained_SAF)")
parser.add_argument("--data", default="base_case_data_with_demands.xlsx",
                    help="input data workbook")
parser.add_argument("--eth-premium", type=float, default=0,
                    help="ethanol premium price, R$/m3 ethanol (default: 0)")
parser.add_argument("--max-saf-capacity", type=float, default=700000,
                    help="maximum ATJ capacity per site, m3 ethanol (default: 700000)")
parser.add_argument("--mip-gap", type=float, default=0.0005,
                    help="Gurobi MIPGap; looser than elsewhere because the exact "
                         "SAF investment locations do not matter here (default: 0.0005)")
parser.add_argument("--quiet", action="store_true", help="suppress the solver log")
args = parser.parse_args()

#Resolve paths relative to this script so the run works from any directory
this_file_path = os.path.dirname(os.path.realpath(__file__))

#Specify Input Data
data = args.data if os.path.isabs(args.data) else os.path.join(this_file_path, args.data)

# create a directory to save results
results_dir1 = os.path.join(this_file_path, args.results_dir)
results_dir = os.path.join(results_dir1, "Case5")
os.makedirs(results_dir, exist_ok=True)

#Create supply chain model - Case 5, upgrading at mills only, blend at refinery or
#airport, maximize mill profits. blend = 0 relaxes the SAF blend requirement.
m = create_supply_chain_model(data, 0, args.eth_premium, 0, args.max_saf_capacity,
                              profit_obj = True, grass_roots_factor=0.5,
                              breakpoints=10, ref_blend=True)

#Fix to no SAF capacity at all airports
for i in m.AIRPORTS:
    m.z[i].fix(0)

#Fix to no SAF capacity at all refineries
for i in m.REFINERIES:
   m.y_ref[i].fix(0)

#Fix mill-specific incentives to 0
for i in m.MILLS:
    m.s[i].fix(0)


prem_range = np.linspace(0,4,41) if args.premiums is None else args.premiums
result = {}
result['SAF Production'] = []
result['eth market'] = []
result['Total Cost'] = []
result['Total Profit'] = []
result['premium'] = []

solver = pyo.SolverFactory('gurobi')
solver.options['MIPGap'] = args.mip_gap

#loop through the premium range
for j in prem_range:

    #Specify SAF Premium Parameter
    m.saf_premium = j*1000 #Convert from $R/l to $R/m3

    print("=== SAF premium " + str(j) + " R$/L", flush=True)
    results = solver.solve(m, tee=not args.quiet)

    #Sum the total SAF production
    saf = 0
    eth = 0
    for i in m.MILLS:
        saf = saf + pyo.value(m.x[i,'saf'])
        eth = eth + pyo.value(m.x[i,'etmk'])
    for i in m.REFINERIES:
        saf = saf + pyo.value(m.x_ref[i,'saf'])

    result['SAF Production'].append(saf)
    result['eth market'].append(eth)
    result['Total Cost'].append(pyo.value(m.sc_cost_expression))
    result['Total Profit'].append(pyo.value(m.profit_expression))
    result['premium'].append(j)
    


results_df = pd.DataFrame.from_dict(result)
results_df.to_csv(os.path.join(results_dir, 'production.csv'))


