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
import os
import sys
import pandas as pd
import matplotlib.pyplot as plt

# Automatically set absolute path to the working directory (..DARKO/)
sys.path.append(os.path.abspath('..'))

# Import DARKO model
import darko as dk

# Load the configuration file
config = dk.load_config_excel('../ConfigFiles/ConfigBP.xlsx')

# Limit the simulation period (for testing purposes, comment the line to run the range from the config file)
# config['StartDate'] = (2016, 1, 1, 0, 0, 0)
# config['StopDate'] = (2016, 1, 7, 0, 0, 0)

# Build the simulation environment:
#SimData = dk.build_simulation(config)

# Solve using GAMS:
#r = dk.solve_GAMS(config['SimulationDirectory'], config['GAMS_folder'])

# Load the simulation results:
inputs, results = dk.get_sim_results(config['SimulationDirectory'], cache=False)

# Load range
rng = pd.date_range('2020-2-1', '2020-3-31', freq='h')

# Plot Net Positions
#dk.plot_net_positions(dk.get_net_position_plot_data(inputs,results,z='Z2'),rng=rng)
#dk.plot_net_positions(dk.get_net_position_plot_data(inputs, results, z='BE'))

# Plot Market Clearing Price
#mcp, vol = dk.plot_market_clearing_price((dk.get_marginal_price_plot_data(inputs, results, zones=['Z1'])), rng=rng)
#mcp, vol = dk.plot_market_clearing_price((dk.get_marginal_price_plot_data(inputs, results, zones=['BE', 'DE', 'NL', 'UK'])), alpha=0.7)

# Plot dispatch plot
dk.Energy_by_fuel_graph(inputs,results,rng=rng)
# Plot renewable energy - MCP plots
dk.renewable_plots(inputs, results, rng=rng, z="BE")
# Plot Ichimoku plot
dk.Ichimoku(inputs, results, rng=rng, z="BE")

