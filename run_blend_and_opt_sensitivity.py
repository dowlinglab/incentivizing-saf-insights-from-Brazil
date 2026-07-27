"""Blend requirement and decision-making paradigm sensitivity study.

Solves the supply chain model over a range of SAF blend requirements for one of
the four case studies in the manuscript:

  1  central planner (minimize total supply chain cost), ATJ capacity at mills
  2  central planner (minimize total supply chain cost), ATJ capacity at refineries
  3  investor (maximize total mill profits),             ATJ capacity at mills
  4  investor (maximize total mill profits),             ATJ capacity at refineries

Results are written to Case<N>/interest_mid_blend_<pct>/ next to this script.

Examples:
    python run_blend_and_opt_sensitivity.py --case 1
    python run_blend_and_opt_sensitivity.py --case 3 --blends 0 0.5
    python run_blend_and_opt_sensitivity.py --case 2 --results-dir Case2_rerun --quiet

To reproduce all 24 manuscript instances (bash/zsh):
    for c in 1 2 3 4; do python run_blend_and_opt_sensitivity.py --case $c; done
"""
import argparse
import os

import numpy as np
import pandas as pd

from create_sc_model_full import *

#Case study definitions: objective sense, and which supply chain stage may invest in ATJ
CASE_SETTINGS = {
    1: {"profit_obj": False, "invest_at": "mills"},
    2: {"profit_obj": False, "invest_at": "refineries"},
    3: {"profit_obj": True,  "invest_at": "mills"},
    4: {"profit_obj": True,  "invest_at": "refineries"},
}

parser = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
parser.add_argument("--case", type=int, choices=sorted(CASE_SETTINGS), required=True,
                    help="case study to run (1-4); see the description above")
parser.add_argument("--blends", type=float, nargs="+", default=[0, .1, .2, .3, .4, .5],
                    help="SAF blend requirements to solve, as fractions "
                         "(default: 0 0.1 0.2 0.3 0.4 0.5)")
parser.add_argument("--results-dir", default=None,
                    help="output folder name (default: Case<N>)")
parser.add_argument("--data", default="base_case_data_with_demands.xlsx",
                    help="input data workbook")
parser.add_argument("--saf-premium", type=float, default=0,
                    help="SAF premium price, R$/m3 SAF (default: 0)")
parser.add_argument("--eth-premium", type=float, default=0,
                    help="ethanol premium price, R$/m3 ethanol (default: 0)")
parser.add_argument("--max-saf-capacity", type=float, default=700000,
                    help="maximum ATJ capacity per site, m3 ethanol (default: 700000)")
parser.add_argument("--mip-gap", type=float, default=0.00003,
                    help="Gurobi MIPGap (default: 0.00003, i.e. 0.003%%)")
parser.add_argument("--quiet", action="store_true", help="suppress the solver log")
args = parser.parse_args()

case = CASE_SETTINGS[args.case]

#Resolve paths relative to this script so the run works from any directory
this_file_path = os.path.dirname(os.path.realpath(__file__))

#Specify Input Data
data = args.data if os.path.isabs(args.data) else os.path.join(this_file_path, args.data)

# create a directory to save results
results_dir1 = os.path.join(this_file_path, args.results_dir or "Case" + str(args.case))
os.makedirs(results_dir1, exist_ok=True)

#Create supply chain model; profit_obj = True maximizes mill profits (Cases 3 and 4),
#profit_obj = False minimizes total supply chain cost (Cases 1 and 2). The blend
#requirement is initialized to 0 and set per iteration below.
m = create_supply_chain_model(data, args.saf_premium, args.eth_premium, 0,
                              args.max_saf_capacity, profit_obj = case["profit_obj"],
                              grass_roots_factor=0.5, breakpoints=10, ref_blend=True)

solver = pyo.SolverFactory('gurobi')
solver.options['MIPGap'] = args.mip_gap

