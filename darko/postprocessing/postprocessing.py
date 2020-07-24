"""
Set of functions useful to analyse to DispaSET output data.

@author: Matija Pavičević
"""

import datetime as dt
import logging
import sys

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from ..common import commons
from .data_handler import dk_to_df


def filter_by_zone(OutputData, inputs, z):
    """
    This function filters the Outputs dataframe by zone

    :param OutputData:      Dataframe of power generation with units as columns and time as index
    :param inputs:          DARKO inputs
    :param z:               Selected zone (e.g. 'BE')
    :returns Power:         Dataframe with power generation by zone
    """
    loc = inputs['units']['Zone']
    Data = OutputData.loc[:, [u for u in OutputData.columns if loc[u] == z]]
    return Data


def filter_by_tech(OutputData, inputs, t):
    """
    This function filters the Output dataframe by technology

    :param OutputData:    Dataframe of power generation with units as columns and time as index
    :param inputs:        DARKO inputs
    :param t:             Selected tech (e.g. 'HOBO')
    :returns Power:
    """
    loc = inputs['units']['Technology']
    Data = OutputData.loc[:, [u for u in OutputData.columns if loc[u] == t]]
    return Data


def get_imports(flows, z):
    """
    Function that computes the balance of the imports/exports of a given zone

    :param flows:           Pandas dataframe with the timeseries of the exchanges
    :param z:               Zone to consider
    :returns NetImports:    Scalar with the net balance over the whole time period
    """
    NetImports = 0
    for key in flows:
        if key[:len(z)] == z:
            NetImports -= flows[key].sum()
        elif key[-len(z):] == z:
            NetImports += flows[key].sum()
    return NetImports


def get_net_position_plot_data(inputs, results, z):
    """
    Function that analyzes net position data

    :param inputs:      darko inputs
    :param results:     simmulation results
    :param z:           zone used for plot
    :return:
    """

    MaxDemand = inputs['demands'].loc[inputs['demands']['Zone'] == z]['MaxDemand'].agg('sum')

    data = pd.DataFrame()
    data_all = pd.DataFrame()

    data.loc[:, 'HourlyNetPosition'] = results['OutputNetPositionOfBiddingArea'].loc[:, z]
    data_all.loc[:, 'DailyNetPosition'] = results['OutputDailyNetPositionOfBiddingArea'].loc[:, z]

    data.loc[:, 'MinHourlyNetPosition'] = data.loc[:, 'HourlyNetPosition'] - \
                                          inputs['config']['default']['NodeHourlyRampDown'] * MaxDemand
    data.loc[:, 'MaxHourlyNetPosition'] = data.loc[:, 'HourlyNetPosition'] + \
                                          inputs['config']['default']['NodeHourlyRampDown'] * MaxDemand
    data.loc[:, ['MinHourlyNetPosition', 'MaxHourlyNetPosition']] = \
        data.loc[:, ['MinHourlyNetPosition', 'MaxHourlyNetPosition']].shift(periods=1).fillna(data.iloc[0, 0])

    data_all.loc[:, 'MinDailyNetPosition'] = data_all.loc[:, 'DailyNetPosition'] - \
                                             inputs['config']['default']['NodeDailyRampDown'] * MaxDemand * 24 * \
                                             inputs['config']['HorizonLength']
    data_all.loc[:, 'MaxDailyNetPosition'] = data_all.loc[:, 'DailyNetPosition'] + \
                                             inputs['config']['default']['NodeDailyRampDown'] * MaxDemand * 24 * \
                                             inputs['config']['HorizonLength']
    data_all.loc[:, ['MinDailyNetPosition', 'MaxDailyNetPosition']] = \
        data_all.loc[:, ['MinDailyNetPosition', 'MaxDailyNetPosition']].shift(periods=1).fillna(data_all.iloc[0, 0])

    return data, data_all, z


