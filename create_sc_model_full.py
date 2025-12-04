'''
This file contains a function defining a supply chain model for distributing bio-jet fuel capacity
 via the alcohol-to-jet (ATJ) technology in Brazil to support the manuscript CITE.

Created by Madelynn Watson and the University of Notre Dame
'''

#Import the necessary packages
import pyomo.environ as pyo
import pandas as pd
import numpy as np

def create_supply_chain_model(data, saf_prem, eth_prem, blend, max_saf_capacity, profit_obj = True, grass_roots_factor=0.5, breakpoints=10, ref_blend=False):
    '''
    This function buils a supply chain model in Pyomo for bio-jet fuel production in Brazil.

    Inputs: 
    
            data: excel sheet containing data for the model including mill distances, refinery distances, airport distances, mill capacities,
                  airport demands, product prices, unit conversion rates, and unit costs.
            saf_prem: premium price for sustainable aviation fuel, units: R$/m3 saf
            eth_prem: premium price for ethanol sold to mills to make saf units: R$/m3 eth
            individual_demand: True if indivual airport demands are to be satified by SAF, otherwise False
            max_saf_capacity: Maximum size for SAF technology at each mill, units: m3 eth
            breakpoints: Number of breakpoints for the linear piece-wise surrogate model, defualt: 10
            profit_obj: Determines the mode of the objective: True: Maximize Profit, False Minimize Cost
            grass_roots_factor: Factor to increase the brownfield CAPEX for greenfield implimentation
            ref_blend: True if blending must occur at refineries False if it can occur at airports

    Returns: Pyomo model m
    '''
    #Create empty pyomo model
    m = pyo.ConcreteModel()

    #Read in Data from Excel sheet "data"
    df_mill_distances = pd.read_excel(data,sheet_name = 'mill_distances')
    df_mill_capacities = pd.read_excel(data, sheet_name='mill_capacities')
    df_airport_demand = pd.read_excel(data, sheet_name= 'airport_demand')
    df_airport_distances = pd.read_excel(data, sheet_name='airport_distances')
    df_refineries = pd.read_excel(data, sheet_name='refineries')
    df_mill_refinery_distances = pd.read_excel(data,sheet_name='mill_ref_distances')
    df_refinery_airport_distances = pd.read_excel(data, sheet_name='ref_air_distances')
    df_conversions = pd.read_excel(data, sheet_name = 'conversions')
    df_prices = pd.read_excel(data, sheet_name='prices')
    df_mill_type_eth = pd.read_excel(data, sheet_name = 'eth_mills')
    df_mill_type_annexed = pd.read_excel(data, sheet_name = 'annexed_mills')
    df_ref_profs1a = pd.read_excel(data, sheet_name='reference1a')
    df_ref_profs1b = pd.read_excel(data, sheet_name='reference1b')
    
    #SETS
    products_and_intermeadiates = ['jui', 'j1', 'j2', 'bag', 'sug', 'et', 'el', 'mol', 'saf','saf air', 'saf ref', 'etmk', 'etsaf', 'etref','etr', 'etpc','eta','g','d','blended saf']
    mills = df_mill_capacities['mill'].tolist()
    annexed_mills = df_mill_type_annexed['Annexed Mills'].tolist()
    ethanol_mills = df_mill_type_eth['Ethanol Mills'].tolist()
    airports = df_airport_demand['airport'].tolist()
    refineries = df_refineries['ref'].tolist()
    conversion_codes = df_conversions['conversion_codes'].tolist()
    selling_products = df_prices['product'].tolist()
    global_market = ['sug','et','f','g']

    #PYOMO SETS
    m.PRODUCTS_AND_INTERMEADIATES = pyo.Set(initialize = products_and_intermeadiates)
    m.MILLS = pyo.Set(initialize = mills)
    m.ANNEXED_MILLS = pyo.Set(initialize = annexed_mills)
    m.ETHANOL_MILLS = pyo.Set(initialize = ethanol_mills)
    m.AIRPORTS = pyo.Set(initialize = airports)
    m.REFINERIES = pyo.Set(initialize = refineries)
    m.CONVERSION_CODES = pyo.Set(initialize=conversion_codes)
    m.INDEX_SET1 = pyo.Set(initialize = np.linspace(0,breakpoints-2,breakpoints-1))
    m.INDEX_SET2 = pyo.Set(initialize = np.linspace(0,breakpoints-3,breakpoints-2))
    m.INDEX_SET3 = pyo.Set(initialize = np.linspace(0,breakpoints-1,breakpoints))
    m.SELLING_PRODUCTS = pyo.Set(initialize = selling_products)
    m.GLOBAL_MARKET = pyo.Set(initialize = global_market)

    #PARAMETERS
    #Mill Capacities
    Ca = {}
    for i in range(len(mills)):
        Ca[mills[i]] = df_mill_capacities['capacity'][i]

    #Conversion Rates
    conv = {}
    for i in range(len(conversion_codes)):
        conv[conversion_codes[i]] = df_conversions['rate'][i]

    #Airport Demands
    Da = {}
    for i in range(len(airports)):
        Da[airports[i]] = df_airport_demand['demand'][i]

    #Price and Costs
    price = {}
    for i in range(len(selling_products)):
        price[selling_products[i]] = df_prices['price'][i]

    cost = {}
    for i in range(len(selling_products)):
        cost[selling_products[i]] = df_prices['cost'][i]

    #Reference Profits
    ref_prof1a = {}
    for i in range(len(mills)):
        ref_prof1a[mills[i]] = df_ref_profs1a['Reference Mill Profs 1a'][i]

    ref_prof1b = {}
    for i in range(len(mills)):
        ref_prof1b[mills[i]] = df_ref_profs1b['Reference Mill Profs 1b'][i]

    #Distances
    mill_distances = {}
    for i in range(len(mills)):
        for j in range(len(mills)):
            mill_distances[mills[i],mills[j]] = df_mill_distances[mills[i]][j]

    airport_distances = {}
    for i in range(len(airports)):
        for j in range(len(mills)):
            airport_distances[airports[i],mills[j]] = df_airport_distances[airports[i]][j]

    mill_ref_distances = {}
    for i in range(len(refineries)):
        for j in range(len(mills)):
            mill_ref_distances[refineries[i],mills[j]] = df_mill_refinery_distances[refineries[i]][j]

    ref_air_distances = {}
    for i in range(len(refineries)):
        for j in range(len(airports)):
            ref_air_distances[refineries[i],airports[j]] = df_refinery_airport_distances[refineries[i]][j]


    #PYOMO PARAMETERS
    m.M = pyo.Param(initialize = 5e6, mutable = True)
    m.n = pyo.Param(initialize = 0.65) #Capex scaling factor
    m.amortization = pyo.Param(initialize = 1) #Already amortized 
    m.blend_requirement = pyo.Param(initialize = blend, mutable = True)
    m.minimum_sugar = pyo.Param(initialize = 0.4, mutable = True)
    m.minimum_ethanol = pyo.Param(initialize = 0.4, mutable = True)
    m.max_saf_capacity = pyo.Param(initialize = max_saf_capacity, mutable = True)
    m.reference_capex = pyo.Param(initialize = 11970824, mutable = True) #2023 R$/year
    m.reference_flow = pyo.Param(initialize = 84000, mutable = True) #m3 eth/year
    m.reference_profit1a = pyo.Param(m.MILLS, initialize = ref_prof1a) #R$/year
    m.reference_profit1b = pyo.Param(m.MILLS, initialize = ref_prof1b) #R$/year
    m.Saf_CAPEX_Inputs = pyo.Param(m.INDEX_SET3, initialize = np.linspace(0,max_saf_capacity,breakpoints))
    m.Sugarcane_Capacity = pyo.Param(m.MILLS, initialize = Ca, mutable = True) #tonne sc
    m.Conversion = pyo.Param(m.CONVERSION_CODES, initialize = conv, mutable = True)
    m.individual_saf_demand = pyo.Param(m.AIRPORTS, initialize = Da, mutable = True) #m3 saf
    m.price = pyo.Param(m.SELLING_PRODUCTS, initialize = price, mutable = True) 
    m.cost = pyo.Param(m.SELLING_PRODUCTS, initialize = cost, mutable = True) 
    m.logistic_cost = pyo.Param(initialize = 0.16, mutable = True)
    m.fixed_logistic_cost = pyo.Param(initialize = 17.82, mutable = True)
    m.mill_distance = pyo.Param(m.MILLS, m.MILLS, initialize = mill_distances, mutable = True) #km
    m.airport_distance = pyo.Param(m.AIRPORTS, m.MILLS, initialize = airport_distances, mutable = True) #km
    m.mill_ref_distance = pyo.Param(m.REFINERIES,m.MILLS, initialize = mill_ref_distances, mutable = True) #km
    m.ref_air_distance = pyo.Param(m.REFINERIES,m.AIRPORTS, initialize = ref_air_distances, mutable = True) #km
    m.saf_premium = pyo.Param(initialize = saf_prem, mutable = True)
    m.eth_prem = pyo.Param(initialize = eth_prem, mutable = True)
    m.ethanol_energy = pyo.Param(initialize = 0.021200) #E100 energy density (TJ/m3)
    m.gas_energy = pyo.Param(initialize = 0.029520) #E25 gasoline energy density (TJ/m3)
    m.total_sugar_demand = pyo.Param(initialize = 44000000, mutable = True) #Sugar production in 2023/2024 season
    m.ground_demand = pyo.Param(initialize = 1.74e6, mutable = True) #Energy consumed from hydrous ethanol and gasoline in 2023 in Brazil (TJ)
    m.ethanol_upper_bound = pyo.Param(initialize = 6000000, mutable = True) #Corn ethanol available for purchase
    m.grass_roots_factor = pyo.Param(initialize = grass_roots_factor, mutable = True) #increase in CAPEX for greenfield development (20%-100% 50% default)
    m.greenfield_opex_air = pyo.Param(initialize = 1130, mutable = True) #Opex for non integrated SAF production (airport)
    m.greenfield_opex_ref = pyo.Param(initialize = 1130, mutable = True) #Opex for non integrated SAF production (refinery)

    #VARIABLES
    #Continious
    #Production
    m.x = pyo.Var(m.MILLS,m.PRODUCTS_AND_INTERMEADIATES, within=pyo.NonNegativeReals) #Amount of products and intermeadiates produced at each mill
    m.v = pyo.Var(m.AIRPORTS,m.PRODUCTS_AND_INTERMEADIATES, within=pyo.NonNegativeReals) #Amount of products and intermeadiates produced at each airport
    m.x_ref = pyo.Var(m.REFINERIES, m.PRODUCTS_AND_INTERMEADIATES, within=pyo.NonNegativeReals) #Amount of products and intermeadiates produced at each airport
    #Purchased
    m.p = pyo.Var(m.GLOBAL_MARKET, within = pyo.NonNegativeReals) #Amount of product purchased from global market
    #Market
    #SAF
    m.vol_saf_sold_mills_air = pyo.Var(m.MILLS, m.AIRPORTS, within=pyo.NonNegativeReals) # volume of saf sold from mill u to airport a
    m.vol_saf_sold_mills_ref = pyo.Var(m.MILLS, m.REFINERIES, within=pyo.NonNegativeReals) # volume of saf sold from mill u to refinery r
    m.vol_saf_sold_ref_air = pyo.Var(m.REFINERIES,m.AIRPORTS, within=pyo.NonNegativeReals) # volume of saf sold from refinery r to airport a
    #Ethanol
    m.vol_eth_sold = pyo.Var(m.MILLS, m.MILLS, within=pyo.NonNegativeReals )   # volume of ethanol send from mill s to s
    m.vol_eth_sold_air = pyo.Var(m.MILLS, m.AIRPORTS, within=pyo.NonNegativeReals) #volume of ethanol sold from mill u to airport a
    m.vol_eth_sold_ref = pyo.Var(m.MILLS, m.REFINERIES, within = pyo.NonNegativeReals) #volume of ethanol sold from mill u to refinery r
    #Incentives
    #m.s = pyo.Var(m.MILLS, within = pyo.NonNegativeReals, initialize = 0, bounds=(0,2)) # Mill specific incentives R$
    m.s = pyo.Var(m.MILLS, within = pyo.NonNegativeReals, initialize = 0) # Mill specific incentives R$

    #CAPEX
    # m.SAF_capacity = pyo.Var(m.MILLS, within=pyo.NonNegativeReals)  # capacity of each mill in producing saf
    # m.SAF_capacity_air = pyo.Var(m.AIRPORTS, within = pyo.NonNegativeReals) #capacity of each airport in producing saf
    # m.SAF_capacity_ref = pyo.Var(m.REFINERIES, within = pyo.NonNegativeReals) #capacity of each refinery in producing saf
    # m.CAPEX = pyo.Var(m.MILLS, within=pyo.NonNegativeReals)  # capital cost as function of saf prod capacity at mills
    # m.CAPEX_air = pyo.Var(m.AIRPORTS, within=pyo.NonNegativeReals)  # capital cost as function of saf prod capacity at airports
    # m.CAPEX_ref = pyo.Var(m.REFINERIES, within=pyo.NonNegativeReals) # capital cost as function of saf prod capacity at refineries
    m.csi = pyo.Var(m.MILLS, m.INDEX_SET1, within = pyo.NonNegativeReals,bounds=(0,1)) #Continious auxillary variable for capex surrogate model - mills
    m.csi_air = pyo.Var(m.AIRPORTS, m.INDEX_SET1, within = pyo.NonNegativeReals,bounds=(0,1)) #Continious auxillary variable for capex surrogate model - airports
    m.csi_ref = pyo.Var(m.REFINERIES, m.INDEX_SET1, within = pyo.NonNegativeReals, bounds=(0,1)) #Continious auxillary variable for capex surrogate model - refineries

    #Binary
    m.y = pyo.Var(m.MILLS, domain = pyo.Binary) #decision on investment in SAF capacity at mills
    m.z = pyo.Var(m.AIRPORTS, domain = pyo.Binary) #decision to invest in SAF capacity at airports
    m.y_ref = pyo.Var(m.REFINERIES, domain = pyo.Binary) #decision to invest in SAF capacity at refineries
    m.aux = pyo.Var(m.MILLS, m.INDEX_SET2, within = pyo.Binary) #Binary auxillary variable for CAPEX surrogate - mills
    m.aux_air = pyo.Var(m.AIRPORTS, m.INDEX_SET2, within = pyo.Binary) #Binary auxillary variable for CAPEX surrogate - airports
    m.aux_ref = pyo.Var(m.REFINERIES, m.INDEX_SET2, within = pyo.Binary) #Binary auxillary variable for CAPEX surrogate - refineries

    #CONSTRAINTS
    #Sugarcane Mill Mass Balances

    #Juice Production in Each Mill
    def juice_production(m,i):
        return m.x[i,'jui'] == m.Sugarcane_Capacity[i]*m.Conversion['sc_to_jui']
    m.juice_production = pyo.Constraint(m.MILLS, rule = juice_production)

    #Bagasse Production in Each Mill
    def bagasse_production(m,i):
        return m.x[i,'bag'] == m.Sugarcane_Capacity[i]*m.Conversion['sc_to_bag']
    m.bagasse_production = pyo.Constraint(m.MILLS, rule = bagasse_production)

    #Juice Split
    def juice_split(m,i):
        return m.x[i,'jui'] == m.x[i,'j1'] + m.x[i,'j2']
    m.juice_split = pyo.Constraint(m.MILLS,rule = juice_split)

    #Ethanol Mills - No sugar production
    def no_sug(m,i):
        return m.x[i,'j1'] == 0
    m.no_sug = pyo.Constraint(m.ETHANOL_MILLS, rule = no_sug)

    #Sugar Production
    def sugar_production(m,i):
        return m.x[i,'sug'] == m.x[i,'j1']*m.Conversion['jui_to_sug']
    m.sugar_production = pyo.Constraint(m.MILLS, rule = sugar_production)

    #Molasse Production
    def molasse_production(m,i):
        return m.x[i,'mol'] == m.x[i,'sug']*m.Conversion['sug_to_mol']
    m.molasse_production = pyo.Constraint(m.MILLS, rule = molasse_production)

    #Electricity Production
    def electricity_production(m,i):
        return m.x[i,'el'] == m.x[i,'bag']*m.Conversion['bag_to_el']
    m.electricity_production = pyo.Constraint(m.MILLS, rule = electricity_production)

    #Annexed Mills
    #Ethanol Production
    def ethanol_production(m,i):
        return m.x[i,'et'] == m.x[i,'j2']*m.Conversion['jui_to_et'] + m.x[i,'mol']*m.Conversion['mol_to_et']
    m.ethanol_production = pyo.Constraint(m.MILLS, rule = ethanol_production)

    #Ethanol Destinations Balance
    def ethanol_destinations(m, i):
        return m.x[i,'et'] == m.x[i,'etmk'] + m.x[i,'etref'] + m.x[i,'etsaf'] + m.x[i,'eta'] + m.x[i,'etr']
    m.ethanol_destinations = pyo.Constraint(m.MILLS, rule = ethanol_destinations)

    #SAF Production
    def saf_production(m,i):
        return m.x[i,'saf'] == (m.x[i,'etsaf'] + m.x[i,'etpc'])*m.Conversion['et_to_saf']
    m.saf_production = pyo.Constraint(m.MILLS, rule = saf_production)

    #SAF Split
    def saf_split(m,i):
        return m.x[i,'saf'] == m.x[i,'saf air'] + m.x[i,'saf ref']
    m.saf_split = pyo.Constraint(m.MILLS, rule = saf_split)

    #Diesel Production
    def diesel_production(m,i):
        return m.x[i,'d'] == (m.x[i,'etsaf'] + m.x[i,'etpc'])*m.Conversion['et_to_d']
    m.diesel_production = pyo.Constraint(m.MILLS, rule = diesel_production)

    #Gasoline Production
    def gas_production(m,i):
        return m.x[i,'g'] == (m.x[i,'etsaf'] + m.x[i,'etpc'])*m.Conversion['et_to_g']
    m.gas_production = pyo.Constraint(m.MILLS, rule = gas_production)

    #Mill Capacity Restrictions

    #Annexed Mills Only
    #Minimum Production Rate of Sugar
    def minimum_sugar_production(m,i):
        return m.x[i,'j1'] >= m.minimum_sugar*m.x[i,'jui']
    m.minimum_sugar_production = pyo.Constraint(m.ANNEXED_MILLS, rule = minimum_sugar_production)

    #Minimum Production Rate of Ethanol
    def minimum_ethanol_production(m,i):
        return m.x[i,'et'] >= m.minimum_ethanol*m.x[i,'jui']*m.Conversion['jui_to_et']
    m.minimum_ethanol_production = pyo.Constraint(m.ANNEXED_MILLS, rule = minimum_ethanol_production)

    #Airport Mass Balances

    #SAF Production
    def saf_prod_air(m,i):
        return m.v[i,'saf'] == m.v[i,'et']*m.Conversion['et_to_saf']
    m.saf_prod_air = pyo.Constraint(m.AIRPORTS, rule=saf_prod_air)

    #Gasoline produdction
    def gas_prod_air(m,i):
        return m.v[i,'g'] == m.v[i,'et']*m.Conversion['et_to_g']
    m.gas_prod_air = pyo.Constraint(m.AIRPORTS, rule = gas_prod_air)

    #Diesel Production
    def diesel_prod_air(m,i):
        return m.v[i,'d'] == m.v[i,'et']*m.Conversion['et_to_d']
    m.diesel_prod_air = pyo.Constraint(m.AIRPORTS, rule = diesel_prod_air)

    #Refinery Mass Balances

    #SAF Production
    def saf_prod_ref(m,i):
        return m.x_ref[i,'saf'] == m.x_ref[i,'et']*m.Conversion['et_to_saf']
    m.saf_prod_ref = pyo.Constraint(m.REFINERIES, rule=saf_prod_ref)

    #Gasoline Producton
    def gas_prod_ref(m,i):
        return m.x_ref[i,'g'] == m.x_ref[i,'et']*m.Conversion['et_to_g']
    m.gas_prod_ref = pyo.Constraint(m.REFINERIES, rule = gas_prod_ref)

    #Diesel Production
    def diesel_prod_ref(m,i):
        return m.x_ref[i,'d'] == m.x_ref[i,'et']*m.Conversion['et_to_d']
    m.diesel_prod_ref = pyo.Constraint(m.REFINERIES, rule = diesel_prod_ref)

    #Market Relationships

    #Mill to Mill - Ethanol
    #Summation of Ethanol Sold to Mills for SAF Production
    def eth_sold_sum(m, i):
        return( sum(m.vol_eth_sold[i, j] for j in m.MILLS if i != j)  )
    m.eth_sold_sum = pyo.Expression(m.MILLS, rule=eth_sold_sum)

    #Balance of Ethanol Sold to Each Mill
    def ethanol_sold(m, i):
        return m.x[i, 'etref'] == m.eth_sold_sum[i]
    m.ethanol_sold = pyo.Constraint(m.MILLS, rule = ethanol_sold)

    #Ethanol Selling Constraint (only sell if not producing SAF) - MILLS
    def eth_selling_constraint(m,i):
        return m.x[i, 'etref'] <= (1-m.y[i])*m.M 
    m.eth_selling_constraint = pyo.Constraint(m.MILLS, rule = eth_selling_constraint)

    #Summation of Ethanol Purchased - MILLS
    def eth_purchased_sum(m,j):
        return( sum(m.vol_eth_sold[i, j] for i in m.MILLS if i != j)  )
    m.eth_purchased_sum = pyo.Expression(m.MILLS, rule = eth_purchased_sum)

    #Balance of Ethanol Purchased by Each Mill
    def ethanol_purchased(m,i):
        return m.x[i,'etpc'] == m.eth_purchased_sum[i]
    m.ethanol_purchased = pyo.Constraint(m.MILLS, rule = ethanol_purchased)

    #Ethanol Purchasing Constraint (only purchase if producing SAF) - MILLS
    def eth_purchasing_constraint(m,i):
        return m.x[i, 'etpc'] <= (m.y[i])*m.M
    m.eth_purchasing_constraint = pyo.Constraint(m.MILLS, rule = eth_purchasing_constraint)

    #Mill to Airport - Ethanol
    #Summation of Ethanol Sold to Airports
    def eth_sold_air_sum(m,i):
        return sum(m.vol_eth_sold_air[i,j] for j in m.AIRPORTS)
    m.eth_sold_air_sum = pyo.Expression(m.MILLS, rule = eth_sold_air_sum)

    #Balance of Ethanol sold to Each Airport
    def eth_sold_air(m,i):
        return m.x[i,'eta'] == m.eth_sold_air_sum[i]
    m.eth_sold_air = pyo.Constraint(m.MILLS, rule = eth_sold_air)

    #Ethanol Selling Constraint (only sell if not producting SAF) - AIRPORTS
    def eth_selling_constraint_air(m,i):
        return m.x[i,'eta'] <= (1-m.y[i])*m.M
    m.eth_selling_constraint_air = pyo.Constraint(m.MILLS, rule = eth_selling_constraint_air)

    #Summation of Ethanol Purchased - AIRPORTS
    def eth_purchased_sum_air(m,i):
        return sum(m.vol_eth_sold_air[j,i] for j in m.MILLS)
    m.eth_purchased_sum_air = pyo.Expression(m.AIRPORTS, rule=eth_purchased_sum_air)

    #Balance of Ethanol Purchased by Each Airport
    def eth_purchased_air(m,i):
        return m.v[i,'et'] == m.eth_purchased_sum_air[i]
    m.eth_purchased_air = pyo.Constraint(m.AIRPORTS, rule = eth_purchased_air)

    #Ethanol Purchasing Constraint (only purchase if producing SAF) - AIRPORTS
    def eth_purchasing_constraint_air(m,i):
        return m.v[i,'et'] <= m.z[i]*m.M
    m.eth_purchasing_constraint_air = pyo.Constraint(m.AIRPORTS, rule = eth_purchasing_constraint_air)

    #Mill to Refinery - Ethanol
    #Summation of Ethanol Sold to Refineries
    def eth_sold_ref_sum(m,i):
        return sum(m.vol_eth_sold_ref[i,j] for j in m.REFINERIES)
    m.eth_sold_ref_sum = pyo.Expression(m.MILLS, rule = eth_sold_ref_sum)

    #Balance of Ethanol sold to Each Refinery
    def eth_sold_ref(m,i):
        return m.x[i,'etr'] == m.eth_sold_ref_sum[i]
    m.eth_sold_ref = pyo.Constraint(m.MILLS, rule = eth_sold_ref)

    #Ethanol Selling Constraint (only sell if not producting SAF) - REFINERIES
    def eth_selling_constraint_ref(m,i):
        return m.x[i,'etr'] <= (1-m.y[i])*m.M
    m.eth_selling_constraint_ref = pyo.Constraint(m.MILLS, rule = eth_selling_constraint_ref)

    #Summation of Ethanol Purchased - REFINERIES
    def eth_purchased_sum_ref(m,i):
        return sum(m.vol_eth_sold_ref[j,i] for j in m.MILLS)
    m.eth_purchased_sum_ref = pyo.Expression(m.REFINERIES, rule=eth_purchased_sum_ref)

    #Balance of Ethanol Purchased by Each Refinery
    def eth_purchased_ref(m,i):
        return m.x_ref[i,'et'] == m.eth_purchased_sum_ref[i]
    m.eth_purchased_ref = pyo.Constraint(m.REFINERIES, rule = eth_purchased_ref)

    #Ethanol Purchasing Constraint (only purchase if producing SAF) - REFINERIES
    def eth_purchasing_constraint_ref(m,i):
        return m.x_ref[i,'et'] <= m.y_ref[i]*m.M
    m.eth_purchasing_constraint_ref = pyo.Constraint(m.REFINERIES, rule = eth_purchasing_constraint_ref)

    #Mill to Refinery - SAF
    #Summation of SAF sold to refineries
    def saf_sold_ref_sum(m,i):
        return sum(m.vol_saf_sold_mills_ref[i,j] for j in m.REFINERIES)
    m.saf_sold_ref_sum = pyo.Expression(m.MILLS, rule = saf_sold_ref_sum)

    #Balance on SAF sold to refineries
    def saf_sold_ref(m,i):
        return m.x[i,'saf ref'] == m.saf_sold_ref_sum[i]
    m.saf_sold_ref = pyo.Constraint(m.MILLS, rule = saf_sold_ref)

    #Summation of SAF purchased - Refineries
    def saf_purchased_sum_ref(m,j):
        return sum(m.vol_saf_sold_mills_ref[i,j] for i in m.MILLS)
    m.saf_purchased_sum_ref = pyo.Expression(m.REFINERIES, rule = saf_purchased_sum_ref)

    #Balance on SAF purchased by Each Refinery
    def saf_purchased_ref(m,i):
        return m.x_ref[i,'saf ref'] == m.saf_purchased_sum_ref[i]
    m.saf_purchased_ref = pyo.Constraint(m.REFINERIES, rule = saf_purchased_ref)

    #Blended SAF Production at Refineries
    def blended_saf(m,i):
        return m.x_ref[i,'blended saf'] == m.x_ref[i,'saf'] + m.x_ref[i,'saf ref']
    m.blended_saf = pyo.Constraint(m.REFINERIES,rule=blended_saf)

    #SAF Demand Fullfillment & Investment

    #Balance on SAF sold to Airports from Mills
    def saf_sold_mills(m,i):
        return m.x[i,'saf air'] == sum(m.vol_saf_sold_mills_air[i,a] for a in m.AIRPORTS)
    m.saf_sold_mills = pyo.Constraint(m.MILLS, rule = saf_sold_mills)

    #Balance on SAF sold to airports from refineries
    def saf_sold_refs(m,i):
        return m.x_ref[i,'blended saf'] == sum(m.vol_saf_sold_ref_air[i,a] for a in m.AIRPORTS)
    m.saf_sold_refs = pyo.Constraint(m.REFINERIES, rule = saf_sold_refs)

    #Demand Requirement for SAF
    if ref_blend == False:
        def saf_demand(m,a):
            return sum(m.vol_saf_sold_mills_air[i, a] for i in m.MILLS) + sum(m.vol_saf_sold_ref_air[i,a] for i in m.REFINERIES) + m.v[a,'saf'] == m.individual_saf_demand[a]*m.blend_requirement
        m.saf_demand = pyo.Constraint(m.AIRPORTS, rule = saf_demand)

    else:
        def saf_demand(m,a):
            return sum(m.vol_saf_sold_ref_air[i,a] for i in m.REFINERIES) == m.individual_saf_demand[a]*m.blend_requirement
        m.saf_demand = pyo.Constraint(m.AIRPORTS, rule = saf_demand)

    #Demand Requirement for Conventional Jet Fuel
    def jet_demand(m):
        return m.p['f'] == sum(m.individual_saf_demand[a]*(1-m.blend_requirement) for a in m.AIRPORTS)
    m.jet_demand = pyo.Constraint(rule = jet_demand)

    #Demand Requirement for Sugar
    def sugar_demand(m):
        return sum(m.x[i,'sug'] for i in m.MILLS) + m.p['sug'] >= m.total_sugar_demand
    m.sugar_demand = pyo.Constraint(rule = sugar_demand)

    #Demand Requirement for Ground Transportation
    def ground_transport_demand(m):
        return (m.p['et'] + sum(m.x[i,'etmk'] for i in m.MILLS))*m.ethanol_energy + (m.p['g'] + sum(m.x[i,'g'] for i in m.MILLS) + sum(m.x_ref[j,'g'] for j in m.REFINERIES) + sum(m.v[a,'g'] for a in m.AIRPORTS))*m.gas_energy >= m.ground_demand
    m.ground_transport_demand = pyo.Constraint(rule = ground_transport_demand)

    #Upper Bound on Ethanol from Corn
    def ethanol_upper(m):
        return m.p['et'] <= m.ethanol_upper_bound
    m.ethanol_upper = pyo.Constraint(rule=ethanol_upper)

    # #Relate SAF production to SAF Capacity - MILLS
    # def saf_cap(m,i):
    #     return m.SAF_capacity[i] == m.x[i,'saf']
    # m.saf_cap = pyo.Constraint(m.MILLS, rule = saf_cap)

    # #Relate SAF production to SAF Capacity - AIRPORTS
    # def saf_cap_air(m,i):
    #     return m.SAF_capacity_air[i] == m.v[i,'saf']
    # m.saf_cap_air = pyo.Constraint(m.AIRPORTS, rule = saf_cap_air)

    # #Relate SAF production to SAF Capacity - REFINERIES
    # def saf_cap_ref(m,i):
    #     return m.SAF_capacity_ref[i] == m.x_ref[i,'saf']
    # m.saf_cap_ref = pyo.Constraint(m.REFINERIES, rule = saf_cap_ref)

    #SAF Investment Upper Bound - MILLS
    def SAF_investment_upper(m, i):
        return m.x[i,'saf'] <= m.y[i]*m.max_saf_capacity 
    m.saf_investment_upper = pyo.Constraint(m.MILLS, rule=SAF_investment_upper)

    #SAF Investment Lower Bound - MILLS
    def SAF_investment_lower(m, i):
        return m.x[i,'saf'] >= m.y[i]*28008
    m.saf_investment_lower = pyo.Constraint(m.MILLS, rule=SAF_investment_lower)

    #SAF Investment Upper Bound - AIRPORTS
    def SAF_investment_upper_air(m,i):
        return m.v[i,'saf'] <= m.z[i]*m.max_saf_capacity
    m.SAF_investment_upper_air = pyo.Constraint(m.AIRPORTS, rule = SAF_investment_upper_air)

    #SAF Investment Lower Bound - AIRPORTS
    def SAF_investment_lower_air(m,i):
        return m.v[i,'saf'] >= m.z[i]
    m.SAF_investment_lower_air = pyo.Constraint(m.AIRPORTS, rule=SAF_investment_lower_air)

    #SAF Investment Upper Bound - REFINERIES
    def SAF_investment_upper_ref(m,i):
        return m.x_ref[i,'saf'] <= m.y_ref[i]*m.max_saf_capacity
    m.SAF_investment_upper_ref = pyo.Constraint(m.REFINERIES, rule = SAF_investment_upper_ref)

    #SAF Investment Lower Bound - REFINERIES
    def SAF_investment_lower_ref(m,i):
        return m.x_ref[i,'saf'] >= m.y_ref[i]*28000
    m.SAF_investment_lower_ref = pyo.Constraint(m.REFINERIES, rule=SAF_investment_lower_ref)

    #Capital Cost Piece-wise Linear Approximation

    #Mills - Brownfield
    #Select the SAF Capacity Range for the Mill
    def select_input_range(m,i):
        return m.x[i,'saf'] == m.Saf_CAPEX_Inputs[0] + sum((m.Saf_CAPEX_Inputs[j+1]-m.Saf_CAPEX_Inputs[j])*m.csi[i,j] for j in m.INDEX_SET1)
    m.select_input_range = pyo.Constraint(m.MILLS, rule = select_input_range)

    #Calculate the CAPEX for each Capacity Range
    def capex_scaling_outputs(m,i):
        return (m.reference_capex*(m.Saf_CAPEX_Inputs[i]/(m.reference_flow*0.41))**m.n)/m.amortization
    m.capex_scaling_output = pyo.Expression(m.INDEX_SET3, rule = capex_scaling_outputs)
    
    # #Assign a CAPEX for the Selected Capacity Range
    # def capex_output(m,i):
    #     return m.CAPEX[i] == m.capex_scaling_output[0] + sum((m.capex_scaling_output[j+1] - m.capex_scaling_output[j])*m.csi[i,j] for j in m.INDEX_SET1)
    # m.capex_output = pyo.Constraint(m.MILLS, rule = capex_output)

    #Assign a CAPEX for the Selected Capacity Range
    def capex_output(m,i):
        return m.capex_scaling_output[0] + sum((m.capex_scaling_output[j+1] - m.capex_scaling_output[j])*m.csi[i,j] for j in m.INDEX_SET1)
    m.CAPEX = pyo.Expression(m.MILLS, rule = capex_output)

    #Enforce Capacity Ranges are Selected Sequentially 
    def auxilary_constraints1(m,i,b):
        return m.csi[i,b] >= m.aux[i,b]
    m.auxilary_constraint1 = pyo.Constraint(m.MILLS, m.INDEX_SET2, rule=auxilary_constraints1)

    #Enforce Capacity Ranges are Selected Sequentially 
    def auxilaryconstraints2(m,i,b):
        return m.aux[i,b] >= m.csi[i,b+1]
    m.auxilaryconstraint2 = pyo.Constraint(m.MILLS, m.INDEX_SET2, rule = auxilaryconstraints2)

    #Airports - Greenfield
    #Select the SAF Capacity Range for the Airport
    def select_input_range_air(m,i):
        return m.v[i,'saf'] == m.Saf_CAPEX_Inputs[0] + sum((m.Saf_CAPEX_Inputs[j+1]-m.Saf_CAPEX_Inputs[j])*m.csi_air[i,j] for j in m.INDEX_SET1)
    m.select_input_range_air = pyo.Constraint(m.AIRPORTS, rule = select_input_range_air)

    #Calculate the CAPEX for each Capacity Range
    def capex_scaling_outputs_air(m,i):
        return (m.reference_capex*(1+ m.grass_roots_factor)*(m.Saf_CAPEX_Inputs[i]/(m.reference_flow*m.Conversion['et_to_saf']))**m.n)/m.amortization
    m.capex_scaling_output_air = pyo.Expression(m.INDEX_SET3, rule = capex_scaling_outputs_air)
    
    # #Assign a CAPEX for the Selected Capacity Range
    # def capex_output_air(m,i):
    #     return m.CAPEX_air[i] == m.capex_scaling_output_air[0] + sum((m.capex_scaling_output_air[j+1] - m.capex_scaling_output_air[j])*m.csi_air[i,j] for j in m.INDEX_SET1)
    # m.capex_output_air = pyo.Constraint(m.AIRPORTS, rule = capex_output_air)

    #Assign a CAPEX for the Selected Capacity Range
    def capex_output_air(m,i):
        return m.capex_scaling_output_air[0] + sum((m.capex_scaling_output_air[j+1] - m.capex_scaling_output_air[j])*m.csi_air[i,j] for j in m.INDEX_SET1)
    m.CAPEX_air = pyo.Expression(m.AIRPORTS, rule = capex_output_air)

    #Enforce Capacity Ranges are Selected Sequentially 
    def auxilary_constraints1_air(m,i,b):
        return m.csi_air[i,b] >= m.aux_air[i,b]
    m.auxilary_constraint1_air = pyo.Constraint(m.AIRPORTS, m.INDEX_SET2, rule=auxilary_constraints1_air)

    #Enforce Capacity Ranges are Selected Sequentially 
    def auxilaryconstraints2_air(m,i,b):
        return m.aux_air[i,b] >= m.csi_air[i,b+1]
    m.auxilaryconstraint2_air = pyo.Constraint(m.AIRPORTS, m.INDEX_SET2, rule = auxilaryconstraints2_air)

    #Refineries - Greenfield
    #Select the SAF Capacity Range for the Refinery
    def select_input_range_ref(m,i):
        return m.x_ref[i,'saf'] == m.Saf_CAPEX_Inputs[0] + sum((m.Saf_CAPEX_Inputs[j+1]-m.Saf_CAPEX_Inputs[j])*m.csi_ref[i,j] for j in m.INDEX_SET1)
    m.select_input_range_ref = pyo.Constraint(m.REFINERIES, rule = select_input_range_ref)

    #Calculate the CAPEX for each Capacity Range
    def capex_scaling_outputs_ref(m,i):
        return (m.reference_capex*(1+ m.grass_roots_factor)*(m.Saf_CAPEX_Inputs[i]/(m.reference_flow*m.Conversion['et_to_saf']))**m.n)/m.amortization
    m.capex_scaling_output_ref = pyo.Expression(m.INDEX_SET3, rule = capex_scaling_outputs_ref)
    
    # #Assign a CAPEX for the Selected Capacity Range
    # def capex_output_ref(m,i):
    #     return m.CAPEX_ref[i] == m.capex_scaling_output_ref[0] + sum((m.capex_scaling_output_ref[j+1] - m.capex_scaling_output_ref[j])*m.csi_ref[i,j] for j in m.INDEX_SET1)
    # m.capex_output_ref = pyo.Constraint(m.REFINERIES, rule = capex_output_ref)

    #Assign a CAPEX for the Selected Capacity Range
    def capex_output_ref(m,i):
        return m.capex_scaling_output_ref[0] + sum((m.capex_scaling_output_ref[j+1] - m.capex_scaling_output_ref[j])*m.csi_ref[i,j] for j in m.INDEX_SET1)
    m.CAPEX_ref = pyo.Expression(m.REFINERIES, rule = capex_output_ref)

    #Enforce Capacity Ranges are Selected Sequentially 
    def auxilary_constraints1_ref(m,i,b):
        return m.csi_ref[i,b] >= m.aux_ref[i,b]
    m.auxilary_constraint1_ref = pyo.Constraint(m.REFINERIES, m.INDEX_SET2, rule=auxilary_constraints1_ref)

    #Enforce Capacity Ranges are Selected Sequentially 
    def auxilaryconstraints2_ref(m,i,b):
        return m.aux_ref[i,b] >= m.csi_ref[i,b+1]
    m.auxilaryconstraint2_ref = pyo.Constraint(m.REFINERIES, m.INDEX_SET2, rule = auxilaryconstraints2_ref)


    #Objective Components
    #Opex - External Costs Only
    def opex_sum(m):
        return sum(m.cost['sug']*m.x[i,'sug'] + m.cost['et']*m.x[i,'et'] + m.cost['saf']*m.x[i,'saf'] + m.cost['el']*m.x[i,'el'] for i in m.MILLS) + sum(m.greenfield_opex_air*m.v[j,'saf'] for j in m.AIRPORTS) + sum(m.greenfield_opex_ref*m.x_ref[j,'saf'] for j in m.REFINERIES)
    m.opex_sum = pyo.Expression(rule = opex_sum)

    #Individual OPEX - Mills
    def individual_opex_mill(m,i):
        return m.cost['sug']*m.x[i,'sug'] + m.cost['et']*m.x[i,'et'] + m.cost['saf']*m.x[i,'saf'] + m.cost['el']*m.x[i,'el'] 
    m.individual_opex_mill = pyo.Expression(m.MILLS, rule=individual_opex_mill)

    #Individual OPEX - Airport
    def individual_opex_air(m,i):
        return m.greenfield_opex_air*m.v[i,'saf']
    m.individual_opex_air = pyo.Expression(m.AIRPORTS, rule = individual_opex_air)

    #Individual OPEX - Refinery
    def individual_opex_ref(m,i):
        return m.greenfield_opex_ref*m.x_ref[i,'saf']
    m.individual_opex_ref = pyo.Expression(m.REFINERIES, rule = individual_opex_ref)

    #Individual Revenue - Mills
    def individual_rev_mill(m,i):
        return m.price['sug']*m.x[i,'sug'] + m.price['et']*m.x[i,'etmk'] + (m.price['et'] + m.eth_prem)*(m.x[i,'etr'] + m.x[i,'etref'])+ m.price['el']*m.x[i,'el'] + (m.price['saf'] + m.saf_premium)*m.x[i,'saf']
    m.individual_rev_mills = pyo.Expression(m.MILLS, rule = individual_rev_mill)

    #Total Revenue
    def total_rev(m):
        return sum(m.individual_rev_mills[i] for i in m.MILLS)
    m.total_rev = pyo.Expression(rule = total_rev)

    # #Individual Mill to Mill Logistic Cost
    # def individual_mill_to_mill_log_cost(m,i):
    #     return sum((m.logistic_cost*m.mill_distance[i,j]* m.vol_eth_sold[i,j]  + m.fixed_logistic_cost*m.vol_eth_sold[i,j]) for j in m.MILLS if i != j)
    # m.individual_mill_to_mill_log_cost = pyo.Expression(m.MILLS, rule = individual_mill_to_mill_log_cost)

    #Individual Mill to Mill Logistic Cost
    def individual_mill_to_mill_log_cost(m,j):
        return sum((m.logistic_cost*m.mill_distance[i,j]* m.vol_eth_sold[i,j]  + m.fixed_logistic_cost*m.vol_eth_sold[i,j]) for i in m.MILLS if i != j)
    m.individual_mill_to_mill_log_cost = pyo.Expression(m.MILLS, rule = individual_mill_to_mill_log_cost)

    #Mill to Mill Logistic Cost
    def mill_to_mill_logsitic_cost(m):
        return sum(sum((m.logistic_cost*m.mill_distance[i,j]* m.vol_eth_sold[i,j]  + m.fixed_logistic_cost*m.vol_eth_sold[i,j]) for i in m.MILLS if i != j) for j in m.MILLS if i != j ) 
    m.mill_to_mill_logistic_cost = pyo.Expression(rule = mill_to_mill_logsitic_cost)

    #Individual Mill to Airport Logistic Cost
    def individual_mill_to_airport_log_cost(m,j):
        return sum(m.logistic_cost*m.airport_distance[i,j]* (m.vol_saf_sold_mills_air[j,i] + m.vol_eth_sold_air[j,i]) + m.fixed_logistic_cost*(m.vol_saf_sold_mills_air[j,i]+ m.vol_eth_sold_air[j,i]) for i in m.AIRPORTS)
    m.individual_mill_to_airport_log_cost = pyo.Expression(m.MILLS, rule=individual_mill_to_airport_log_cost)

    #Mill to Airport Logistic Cost
    def mill_to_airport_logistic_cost(m):
        return sum(sum((m.logistic_cost*m.airport_distance[i,j]* (m.vol_saf_sold_mills_air[j,i]+ m.vol_eth_sold_air[j,i]) + m.fixed_logistic_cost*(m.vol_saf_sold_mills_air[j,i] + m.vol_eth_sold_air[j,i])) for i in m.AIRPORTS) for j in m.MILLS)
    m.mill_to_airport_logistic_cost = pyo.Expression(rule = mill_to_airport_logistic_cost)

    #Individual Mill to Refinery Logistic Cost
    def individual_mill_to_ref_log_cost(m,j):
        return sum(m.logistic_cost*m.mill_ref_distance[i,j]* (m.vol_saf_sold_mills_ref[j,i] + m.vol_eth_sold_ref[j,i]) + m.fixed_logistic_cost*(m.vol_saf_sold_mills_ref[j,i]+ m.vol_eth_sold_ref[j,i]) for i in m.REFINERIES)
    m.individual_mill_to_ref_log_cost = pyo.Expression(m.MILLS, rule = individual_mill_to_ref_log_cost)

    #Mill to Refinery Logistic Cost
    def mill_to_ref_logistic_cost(m):
        return sum(m.individual_mill_to_ref_log_cost[i] for i in m.MILLS)
    m.mill_to_ref_logistic_cost = pyo.Expression(rule=mill_to_ref_logistic_cost)

    #Individual Refinery to Airport Logistic Cost
    def individual_ref_to_airport_log_cost(m,i):
        return sum(m.logistic_cost*m.ref_air_distance[i,j]* (m.vol_saf_sold_ref_air[i,j]) + m.fixed_logistic_cost*(m.vol_saf_sold_ref_air[i,j]) for j in m.AIRPORTS)
    m.individual_ref_to_airport_log_cost = pyo.Expression(m.REFINERIES, rule = individual_ref_to_airport_log_cost)

    #Refinery to Airport Logistic Cost
    def ref_to_air_logistic_cost(m):
        return sum(m.individual_ref_to_airport_log_cost[i] for i in m.REFINERIES)
    m.ref_to_air_logistic_cost = pyo.Expression(rule=ref_to_air_logistic_cost)

    #Capex
    def capex_sum(m):
        return sum(m.CAPEX[i] for i in m.MILLS) + sum(m.CAPEX_air[j] for j in m.AIRPORTS) + sum(m.CAPEX_ref[i] for i in m.REFINERIES)
    m.capex_sum = pyo.Expression(rule = capex_sum)

    #Additional Costs - external costs only
    def additional_costs(m):
        return m.price['sug']*m.p['sug'] + m.price['saf']*m.p['f'] + m.price['et']*m.p['et'] + m.price['g']*m.p['g']
    m.additional_costs = pyo.Expression(rule = additional_costs)

    #Individual Profits
    def individual_prof(m,i):
        return m.individual_rev_mills[i] + m.s[i] - (m.individual_opex_mill[i] + m.price['et']*m.x[i,'etpc'] + m.CAPEX[i] + m.individual_mill_to_ref_log_cost[i] + m.individual_mill_to_airport_log_cost[i] + m.individual_mill_to_mill_log_cost[i])
    m.ind_profs = pyo.Expression(m.MILLS, rule=individual_prof)

    # #Positive Profit Constraint/Min Profit Constraint
    # def positive_profs(m,i):
    #     return m.ind_profs[i] >= m.reference_profit1b[i]
    # m.pos_profs = pyo.Constraint(m.MILLS, rule = positive_profs)

    #Positive Profit Constraint/Min Profit Constraint
    def positive_profs(m,i):
        return m.ind_profs[i] >= 0
    m.pos_profs = pyo.Constraint(m.MILLS, rule = positive_profs)

    #Total Mill Profit Expression
    def profit_expression(m):
        return m.total_rev - (sum(m.individual_opex_mill[i] for i in m.MILLS) + sum(m.price['et']*m.x[i,'etpc'] for i in m.MILLS) + m.mill_to_mill_logistic_cost + m.mill_to_airport_logistic_cost + m.mill_to_ref_logistic_cost + sum(m.CAPEX[i] for i in m.MILLS))
    m.profit_expression = pyo.Expression(rule = profit_expression)

    #Total Supply Chain Cost Expression
    def sc_cost_expression(m):
        return m.opex_sum + m.mill_to_mill_logistic_cost + m.mill_to_airport_logistic_cost + m.mill_to_ref_logistic_cost + m.ref_to_air_logistic_cost + m.capex_sum + m.additional_costs + sum(m.s[i] for i in m.MILLS)
    m.sc_cost_expression = pyo.Expression(rule = sc_cost_expression)

    # if profit_obj == True:
    #     #OBJECTIVE
    #     def objective(m):
    #         return m.total_rev - (m.opex_sum + m.mill_to_mill_logistic_cost + m.mill_to_airport_logistic_cost + m.mill_to_ref_logistic_cost + m.ref_to_air_logistic_cost + m.capex_sum + m.additional_costs)
    #     m.objective = pyo.Objective(rule = objective, sense = pyo.maximize)

    # else:
    #     #OBJECTIVE
    #     def objective(m):
    #         return m.opex_sum + m.mill_to_mill_logistic_cost + m.mill_to_airport_logistic_cost + m.mill_to_ref_logistic_cost + m.ref_to_air_logistic_cost + m.capex_sum + m.additional_costs
    #     m.objective = pyo.Objective(rule = objective, sense = pyo.minimize)
        
    if profit_obj == True:
        #OBJECTIVE
        def objective(m):
            return m.profit_expression
        m.objective = pyo.Objective(rule = objective, sense = pyo.maximize)

    else:
        #OBJECTIVE
        def objective(m):
            return m.sc_cost_expression
        m.objective = pyo.Objective(rule = objective, sense = pyo.minimize)
        #def objective(m):
            #return m.mill_to_ref_logistic_cost + m.ref_to_air_logistic_cost
        #m.objective = pyo.Objective(rule = objective, sense = pyo.minimize)
        

    return m
