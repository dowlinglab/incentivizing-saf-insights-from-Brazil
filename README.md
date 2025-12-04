# incentivizing-saf-insights-from-brazil
Supporting codes for "Incentivizing Sustainable Aviation Fuel: Supply Chain and Policy Insights from Brazil."

## Dependencies
The scripts in this repository build an optimization model via Pyomo (v6.6.1) and solve using Gurobi (v10.0.3).

## Repository Content
The content of this repository is detailed below:
### Python Scripts
create_sc_model_full: contains a function to create and initialize the optimization model

create_maps: contains a function to create interactive maps of the optimal supply chain designs

run_blend_and_opt_sensitivity: contains a script to run a sensitivty analysis varying the decision-making paradigm and SAF blend requirement solving instances of create_sc_model_full and collect results data

run_create_maps: contains a script to run create_maps for different case studies

run_integer_cuts: contains a script to run an integer cut analysis on the optimal supply chain design and collect results data

run_mill_specific_incentives: contains a script to run instances of create_sc_model_full where mill-specific incentives are a variable to be optimized and collect results data

run_unconstrained_SAF_prem_sensitivity: contains a script to run instances of create_sc_model_full with no required SAF production at various SAF premium prices and collect results data

### Jupyter Notebooks
IntegerCutAnalysis: make plots to visualize the integer cut analysis results (maps)

SensitivityAnalysis: make plots to visualize the incentive sensitivty study to production incentives (line plot), SAF premium prices (line plot), and mill-specific incentives (bar chart and line plot)

SupplyChainMaps: make plots to visualize the optimal supply chain infrastructure locations for each case study (maps)

SupplyChainSummary: make plots to visualize the supply chain flows in the optimal design (line plot) and emissions sensitivity to ATJ technology (contour plot)

### Folders
Case1: results files from run_blend_and_opt_sensitivity for Case 1

Case2: results files from run_blend_and_opt_sensitivity for Case 2

Case3: results files from run_blend_and_opt_sensitivity for Case 3

Case4: results files from run_blend_and_opt_sensitivity for Case 4

integer_cuts_case1: results files from run_integer_cuts for Case 1

integer_cuts_case3: results files from run_integer_cuts for Case 3

mill_specific_incentives: results files from run_mill_specific_incentives

unconstrained_SAF: results files from run_unconstrained_SAF_prem_sensitivity

Results_Figures: all figures produced for the manuscript

### Other Files
README: this file

335MillsLatitudesLongitudes: excel file containing latitude and longitude data for all sugarcane mills in the supply chain

AirportsLatitudeLongitude: excel file containing latitude and longitude data for all airports in the supply chain

base_case_data_with_demands: excel file containing input data to the supply chain model including distances between infrastructure, capacity, demand, price, conversion, and cost data

integer_cut_organized_data: excel file containing organized results data from integer_cuts_case1 and integer_cuts_case3 for easy plotting

OilRefineriesLatLong: excel file containing latitude and longitude data for all refineries in the supply chain

gadm41_BRA_1: database file from the GADM database containing geographic data from Brazil to create map figures in python

gadm41_BRA_1: shape file from the GADM database containing geographic data from Brazil to create map figures in python

gadm41_BRA_1: shape index file from the GADM database containing geographic data from Brazil to create map figures in python
