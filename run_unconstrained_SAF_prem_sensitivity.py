# from create_sc_model_with_demand import *
from create_sc_model_full import *
import os
import pandas as pd
import numpy as np

this_file_path = os.path.dirname(os.path.realpath(__file__))

# create a directory to save results
results_dir1 = os.path.join(this_file_path, "unconstrained_SAF")
if not os.path.isdir(results_dir1):
    os.mkdir(results_dir1)

# create a directory to save results
results_dir = os.path.join(results_dir1, "Case 5")
if not os.path.isdir(results_dir):
    os.mkdir(results_dir)
    
#Specify Input Data and Parameters
data = 'base_case_data_with_demands.xlsx'
saf_prem = 0 #Initialize SAF incentive to 0
eth_prem = 0 #No ethanol premium
max_saf_capacity = 700000
blend = 0 #Set to zero to relax the SAF blend requirement constraint

#Create supply chain model - Scenario 1, upgrading at mills only, blend at refinery or airport, maximize profit, only meet SAF demand
m = create_supply_chain_model(data, saf_prem, eth_prem, blend, max_saf_capacity, profit_obj = True, grass_roots_factor=0.5, breakpoints=10, ref_blend=True)

#Fix to no SAF capacity at all airports
for i in m.AIRPORTS:
    m.z[i].fix(0)

#Fix to no SAF capacity at all refineries
for i in m.REFINERIES:
   m.y_ref[i].fix(0)

#Fix mill-specific incentives to 0
for i in m.MILLS:
    m.s[i].fix(0)


prem_range = np.linspace(0,4,41)
result = {}
result['SAF Production'] = []
result['eth market'] = []
result['Total Cost'] = []
result['Total Profit'] = []
result['premium'] = []

#loop through the premium range
for j in prem_range:

    #Specify SAF Premium Parameter
    m.saf_premium = j*1000 #Convert from $R/l to $R/m3

    solver = pyo.SolverFactory('gurobi')

    solver.options['MIPGap'] = 0.0005 #Increase the MIP gap since not worried about the exact location of SAF investments to improve solve time
    results = solver.solve(m, tee=True)

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
results_df.to_csv(results_dir + '/production.csv')


