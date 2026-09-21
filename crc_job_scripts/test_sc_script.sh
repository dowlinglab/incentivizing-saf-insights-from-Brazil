#!/bin/bash
#$ -M YOUR_NETID@nd.edu
#$ -m abe
#$ -q long
#$ -N run_sc_model
conda activate /afs/crc/user/<n>/<netid>/.conda/envs/<env>
export LD_LIBRARY_PATH=~/afs/crc/user/<n>/<netid>/.conda/envs/<env>/lib:$LD_LIBRARY_PATH 
module load gurobi/11.0.2
python run_unconstrained_SAF_prem_sensitivity.py
