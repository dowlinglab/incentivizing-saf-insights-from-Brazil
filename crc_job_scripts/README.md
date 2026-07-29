# CRC job scripts

How the long runs were submitted on the Notre Dame CRC, copied from the private
repository and sanitised: the personal e-mail address and AFS paths are replaced
with placeholders (`YOUR_NETID`, `<n>`, `<netid>`, `<env>`). Fill those in before
submitting.

- `run_sc_model_job.py` writes a Sun Grid Engine script and `qsub`s it.
- `test_sc_script.sh` is the generated script, kept as an example.

Note `module load gurobi/11.0.2` — the solver logs from these runs report Gurobi
**12.0.2**, and the manuscript names **10.0.3**. See PROVENANCE.md.
