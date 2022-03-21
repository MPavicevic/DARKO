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

# Plot Net Positions
rng = pd.date_range('2020-1-1', '2020-1-5', freq='h')
# dk.plot_net_positions(dk.get_net_position_plot_data(inputs,results,z='Z2'),rng=rng)
#dk.plot_net_positions(dk.get_net_position_plot_data(inputs, results, z='BE'))

# Plot Market Clearing Price
#mcp, vol = dk.plot_market_clearing_price((dk.get_marginal_price_plot_data(inputs, results, zones=['Z1'])), rng=rng)
#mcp, vol = dk.plot_market_clearing_price((dk.get_marginal_price_plot_data(inputs, results, zones=['BE', 'DE', 'NL', 'UK'])), alpha=0.7)

#dk.Energy_by_fuel_graph(inputs,results,rng)

def Ishimoku(inputs, results, rng=None):

    import matplotlib.patches as mpatches
    import matplotlib.lines as mlines
    import matplotlib.pyplot as plt
    import pandas as pd
    from darko import commons
    mcp, vol, price, price_cstc = dk.get_marginal_price_plot_data(inputs, results, zones=['BE', 'DE', 'NL', 'UK'])
    mcp_min = mcp.groupby(pd.Grouper(freq='D')).min()
    mcp_max = mcp.groupby(pd.Grouper(freq='D')).max()
    mcp_mean = mcp.groupby(pd.Grouper(freq='D')).mean()
    mcp_open = mcp.between_time('00:00:00', '00:00:30')
    mcp_close = mcp.between_time('23:00:00', '23:00:30')

    prices = {}
    #for z in inputs['sets']['n']:
    for z in ['BE']:
        prices[z] = pd.DataFrame()
        prices[z].loc[:, 'open'] = mcp_open.loc[:, z]
        prices[z].loc[:, 'close'] = mcp_close.loc[:, z].values
        prices[z].loc[:, 'high'] = mcp_max.loc[:, z]
        prices[z].loc[:, 'low'] = mcp_min.loc[:, z]


    pd.plotting.register_matplotlib_converters()


    # create figure
    plt.figure()

    figsize = (9, 5)
    fig1, axes = plt.subplots(figsize=figsize, frameon=True)
    # define width of candlestick elements
    width = .4
    width2 = .05

    # define up and down prices
    up = prices['BE'][prices['BE'].close >= prices['BE'].open]
    down = prices['BE'][prices['BE'].close < prices['BE'].open]

    # define colors to use
    col1 = 'green'
    col2 = 'red'

    # plot up prices
    axes.bar(up.index, up.close - up.open, width, bottom=up.open, color=col1)
    axes.bar(up.index, up.high - up.close, width2, bottom=up.close, color=col1)
    axes.bar(up.index, up.low - up.open, width2, bottom=up.open, color=col1)

    # plot down prices
    axes.bar(down.index, down.close - down.open, width, bottom=down.open, color=col2)
    axes.bar(down.index, down.high - down.open, width2, bottom=down.open, color=col2)
    axes.bar(down.index, down.low - down.close, width2, bottom=down.close, color=col2)

    # rotate x-axis tick labels
    #axes.set_xticklabels(rotation=45, ha='right', )

    d = pd.DataFrame()

    # Tenkan-sen (Conversion Line): (9-period high + 9-period low)/2))
    period9_high = prices['BE']['high'].rolling(window=9, center=True, min_periods=1).mean()
    period9_low = prices['BE']['low'].rolling(window=9, center=True, min_periods=1).mean()
    d['Tenkan Sen'] = (period9_high + period9_low) / 2

    # Kijun-sen (Base Line): (26-period high + 26-period low)/2))
    period26_high = prices['BE']['high'].rolling(center=True, min_periods=1, window=26).mean()
    period26_low = prices['BE']['low'].rolling(center=True, min_periods=1, window=26).mean()
    d['Kijun Sen'] = (period26_high + period26_low) / 2

    # Senkou Span A (Leading Span A): (Conversion Line + Base Line)/2))
    d['Senkou Span A'] = ((d['Tenkan Sen'] + d['Kijun Sen']) / 2).shift(26)

    # Senkou Span B (Leading Span B): (52-period high + 52-period low)/2))
    period52_high = prices['BE']['high'].rolling(center=True, min_periods=1, window=52).mean()
    period52_low = prices['BE']['low'].rolling(center=True, min_periods=1, window=52).mean()
    d['Senkou Span B'] = ((period52_high + period52_low) / 2).shift(26)

    # The most current closing price plotted 22 time periods behind
    d['Chikou Span'] = prices['BE']['close'].shift(-22)  # 22 according to investopedia

    tmp = d.loc[:, ['Senkou Span A', 'Senkou Span B', 'Kijun Sen', 'Tenkan Sen', 'Chikou Span']].tail(300)
    tmp = tmp.reset_index()

    x1=tmp['index'].values
    y1=tmp['Senkou Span A'].values
    y2=tmp['Senkou Span B'].values

    tmp.plot(x='index', y='Senkou Span A', ax=axes, kind='line', color='green', alpha=0.7)
    tmp.plot(x='index', y='Senkou Span B', ax=axes, kind='line', color='red', alpha=0.7)
    axes.fill_between(x1, y1, y2, where=y2 > y1, facecolor='green')
    axes.fill_between(x1, y1, y2, where=y1 > y2, facecolor='red')

    tmp.plot(x='index', y='Tenkan Sen', ax=axes, kind='line', color='blue', alpha=0.2)
    tmp.plot(x='index', y='Kijun Sen', ax=axes, kind='line', color='purple', alpha=0.2)
    tmp.plot(x='index', y='Chikou Span', ax=axes, kind='line', color='orange', alpha=0.3)

    # Add titles
    axes.set_ylabel('MCP [EUR/MWh]')
    axes.set_xlabel('Date\n')
    axes.set_title('Ishimoku for the Belgian market\n', fontweight='bold')

    # Display everything
    plt.show()


dk.Ishimoku(inputs, results, rng)