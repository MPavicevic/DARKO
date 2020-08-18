"""
Set of functions useful to analyse to DispaSET output data.

@author: Matija Pavičević
"""

import datetime as dt
import logging

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from ..common import commons
from .data_handler import dk_to_df


# Helper functions
def listToString(s):
    """
    Convert list to string with blank spaces in between the list elements

    :param s: list of strings
    :return:  whole string
    """
    str1 = " "
    return (str1.join(s))


def round_down(x, y):
    """
    Round number x to nearest integer of y multiplier
    :param x:  input number
    :param y:  multiplier
    :return:   integer
    """
    return int(x - (x % y))


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


# Data analysis for plots
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


def get_marginal_price_plot_data(inputs, results, zones):
    """
    Plot marginal price in selected zones

    :param inputs:
    :param results:
    :param zones:
    :return:
    """
    mcp = results['OutputMarginalPrice'].loc[:, zones]
    volume = pd.DataFrame()
    for z in zones:
        tmp = results['OutputAcceptanceRatioOfDemandOrders'].loc[
              :, inputs['demands'].loc[inputs['demands']['Zone'].isin([z])]['Unit']] * \
              inputs['demands'].loc[inputs['demands']['Zone'].isin([z])]['MaxDemand'].sum()
        volume.loc[:, z] = tmp.sum(axis=1)

    idx_short = pd.DatetimeIndex(pd.date_range(start=dt.datetime(*inputs['config']['StartDate']),
                                               end=dt.datetime(*inputs['config']['StopDate']),
                                               freq=str(inputs['config']['HorizonLength']) + 'd'))
    idx = pd.DatetimeIndex(pd.date_range(start=dt.datetime(*inputs['config']['StartDate']),
                                         end=dt.datetime(*inputs['config']['StopDate']),
                                         freq='h'))

    tmp_mcp = mcp.copy().reset_index(drop=True)
    tmp_baseline = mcp * volume
    tmp_baseline.reset_index(drop=True, inplace=True)
    tmp_vol = volume.copy().reset_index(drop=True)
    step = inputs['config']['HorizonLength'] * 24
    price = {'mean': pd.DataFrame(tmp_mcp.groupby(tmp_mcp.index // step).mean().set_index(idx_short),
                                  index=idx, columns=mcp.columns),
             'min': pd.DataFrame(tmp_mcp.groupby(tmp_mcp.index // step).min().set_index(idx_short),
                                 index=idx, columns=mcp.columns),
             'max': pd.DataFrame(tmp_mcp.groupby(tmp_mcp.index // step).max().set_index(idx_short),
                                 index=idx, columns=mcp.columns),
             'baseline': pd.DataFrame(tmp_baseline.groupby(tmp_baseline.index // step).sum().set_index(idx_short) /
                                      tmp_vol.groupby(tmp_vol.index // step).sum().set_index(idx_short),
                                      index=idx, columns=mcp.columns)}

    bb = mcp.loc[idx_short + dt.timedelta(hours=inputs['config']['HorizonLength'] * 24 - 1), :]
    bb.reset_index(drop=True, inplace=True)
    cstck = {'open': mcp.loc[idx_short,:],
                   'high': price['max'].loc[idx_short,:],
                   'low': price['min'].loc[idx_short,:],
                   'close': bb.set_index(idx_short),
                   'volume': tmp_vol.groupby(tmp_vol.index // step).sum().set_index(idx_short)}

    price_cstc = {}
    cols = ['open','high','low','close','volume']
    for z in mcp.columns:
        price_cstc[z] = pd.concat([cstck['open'][z],cstck['high'][z],cstck['low'][z],cstck['close'][z],
                                      cstck['volume'][z]], axis=1)
        price_cstc[z].columns = cols

    for p in list(price):
        price[p].ffill(inplace=True)

    return mcp, volume, price, price_cstc


# Plotting functions
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
    elif rng[0] < data[0].index[0] or rng[0] > data[0].index[-1] or rng[-1] < data[0].index[0] or rng[-1] > \
            data[0].index[-1]:
        logging.warning('Plotting range is not properly defined, considering the first simulated week')
        pdrng = data[0].index[:min(len(data[0]) - 1, 7 * 24)]
    elif rng[0] < data[1].index[0] or rng[0] > data[1].index[-1] or rng[-1] < data[1].index[0] or rng[-1] > \
            data[1].index[-1]:
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


def plot_market_clearing_price(data, rng=None, alpha=0.7, figsize=(10, 7.5)):
    """
    Plot market clearing price and mcp statistics

    :param data:     output from get_marginal_price_plot_data function
    :param rng:      plot range
    :param alpha:    color alopha
    :param figsize:  figure size
    :return:
    """
    from matplotlib.pyplot import cm
    import mplfinance as mpf

    mcp, vol, price, price_cstc = data

    if rng is None:
        pdrng = mcp.index[:min(len(mcp) - 1, 7 * 24)]
    elif not type(rng) == type(mcp.index):
        logging.error('The "rng" variable must be a pandas DatetimeIndex')
        raise ValueError()
    elif rng[0] < mcp.index[0] or rng[0] > mcp.index[-1] or rng[-1] < mcp.index[0] or rng[-1] > mcp.index[-1]:
        logging.warning('Plotting range is not properly defined, considering the first simulated week')
        pdrng = mcp.index[:min(len(mcp) - 1, 7 * 24)]
    else:
        pdrng = rng

    # Mcp - Volume plot
    fig, axes = plt.subplots(nrows=2, ncols=1, sharex=True, figsize=figsize, frameon=True,
                             gridspec_kw={'height_ratios': [1, 1], 'hspace': 0.2})

    color = iter(cm.rainbow(np.linspace(0, 1, len(mcp.columns))))
    for z in mcp.columns:
        c = next(color)
        axes[0].plot(pdrng, mcp.loc[pdrng, z].values, color=c)
        axes[1].bar(pdrng, vol.loc[pdrng, z].values, color=c, alpha=alpha, width=1 / (len(pdrng) + 1))

    axes[0].set_ylabel('MCP [EUR/MWh]')
    axes[0].set_title('Market Clearing Price in ' + listToString(mcp.columns))
    axes[0].axhline(linewidth=1, color='gray')
    axes[0].grid(True)
    axes[1].set_title('Traded volume in ' + listToString(mcp.columns))
    axes[1].set_ylabel('Volume [MWh]')
    plt.show()

    # MCP - volume histograms
    fig1, axes = plt.subplots(nrows=2, ncols=1, sharex=False, figsize=figsize, frameon=True,
                              gridspec_kw={'height_ratios': [1, 1], 'hspace': 0.2})
    color = iter(cm.rainbow(np.linspace(0, 1, len(mcp.columns))))
    for z in mcp.columns:
        c = next(color)
        axes[0].hist(mcp.loc[pdrng, z].values, color=c, alpha=alpha,
                     bins=2 * round_down(mcp.max().max() - mcp.min().min(), 5),
                     range=(mcp.min().min(), mcp.max().max()), rwidth=0.9)
        axes[1].hist(vol.loc[pdrng, z].values, color=c, alpha=alpha,
                     bins=2 * round_down(mcp.max().max() - mcp.min().min(), 5),
                     range=(vol.min().min(), vol.max().max()), rwidth=0.9)
    axes[0].set_xlabel('MCP Bins [EUR/MWh]')
    axes[0].set_ylabel('Frequency')
    axes[0].set_title('MCP and volume histograms in ' + listToString(mcp.columns))
    axes[0].grid(True)

    axes[1].set_xlabel('Traded Volume Bins [MWh]')
    axes[1].set_ylabel('Frequency')
    axes[1].grid(True)
    plt.show()

    # MCP in individual zones
    columns = 1
    rows = int(len(mcp.columns) / columns) + (len(mcp.columns) % columns > 0)
    fig2 = plt.figure(figsize=figsize, constrained_layout=True)
    spec = fig2.add_gridspec(nrows=rows, ncols=columns)

    j = 0
    for row in range(rows):
        for col in range(columns):
            i = list(mcp.columns)[j]
            bb = pd.DataFrame([mcp.loc[pdrng, i], price['min'].loc[pdrng, i], price['max'].loc[pdrng, i],
                               price['mean'].loc[pdrng, i], price['baseline'].loc[pdrng, i]])
            labels = ['MCP', 'min', 'max', 'mean', 'baseline']
            bb = bb.T
            bb.columns = labels
            ax = fig2.add_subplot(spec[row, col])
            handles = ax.plot(bb.loc[pdrng, :])
            ax.set_ylabel('MCP [EUR/MWh]')
            ax.set_ylim(price['min'].min().min() * 0.95, price['max'].max().max() * 1.05)
            ax.grid(True)
            ax.set_title('Market Clearing Price in ' + i)
            j = j + 1
    labels = ['MCP', 'min', 'max', 'mean', 'baseline']
    plt.legend(handles, labels, loc='center left', bbox_to_anchor=(1.02, 0.8))
    plt.show()

    # Candle plot
    mc = mpf.make_marketcolors(up='palegreen', down='c',
                               edge='inherit',
                               wick='black',
                               volume='in',
                               ohlc='i')
    s = mpf.make_mpf_style(marketcolors=mc)

    for i in list(price_cstc):
        mpf.plot(price_cstc[i], type='candle', mav=(2, 4, 6), volume=True, figratio=(10, 4), style=s,
                 title='Market movement in ' + i, figsize=figsize)
        plt.show()

    return mcp, vol


def get_market_clearing_data(inputs, results, zone, time):

    vol_dem = inputs['demands'].loc[inputs['demands']['Zone'] == zone]['MaxDemand'] * \
              inputs['param_df']['AvailabilityFactorDemandOrder'].loc[:,
              inputs['param_df']['AvailabilityFactorDemandOrder'].columns.isin(list(
                  inputs['demands'].loc[inputs['demands']['Zone'] == zone].index))]
    vol_dem.index = results['OutputMarginalPrice'].index
    price_dem =  inputs['param_df']['PriceDemandOrder'].loc[:,
                 inputs['param_df']['PriceDemandOrder'].columns.isin(list(
                     inputs['demands'].loc[inputs['demands']['Zone'] == zone].index))]
    price_dem.index = results['OutputMarginalPrice'].index

    def lspc(price, volume):
        return np.linspace(price,price,volume).T

    aa = pd.DataFrame()
    for z in vol_dem.columns:
        tmp = pd.DataFrame(lspc(price_dem.loc[time,z],int(vol_dem.loc[time,z])))
        aa = aa.append(tmp,ignore_index=True)

    plt.plot(aa, label="Supply Curve")
    # plt.plot(q, D(q), label="Demand Curve")
    plt.title("Supply and Demand")
    plt.legend(frameon=False)
    plt.xlabel("Quantity $q$")
    plt.ylabel("Price")
    plt.show()
