# from create_sc_model_with_demand import *
from create_sc_model_full import *
import os
import pandas as pd
import numpy as np

this_file_path = os.path.dirname(os.path.realpath(__file__))

# create a directory to save results
results_dir1 = os.path.join(this_file_path, "Case1") #Update the name for each case study: Case1, Case2, Case3, Case4
if not os.path.isdir(results_dir1):
    os.mkdir(results_dir1)

#Specify a blend range to iterate over
blend_range = [0,.1,.2,.3,.4,.5] #0% to 50% SAF blend range, 0% is the reference point for each case study

#Specify Input Data and Parameters
data = 'base_case_data_with_demands.xlsx'
saf_prem = 0 #No SAF premium
eth_prem = 0 #No ethanol premium
max_saf_capacity = 700000
blend = 0 #Initialize blend to 0

#Create supply chain model, set profit_obj = True for Cases 3 and 4 and profit_obj = False for Cases 1 and 2
m = create_supply_chain_model(data, saf_prem, eth_prem, blend, max_saf_capacity, profit_obj = False, grass_roots_factor=0.5, breakpoints=10, ref_blend=True)

#Loop through the premium range
p=0
for k in blend_range: 
    #Create a new directory to save results for each scenario/case
    results_dir = os.path.join(results_dir1, "interest_mid_blend_" + str(p))
    p = p+10 #add to the string to name each blend case
    if not os.path.isdir(results_dir):
        os.mkdir(results_dir)

    #Specify SAF Premium Parameter
    m.blend_requirement= k
    
    #Fix to no saf capacity at all airports
    for i in m.AIRPORTS:
        m.z[i].fix(0)

    #Fix investments at refineries to 0 for Cases 1 and 3, comment out for Cases 2 and 4
    for i in m.REFINERIES:
       m.y_ref[i].fix(0)
    
    #Fix investments at mills to 0 for Cases 1 and 3, comment out for Cases 2 and 4
    # for i in m.MILLS:
    #    m.y[i].fix(0)  
        
    #Set mill specific incetives to 0, not used for this analysis
    for i in m.MILLS:
        m.s[i].fix(0)

    solver = pyo.SolverFactory('gurobi')

    solver.options['MIPGap'] = 0.00003 #Fix MIP gap to 0.003%
    
    #Solve the model
    results = solver.solve(m, tee=True)

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
    mill_vol.to_csv(results_dir + "/mill_to_mill_volumes.csv")

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
    mill_con.to_csv(results_dir + "/mill_to_mill_connections.csv")

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
    air_vol.to_csv(results_dir + "/mill_to_airport_volumes.csv")
            
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
    air_con.to_csv(results_dir + "/mill_to_airport_connections.csv")

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
    air_vol.to_csv(results_dir + "/mill_to_airport_volumes_eth.csv")
            
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
    air_con.to_csv(results_dir + "/mill_to_airport_connections_eth.csv")

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
    ref_vol.to_csv(results_dir + "/mill_to_ref_vol_eth.csv")

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
    ref_vol.to_csv(results_dir + "/mill_to_ref_vol_saf.csv")

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
    ref_vol.to_csv(results_dir + "/ref_to_air_vol_saf.csv")

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

    for i in m.MILLS:
        key_results['OPEX'].append(pyo.value(m.individual_opex_mill[i]))
        key_results['CAPEX'].append(pyo.value(m.CAPEX[i]))
        key_results['logistic'].append(pyo.value(m.individual_mill_to_mill_log_cost[i]) + pyo.value(m.individual_mill_to_airport_log_cost[i]) + pyo.value(m.individual_mill_to_ref_log_cost[i]))
        key_results['individual profit'].append(pyo.value(m.ind_profs[i]))
        key_results['profit'].append(pyo.value(m.profit_expression))
        key_results['additional costs'].append(pyo.value(m.additional_costs))
        key_results['sc cost'].append(pyo.value(m.sc_cost_expression))
        key_results['objective'].append(pyo.value(m.objective))
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
    results.to_csv(results_dir + '/key_results_mills.csv')

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
        key_results['additional costs'].append(pyo.value(m.additional_costs))
        key_results['objective'].append(pyo.value(m.objective))
        key_results['et'].append(pyo.value(m.v[a,'et']))
        key_results['SAF'].append(pyo.value(m.v[a,'saf']))
        key_results['g'].append(pyo.value(m.v[a,'g']))
        key_results['d'].append(pyo.value(m.v[a,'d']))
        key_results['jet fuel'].append(pyo.value(m.p['f']))
        key_results['gasoline'].append(pyo.value(m.p['g']))
        key_results['ethanol'].append(pyo.value(m.p['et']))
        key_results['sugar'].append(pyo.value(m.p['sug']))

    results = pd.DataFrame.from_dict(key_results)
    results.to_csv(results_dir + '/key_results_air.csv')

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
        key_results['total logistic'].append(pyo.value(m.mill_to_mill_logistic_cost) + pyo.value(m.mill_to_airport_logistic_cost) + pyo.value(m.mill_to_ref_logistic_cost) + pyo.value(m.ref_to_air_logistic_cost))
        key_results['additional costs'].append(pyo.value(m.additional_costs))
        key_results['objective'].append(pyo.value(m.objective))
        key_results['blended SAF'].append(pyo.value(m.x_ref[i,'blended saf']))
        key_results['SAF'].append(pyo.value(m.x_ref[i,'saf']))
        key_results['g'].append(pyo.value(m.x_ref[i,'g']))
        key_results['d'].append(pyo.value(m.x_ref[i,'d']))
        

    results = pd.DataFrame.from_dict(key_results)
    results.to_csv(results_dir + '/key_results_ref.csv')