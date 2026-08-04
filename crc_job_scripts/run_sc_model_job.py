import os

this_file_path = os.path.dirname(os.path.realpath(__file__))
print(this_file_path)

def submit_job():
    # create a directory to save job scripts
    job_scripts_dir = os.path.join(this_file_path, "sim_job_scripts")
    if not os.path.isdir(job_scripts_dir):
        os.mkdir(job_scripts_dir)

    file_name = os.path.join(job_scripts_dir, f"test_sc_script.sh")
    with open(file_name, "w") as f:
        f.write(
            "#!/bin/bash\n"
            + "#$ -M YOUR_NETID@nd.edu\n"
            + "#$ -m abe\n"
            + "#$ -q long\n"
            + "#$ -N run_sc_model\n"
            + "conda activate /afs/crc/user/<n>/<netid>/.conda/envs/<env>\n"
            + "export LD_LIBRARY_PATH=~/afs/crc/user/<n>/<netid>/.conda/envs/<env>/lib:$LD_LIBRARY_PATH \n" 
            + "module load gurobi/11.0.2\n"
            + "python run_unconstrained_SAF_prem_sensitivity.py"
        )

    os.system(f"qsub {file_name}")

submit_job()