def plot_net_positions(data, rng=None, alpha=0.7, figsize=(10, 5)):
    """
    Plot net positions in the selected zone

    :param data:        data obtained from the get_net_position_plot_data function
    :param rng:         date range for plot
    :param alpha:       alpha for the color
    :param figsize:     figure size
    :return:
    """
    if rng is None:
        pdrng = data[0].index[:min(len(data[0]) - 1, 7 * 24)]
        pdrng_day = data[1].index[:min(len(data[1]) - 1, 7 * 24)]
    elif not type(rng) == type(data[0].index):
        logging.error('The "rng" variable must be a pandas DatetimeIndex')
        raise ValueError()
    elif not type(rng) == type(data[1].index):
        logging.error('The "rng" variable must be a pandas DatetimeIndex')
        raise ValueError()
    elif rng[0] < data[0].index[0] or rng[0] > data[0].index[-1] or rng[-1] < data[0].index[0] or rng[-1] > data[0].index[-1]:
        logging.warning('Plotting range is not properly defined, considering the first simulated week')
        pdrng = data[0].index[:min(len(data[0]) - 1, 7 * 24)]
    elif rng[0] < data[1].index[0] or rng[0] > data[1].index[-1] or rng[-1] < data[1].index[0] or rng[-1] > data[1].index[-1]:
        logging.warning('Plotting range is not properly defined, considering the first simulated week')
        pdrng_day = data[1].index[:min(len(data[1]) - 1, 7 * 24)]
    else:
        pdrng = rng
        pdrng_day = data[1].index

    fig, axes = plt.subplots(nrows=2, ncols=1, sharex=False, figsize=figsize, frameon=True,
                             gridspec_kw={'height_ratios': [1, 1], 'hspace': 0.2})

    axes[0].plot(pdrng, data[0].loc[pdrng, 'HourlyNetPosition'].values, color='red')
    axes[0].fill_between(pdrng, y1=data[0].loc[pdrng, 'MinHourlyNetPosition'].values,
                         y2=data[0].loc[pdrng, 'MaxHourlyNetPosition'].values,
                         facecolor='#fad414', alpha=alpha)
    axes[0].set_ylabel('Hourly Net Position [MWh]')
    axes[0].set_title('Net Positions in ' + data[2])
    axes[0].axhline(linewidth=1, color='gray')
    axes[0].grid(True)
    axes[1].plot(pdrng_day, data[1].loc[pdrng_day, 'DailyNetPosition'].values, color='red')
    axes[1].fill_between(pdrng_day, y1=data[1].loc[pdrng_day, 'MinDailyNetPosition'].values,
                         y2=data[1].loc[pdrng_day, 'MaxDailyNetPosition'].values,
                         facecolor='#ade9f7', alpha=alpha)
    axes[1].set_ylabel('Daily Net Position [MWh]')
    axes[1].axhline(linewidth=1, color='gray')
    axes[1].grid(True)
    plt.show()

def get_marginal_price_plot_data(inputs, results, zones):
    """
    Plot marginal price in selected zones

    :param inputs:
    :param results:
    :param zones:
    :return:
    """
    mcp = results['OutputMarginalPrice'].loc[:, zones]

    return mcp

def plot_market_clearing_price(data, rng, alpha=0.7, figsize=(10, 5)):
    """

    :param data:
    :param rng:
    :param alpha:
    :param figsize:
    :return:
    """

    from matplotlib.pyplot import cm

    if rng is None:
        pdrng = data.index[:min(len(data) - 1, 7 * 24)]
    elif not type(rng) == type(data.index):
        logging.error('The "rng" variable must be a pandas DatetimeIndex')
        raise ValueError()
    elif rng[0] < data.index[0] or rng[0] > data.index[-1] or rng[-1] < data.index[0] or rng[-1] > data.index[-1]:
        logging.warning('Plotting range is not properly defined, considering the first simulated week')
        pdrng = data.index[:min(len(data) - 1, 7 * 24)]
    else:
        pdrng = rng

    fig, axes = plt.subplots(nrows=2, ncols=1, sharex=False, figsize=figsize, frameon=True,
                             gridspec_kw={'height_ratios': [1, 1], 'hspace': 0.2})

    color = iter(cm.rainbow(np.linspace(0, 1, len(data.columns))))
    for z in data.columns:
        c = next(color)
        axes[0].plot(pdrng, data.loc[pdrng, z].values, color=c)
    axes[0].set_ylabel('MCP [EUR/MWh]')
    axes[0].set_title('Market Clearing Price in ' + listToString(data.columns))
    axes[0].axhline(linewidth=1, color='gray')
    axes[0].grid(True)

    plt.show()


def listToString(s):
    # initialize an empty string
    str1 = " "

    # return string
    return (str1.join(s))