#Loop through the blend range
for k in args.blends:
    #Create a new directory to save results for each scenario/case
    results_dir = os.path.join(results_dir1,
                               "interest_mid_blend_" + str(int(round(k * 100))))
    os.makedirs(results_dir, exist_ok=True)

    #Specify SAF Blend Requirement Parameter
    m.blend_requirement= k

    #Fix to no saf capacity at all airports
    for i in m.AIRPORTS:
        m.z[i].fix(0)

    #Restrict ATJ investments to a single supply chain stage
    if case["invest_at"] == "mills":
        for i in m.REFINERIES:
            m.y_ref[i].fix(0)
    else:
        for i in m.MILLS:
            m.y[i].fix(0)

    #Set mill specific incetives to 0, not used for this analysis
    for i in m.MILLS:
        m.s[i].fix(0)

    #Solve the model
    print("=== Case " + str(args.case) + ", blend requirement " + str(k), flush=True)
    results = solver.solve(m, tee=not args.quiet)

    #Save Connection Data to CSV File

    #Mill to Mill Volumes
    mill_volumes = {}
    mill_volumes['volumes'] = m.MILLS

    for i in m.MILLS:
        mill_volumes[i] = []
        for j in m.MILLS:
            if i != j:
                if pyo.value(m.vol_eth_sold[i,j]) > 1e-6:
                    mill_volumes[i].append(pyo.value(m.vol_eth_sold[i,j]))
                else: 
                    mill_volumes[i].append(0)
            else:
                mill_volumes[i].append(0)
                
    mill_vol = pd.DataFrame.from_dict(mill_volumes)
    mill_vol.to_csv(os.path.join(results_dir, "mill_to_mill_volumes.csv"))

    #Mill to Mill Connections
    mill_connections={}
    mill_connections['connections'] = m.MILLS

    for i in m.MILLS:
        mill_connections[i] = []
        for j in m.MILLS:
            if i != j:
                if pyo.value(m.vol_eth_sold[i,j]) > 1e-6:
                    mill_connections[i].append(1)
                else: 
                    mill_connections[i].append(0)
            else:
                mill_connections[i].append(0)

    mill_con = pd.DataFrame.from_dict(mill_connections)
    mill_con.to_csv(os.path.join(results_dir, "mill_to_mill_connections.csv"))

    #Mill to Airport Volumes SAF
    airport_volumes={}
    airport_volumes['volumes'] = m.AIRPORTS

    for i in m.MILLS:
        airport_volumes[i] = []
        for j in m.AIRPORTS:
            if pyo.value(m.vol_saf_sold_mills_air[i,j])>1e-6:
                airport_volumes[i].append(pyo.value(m.vol_saf_sold_mills_air[i,j]))
            else:
                airport_volumes[i].append(0)

    air_vol = pd.DataFrame.from_dict(airport_volumes)
    air_vol.to_csv(os.path.join(results_dir, "mill_to_airport_volumes.csv"))
            
    #Mill to Airport Connections SAF
    airport_connections={}
    airport_connections['connections'] = m.AIRPORTS

    for i in m.MILLS:
        airport_connections[i] = []
        for j in m.AIRPORTS:
            if pyo.value(m.vol_saf_sold_mills_air[i,j])>1e-6:
                airport_connections[i].append(1)
            else:
                airport_connections[i].append(0)
                
    air_con = pd.DataFrame.from_dict(airport_connections)
    air_con.to_csv(os.path.join(results_dir, "mill_to_airport_connections.csv"))

    #Mill to Airport Volumes Ethanol
    airport_volumes={}
    airport_volumes['volumes'] = m.AIRPORTS

    for i in m.MILLS:
        airport_volumes[i] = []
        for j in m.AIRPORTS:
            if pyo.value(m.vol_eth_sold_air[i,j])>1e-6:
                airport_volumes[i].append(pyo.value(m.vol_eth_sold_air[i,j]))
            else:
                airport_volumes[i].append(0)

    air_vol = pd.DataFrame.from_dict(airport_volumes)
    air_vol.to_csv(os.path.join(results_dir, "mill_to_airport_volumes_eth.csv"))
            
    #Mill to Airport Connections SAF
    airport_connections={}
    airport_connections['connections'] = m.AIRPORTS

    for i in m.MILLS:
        airport_connections[i] = []
        for j in m.AIRPORTS:
            if pyo.value(m.vol_eth_sold_air[i,j])>1e-6:
                airport_connections[i].append(1)
            else:
                airport_connections[i].append(0)
                
    air_con = pd.DataFrame.from_dict(airport_connections)
    air_con.to_csv(os.path.join(results_dir, "mill_to_airport_connections_eth.csv"))

    #Mill to Refinery Volumes Ethanol
    ref_volumes = {}
    ref_volumes['volumes'] = m.REFINERIES

    for i in m.MILLS:
        ref_volumes[i] = []
        for j in m.REFINERIES:
            if pyo.value(m.vol_eth_sold_ref[i,j])>1e-6:
                ref_volumes[i].append(pyo.value(m.vol_eth_sold_ref[i,j]))
            else:
                ref_volumes[i].append(0)

    ref_vol = pd.DataFrame.from_dict(ref_volumes)
    ref_vol.to_csv(os.path.join(results_dir, "mill_to_ref_vol_eth.csv"))

    #Mill to Refinery Volumes SAF
    ref_volumes = {}
    ref_volumes['volumes'] = m.REFINERIES

    for i in m.MILLS:
        ref_volumes[i] = []
        for j in m.REFINERIES:
            if pyo.value(m.vol_saf_sold_mills_ref[i,j])>1e-6:
                ref_volumes[i].append(pyo.value(m.vol_saf_sold_mills_ref[i,j]))
            else:
                ref_volumes[i].append(0)

    ref_vol = pd.DataFrame.from_dict(ref_volumes)
    ref_vol.to_csv(os.path.join(results_dir, "mill_to_ref_vol_saf.csv"))

    #Refinery to Airports Volumes Blended SAF
    ref_volumes = {}
    ref_volumes['volumes'] = m.AIRPORTS

    for i in m.REFINERIES:
        ref_volumes[i] = []
        for j in m.AIRPORTS:
            if pyo.value(m.vol_saf_sold_ref_air[i,j])>1e-6:
                ref_volumes[i].append(pyo.value(m.vol_saf_sold_ref_air[i,j]))
            else:
                ref_volumes[i].append(0)

    ref_vol = pd.DataFrame.from_dict(ref_volumes)
    ref_vol.to_csv(os.path.join(results_dir, "ref_to_air_vol_saf.csv"))

    #Other Important Results Data
    #Important Results Data Indexed by Mills
    key_results={}
    key_results['mills'] = m.MILLS

    key_results['OPEX'] = []
    key_results['CAPEX'] = []
    key_results['logistic'] = []
    key_results['profit'] = []
    key_results['additional costs'] = []
    key_results['et'] = []
    key_results['etmk'] = []
    key_results['etsaf'] = []
    key_results['etpc'] = []
    key_results['etref'] = []
    key_results['eta'] = []
    key_results['etr'] = []
    key_results['j1'] = []
    key_results['j2'] = []
    key_results['sug'] = []
    key_results['el'] = []
    key_results['SAF'] = []
    key_results['SAF ref'] = []
    key_results['SAF air'] = []
    key_results['g'] = []
    key_results['d'] = []
    key_results['objective'] = []
    key_results['sc cost'] = []
    key_results['individual profit'] = []
    key_results['capacity'] = []
    key_results['incentives'] = []

    #These expressions are identical for every mill, airport and refinery. Evaluating
    #each once rather than once per index writes exactly the same values and saves
    #roughly 10 minutes per instance (each evaluation costs ~0.55 s).
    total_profit = pyo.value(m.profit_expression)
    total_additional_costs = pyo.value(m.additional_costs)
    total_sc_cost = pyo.value(m.sc_cost_expression)
    total_objective = pyo.value(m.objective)
    total_logistic = (pyo.value(m.mill_to_mill_logistic_cost)
                      + pyo.value(m.mill_to_airport_logistic_cost)
                      + pyo.value(m.mill_to_ref_logistic_cost)
                      + pyo.value(m.ref_to_air_logistic_cost))

    for i in m.MILLS:
        key_results['OPEX'].append(pyo.value(m.individual_opex_mill[i]))
        key_results['CAPEX'].append(pyo.value(m.CAPEX[i]))
        key_results['logistic'].append(pyo.value(m.individual_mill_to_mill_log_cost[i]) + pyo.value(m.individual_mill_to_airport_log_cost[i]) + pyo.value(m.individual_mill_to_ref_log_cost[i]))
        key_results['individual profit'].append(pyo.value(m.ind_profs[i]))
        key_results['profit'].append(total_profit)
        key_results['additional costs'].append(total_additional_costs)
        key_results['sc cost'].append(total_sc_cost)
        key_results['objective'].append(total_objective)
        key_results['et'].append(pyo.value(m.x[i,'et']))
        key_results['etmk'].append(pyo.value(m.x[i,'etmk']))
        key_results['etsaf'].append(pyo.value(m.x[i,'etsaf']))
        key_results['etpc'].append(pyo.value(m.x[i,'etpc']))
        key_results['etref'].append(pyo.value(m.x[i,'etref']))
        key_results['eta'].append(pyo.value(m.x[i,'eta']))
        key_results['etr'].append(pyo.value(m.x[i,'etr']))
        key_results['j1'].append(pyo.value(m.x[i,'j1']))
        key_results['j2'].append(pyo.value(m.x[i,'j2']))
        key_results['sug'].append(pyo.value(m.x[i,'sug']))
        key_results['el'].append(pyo.value(m.x[i,'el']))
        key_results['SAF'].append(pyo.value(m.x[i,'saf']))
        key_results['SAF ref'].append(pyo.value(m.x[i,'saf ref']))
        key_results['SAF air'].append(pyo.value(m.x[i,'saf air']))
        key_results['g'].append(pyo.value(m.x[i,'g']))
        key_results['d'].append(pyo.value(m.x[i,'d']))
        key_results['capacity'].append(pyo.value(m.Sugarcane_Capacity[i]))
        key_results['incentives'].append(pyo.value(m.s[i]))

    results = pd.DataFrame.from_dict(key_results)
    results.to_csv(os.path.join(results_dir, 'key_results_mills.csv'))

    #Important Results Data Indexed by Airports
    key_results={}
    key_results['airports'] = m.AIRPORTS

    key_results['OPEX'] = []
    key_results['CAPEX'] = []
    key_results['total cost'] = []
    key_results['additional costs'] = []
    key_results['objective'] = []
    key_results['jet fuel'] = []
    key_results['gasoline'] = []
    key_results['ethanol'] = []
    key_results['sugar'] = []
    key_results['et'] = []
    key_results['SAF'] = []
    key_results['g'] = []
    key_results['d'] = []

    for a in m.AIRPORTS:
        key_results['OPEX'].append(pyo.value(m.individual_opex_air[a]))
        key_results['CAPEX'].append(pyo.value(m.CAPEX_air[a]))
        key_results['total cost'].append(pyo.value(m.CAPEX_air[a]) + pyo.value(m.individual_opex_air[a]))
        key_results['additional costs'].append(total_additional_costs)
        key_results['objective'].append(total_objective)
        key_results['et'].append(pyo.value(m.v[a,'et']))
        key_results['SAF'].append(pyo.value(m.v[a,'saf']))
        key_results['g'].append(pyo.value(m.v[a,'g']))
        key_results['d'].append(pyo.value(m.v[a,'d']))
        key_results['jet fuel'].append(pyo.value(m.p['f']))
        key_results['gasoline'].append(pyo.value(m.p['g']))
        key_results['ethanol'].append(pyo.value(m.p['et']))
        key_results['sugar'].append(pyo.value(m.p['sug']))

    results = pd.DataFrame.from_dict(key_results)
    results.to_csv(os.path.join(results_dir, 'key_results_air.csv'))

    #Important Results Data Indexed by Refinery
    key_results={}
    key_results['refinery'] = m.REFINERIES

    key_results['OPEX'] = []
    key_results['CAPEX'] = []
    # key_results['total cost'] = []
    key_results['additional costs'] = []
    key_results['objective'] = []
    key_results['blended SAF'] = []
    key_results['SAF'] = []
    key_results['g'] = []
    key_results['d'] = [] 
    key_results['total logistic'] = []

    for i in m.REFINERIES:
        key_results['OPEX'].append(pyo.value(m.individual_opex_ref[i]))
        key_results['CAPEX'].append(pyo.value(m.CAPEX_ref[i]))
        # key_results['total cost'].append(pyo.value(m.CAPEX_air[a]) + pyo.value(m.individual_opex_air[a]))
        key_results['total logistic'].append(total_logistic)
        key_results['additional costs'].append(total_additional_costs)
        key_results['objective'].append(total_objective)
        key_results['blended SAF'].append(pyo.value(m.x_ref[i,'blended saf']))
        key_results['SAF'].append(pyo.value(m.x_ref[i,'saf']))
        key_results['g'].append(pyo.value(m.x_ref[i,'g']))
        key_results['d'].append(pyo.value(m.x_ref[i,'d']))
        

    results = pd.DataFrame.from_dict(key_results)
    results.to_csv(os.path.join(results_dir, 'key_results_ref.csv'))