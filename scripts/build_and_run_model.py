# -*- coding: utf-8 -*-
"""
This script runs the DARKO model. The main steps are:
    - Load DARKO
    - Load the config file for the model
    - build the mode
    - run the model
    - display and analyse the results

@author: Matija Pavičević
"""

# Add the root folder of DARKO to the path so that the library can be loaded:
import sys,os
sys.path.append(os.path.abspath('..'))

# Import Dispa-SET
import darko as dk

# Load the configuration file
config = dk.load_config_excel('../ConfigFiles/ConfigTest.xlsx')

# Limit the simulation period (for testing purposes, comment the line to run the whole year)
#config['StartDate'] = (2016, 1, 1, 0, 0, 0)
#config['StopDate'] = (2016, 1, 7, 0, 0, 0)

# Build the simulation environment:
SimData = dk.build_simulation(config)

## Solve using GAMS:
#_ = ds.solve_GAMS(config['SimulationDirectory'], config['GAMS_folder'])
#
## Load the simulation results:
#inputs,results = ds.get_sim_results(config['SimulationDirectory'],cache=False)