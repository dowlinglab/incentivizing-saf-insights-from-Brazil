from create_maps import *

#Generates interactive maps for the optimal supply chain design including infrastructure locations and connections

results_folder1 = "Case1" #Specify the case study the results folder the solution comes from

results_folder2 = 'interest_mid_blend_50' #Specify the blend requirement results folder the solution comes from

create_model_map(results_folder1,results_folder2)
