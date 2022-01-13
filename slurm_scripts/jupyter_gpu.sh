#!/bin/bash
#SBATCH --job-name=2-hours-jupyter
#SBATCH --ntasks=1                  # Run only one task
#SBATCH --output=slurm/jupyter.log    # Output name (%j is replaced by job ID)
#SBATCH --error=slurm/jupyter.log     # Output errors (optional)
#SBATCH --partition=ialab-high
#SBATCH --nodelist=scylla
#SBATCH --workdir=/home/jiossandon/storage/instructions-follower   # Where to run the job
#SBATCH --gres=gpu # Request one GPU
#SBATCH --time=2:00:00

pwd; hostname; date

source /home/jiossandon/repos/360-visualization/r2r/bin/activate
export MPLBACKEND=TKAgg

echo "Starting notebook requesting one GPU"
python3.6 /home/jiossandon/storage/instructions-follower/main.py
