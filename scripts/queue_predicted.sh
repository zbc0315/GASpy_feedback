#!/bin/sh -l

#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --time=00:30:00
#SBATCH --partition=regular
#SBATCH --job-name=queue_predicted
#SBATCH --output=queue_predicted-%j.out
#SBATCH --error=queue_predicted-%j.error
#SBATCH --constraint=haswell

# Load the input argument (i.e., the number of requested submissions).
# Defaults to 100 total submissions. Note that you should change `n_systems` manually
# if you add or subtract systems
n_submissions=${1:-100}
n_systems=2
submissions_per_system=$((n_submissions / n_systems))

# Load GASpy environment and variables
. ~/GASpy/.load_env.sh

# CO2RR:  Tell Luigi to queue various simulations based on a model's predictions
PYTHONPATH=$PYTHONPATH luigi \
    --module gaspy_feedback.feedback Predictions \
    --ads-list '["CO"]' \
    --prediction-min -2.6 \
    --prediction-max 1.4 \
    --prediction-target -0.60 \
    --predictions-location '/global/project/projectdirs/m2755/GASpy/GASpy_regressions/pkls/CO2RR_predictions_GP_around_TPOT_FEATURES_coordcount_neighbors_coordcounts_RESPONSES_energy_BLOCKS_adsorbate.pkl' \
    --priority 'gaussian' \
    --block '("CO",)' \
    --xc 'rpbe' \
    --max-submit $submissions_per_system \
    --scheduler-host $LUIGI_PORT \
    --workers=1 \
    --log-level=WARNING \
    --worker-timeout 300 

# HER:  Tell Luigi to queue various simulations based on a model's predictions
PYTHONPATH=$PYTHONPATH luigi \
    --module gaspy_feedback.feedback Predictions \
    --ads-list '["H"]' \
    --prediction-min -2.28 \
    --prediction-max 1.72 \
    --prediction-target -0.28 \
    --predictions-location '/global/project/projectdirs/m2755/GASpy/GASpy_regressions/pkls/HER_predictions_GP_around_TPOT_FEATURES_coordcount_neighbors_coordcounts_RESPONSES_energy_BLOCKS_adsorbate.pkl' \
    --priority 'gaussian' \
    --block '("H",)' \
    --xc 'rpbe' \
    --max-submit $submissions_per_system \
    --scheduler-host $LUIGI_PORT \
    --workers=1 \
    --log-level=WARNING \
    --worker-timeout 300 
