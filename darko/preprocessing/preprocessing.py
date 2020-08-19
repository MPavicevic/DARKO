"""
This is the main file of the DARKO pre-processing tool.
It comprises a single function that generated the DARKO simulation environment.

@author: Matija Pavičević
"""

import datetime as dt
import logging
import os
import shutil
import sys

import numpy as np
import pandas as pd

from .data_check import check_units, check_sto, check_demands, check_MinMaxFlows, check_AvailabilityFactorsUnits, \
    check_AvailabilityFactorsDemands, check_df
# isStorage
from .data_handler import load_csv, UnitBasedTable, NodeBasedTable, define_parameter
from .utils import incidence_matrix, select_units, select_demands, interconnections

from .. import __version__
from ..misc.gdx_handler import write_variables, gdx_to_list, gdx_to_dataframe
from ..common import commons  # Load fuel types, technologies, timestep, etc:

GMS_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'GAMS')


def build_simulation(config):
    """
    This function reads the DARKO config, loads the specified data,
    processes it when needed, and formats it in the proper DARKO format.
    The output of the function is a directory with all inputs and simulation files required to run a DARKO simulation

    :param config:        Dictionary with all the configuration fields loaded from the excel file.
                          Output of the 'LoadConfig' function.
    """
    darko_version = __version__
    logging.info('New build started. DARKO version: ' + darko_version)
    # %%###############################################################################################################
    #####################################   Main Inputs    ############################################################
    ###################################################################################################################

    # Day/hour corresponding to the first and last days of the simulation:
    # Note that the first available data corresponds to 2015.01.31 (23.00) and the
    # last day with data is 2015.12.31 (22.00)
    __, m_start, d_start, __, __, __ = config['StartDate']
    y_end, m_end, d_end, _, _, _ = config['StopDate']
    config['StopDate'] = (y_end, m_end, d_end, 23, 59, 00)  # updating stopdate to the end of the day

    # Indexes of the simulation:
    idx_std = pd.DatetimeIndex(pd.date_range(start=dt.datetime(*config['StartDate']),
                                             end=dt.datetime(*config['StopDate']),
                                             freq=commons['TimeStep'])
                               )
    idx_utc_noloc = idx_std - dt.timedelta(hours=1)
    idx_utc = idx_utc_noloc.tz_localize('UTC')

    # Indexes for the whole year considered in StartDate
    idx_utc_year_noloc = pd.DatetimeIndex(pd.date_range(
                                          start=dt.datetime(*(config['StartDate'][0], 1, 1, 0, 0)),
                                          end=dt.datetime(*(config['StartDate'][0], 12, 31, 23, 59, 59)),
                                          freq=commons['TimeStep'])
                                         )

    # %%###############################################################################################################
    #####################################   Data Loading    ###########################################################
    ###################################################################################################################

    # Start and end of the simulation:
    delta = idx_utc[-1] - idx_utc[0]
    days_simulation = delta.days + 1

    # Players in the market:
    '''Supply side'''
    plants = pd.DataFrame()
    if os.path.isfile(config['PlayersSupplySide']):
        plants = load_csv(config['PlayersSupplySide'])
    elif '##' in config['PlayersSupplySide']:
        for z in config['zones']:
            path = config['PlayersSupplySide'].replace('##', str(z))
            tmp = load_csv(path)
            plants = plants.append(tmp, ignore_index=True)
    # Remove invalid power plants:
    plants = select_units(plants, config)
    # fill missing parameters with 0
    plants[['PriceBlockOrder', 'PriceFlexibleOrder', 'AccaptanceBlockOrdersMin', 'AvailabilityFactorFlexibleOrder']] = \
        plants[['PriceBlockOrder', 'PriceFlexibleOrder', 'AccaptanceBlockOrdersMin', 'AvailabilityFactorFlexibleOrder']
        ].fillna(0)
    # Rename parameters
    plants.rename(columns={'RampUp': 'UnitRampUp', 'RampDown': 'UnitRampDown'}, inplace=True)
    # Fill missing parameters with 1
    plants[['UnitRampUp', 'UnitRampDown']] = plants[['UnitRampUp', 'UnitRampDown']].fillna(1)

    # check plant list:
    check_units(config, plants)
    # If not present, add the non-compulsory fields to the units table:
    for key in ['StorageCapacity', 'StorageSelfDischarge', 'StorageChargingCapacity',
                'StorageChargingEfficiency']:
        if key not in plants.columns:
            plants[key] = np.nan

    # Defining the hydro storages:
    plants_sto = plants[[u in commons['tech_storage'] for u in plants['Technology']]]
    # check storage plants:
    check_sto(config, plants_sto)

    ReservoirLevels = UnitBasedTable(plants_sto, config['StorageProfiles'],
                                     idx_std, config['zones'],
                                     fallbacks=['Unit', 'Technology', 'Zone'],
                                     tablename='ReservoirLevels',
                                     default=0)
    ReservoirScaledInflows = UnitBasedTable(plants_sto, config['StorageInFlows'],
                                            idx_std, config['zones'],
                                            fallbacks=['Unit', 'Technology', 'Zone'],
                                            tablename='ReservoirScaledInflows',
                                            default=0)

    '''Demand side'''
    demands = pd.DataFrame()
    if os.path.isfile(config['PlayersDemandSide']):
        demands = load_csv(config['PlayersDemandSide'])
    elif '##' in config['PlayersDemandSide']:
        for z in config['zones']:
            path = config['PlayersDemandSide'].replace('##', str(z))
            tmp = load_csv(path)
            demands = demands.append(tmp, ignore_index=True)
    # remove invalid power plants:
    demands = select_demands(demands, config)

    # check demands list:
    check_demands(config, demands)

    # Load:
    AFDemandOrder = UnitBasedTable(demands, config['QuantityDemandOrder'],
                                   idx_std, config['zones'],
                                   fallbacks=['Unit'],
                                   tablename='AvailabilityFactorsDemandOrder',
                                   default=0)
    AFSimpleOrder = UnitBasedTable(plants, config['QuantitySimpleOrder'],
                                   idx_std, config['zones'],
                                   fallbacks=['Unit', 'Technology'],
                                   tablename='AvailabilityFactorsSimpleOrder',
                                   default=0)
    AFBlockOrder = UnitBasedTable(plants, config['QuantityBlockOrder'],
                                  idx_std, config['zones'],
                                  fallbacks=['Unit', 'Technology'],
                                  tablename='AvailabilityFactorsBlockOrder',
                                  default=0)

    # Price:
    PriceDemandOrder = UnitBasedTable(demands, config['PriceDemandOrder'],
                                      idx_std, config['zones'],
                                      fallbacks=['Unit'],
                                      tablename='PriceDemandOrder',
                                      default=0)
    PriceSimpleOrder = UnitBasedTable(plants, config['PriceSimpleOrder'],
                                      idx_std, config['zones'],
                                      fallbacks=['Unit', 'Technology'],
                                      tablename='PriceSimpleOrder',
                                      default=0)

    # Daily node based ramping rates TODO: Make a function that loads only single values for each zone instead of this
    NodeDailyRampUp = NodeBasedTable(config['NodeDailyRampUp'], idx_std,
                                     config['zones'], tablename='NodeDailyRampUp',
                                     default=config['default']['NodeDailyRampUp'])
    NodeDailyRampDown = NodeBasedTable(config['NodeDailyRampDown'], idx_std,
                                       config['zones'], tablename='NodeDailyRampDown',
                                       default=config['default']['NodeDailyRampDown'])
    NodeDailyRamp = pd.DataFrame([NodeDailyRampUp.iloc[0], NodeDailyRampDown.iloc[0]],
                                 index=['NodeDailyRampUp', 'NodeDailyRampDown']).T
    MaxDemand = demands.groupby(['Zone'])['MaxDemand'].agg('sum')
    # Adjust to the fraction of max total demand
    NodeDailyRamp = (NodeDailyRamp.T * MaxDemand * 24 * config['HorizonLength']).T
    NodeDailyRamp.reset_index(inplace=True)

    # Hourly node based ramping rates
    NodeHourlyRampUp = NodeBasedTable(config['NodeHourlyRampUp'], idx_std,
                                      config['zones'], tablename='NodeHourlyRampUp',
                                      default=config['default']['NodeHourlyRampUp'])
    NodeHourlyRampDown = NodeBasedTable(config['NodeHourlyRampDown'], idx_std,
                                        config['zones'], tablename='NodeHourlyRampDown',
                                        default=config['default']['NodeHourlyRampDown'])
    # Adjust to the fraction of max capacity
    NodeHourlyRampUp = NodeHourlyRampUp * MaxDemand
    NodeHourlyRampDown = NodeHourlyRampDown * MaxDemand

    # Interconnections:
    if os.path.isfile(config['Interconnections']):
        flows = load_csv(config['Interconnections'], index_col=0, parse_dates=True).fillna(0)
    else:
        logging.warning('No historical flows will be considered (no valid file provided)')
        flows = pd.DataFrame(index=idx_std)
    if os.path.isfile(config['NTC']):
        ntc = load_csv(config['NTC'], index_col=0, parse_dates=True).fillna(0)
    else:
        logging.warning('No NTC values will be considered (no valid file provided)')
        ntc = pd.DataFrame(index=idx_std)

    LineDailyRampUp = NodeBasedTable(config['LineDailyRampUp'], idx_std,
                                     list(ntc.columns), tablename='LineDailyRampUp',
                                     default=config['default']['LineDailyRampUp'])
    LineDailyRampDown = NodeBasedTable(config['LineDailyRampDown'], idx_std,
                                       list(ntc.columns), tablename='LineDailyRampDown',
                                       default=config['default']['LineDailyRampDown'])
    LineDailyRamp = pd.DataFrame([LineDailyRampUp.iloc[0], LineDailyRampDown.iloc[0]],
                                 index=['LineDailyRampUp', 'LineDailyRampDown']).T
    # Adjust to the fraction of max total demand
    LineDailyRamp = (LineDailyRamp.T * ntc.max() * 24 * config['HorizonLength']).T
    LineDailyRamp.reset_index(inplace=True)

    # Interconnection ramping rates
    LineHourlyRampUp = NodeBasedTable(config['LineHourlyRampUp'], idx_std,
                                      list(ntc.columns), tablename='LineHourlyRampUp',
                                      default=config['default']['LineHourlyRampUp'])
    LineHourlyRampDown = NodeBasedTable(config['LineHourlyRampDown'], idx_std,
                                        list(ntc.columns), tablename='LineHourlyRampDown',
                                        default=config['default']['LineHourlyRampDown'])
    # Adjust to the fraction of max capacity
    LineHourlyRampUp = LineHourlyRampUp * ntc.max()
    LineHourlyRampDown = LineHourlyRampDown * ntc.max()

    # data checks:
    check_AvailabilityFactorsDemands(demands, AFDemandOrder)
    check_AvailabilityFactorsUnits(plants, AFSimpleOrder)
    check_AvailabilityFactorsUnits(plants, AFBlockOrder)

    # Interconnections:
    [Interconnections_sim, Interconnections_RoW, Interconnections] = interconnections(config['zones'], ntc, flows)

    if len(Interconnections_sim.columns) > 0:
        ntcs = Interconnections_sim.reindex(idx_std)
    else:
        ntcs = pd.DataFrame(index=idx_std)
    Inter_RoW = Interconnections_RoW.reindex(idx_std)

    # %%
    # checking data
    # Availability factors
    check_df(AFDemandOrder, StartDate=idx_std[0], StopDate=idx_std[-1],
             name='AvailabilityFactorsDemandOrder')
    check_df(AFBlockOrder, StartDate=idx_std[0], StopDate=idx_std[-1],
             name='AvailabilityFactorsBlockOrder')
    check_df(AFSimpleOrder, StartDate=idx_std[0], StopDate=idx_std[-1],
             name='AvailabilityFactorsSimpleOrder')
    # Prices
    check_df(PriceDemandOrder, StartDate=idx_std[0], StopDate=idx_std[-1],
             name='PriceDemandOrder')
    check_df(PriceSimpleOrder, StartDate=idx_std[0], StopDate=idx_std[-1],
             name='PriceSimpleOrder')
    # Interconnections
    check_df(Inter_RoW, StartDate=idx_std[0], StopDate=idx_std[-1],
             name='Inter_RoW')
    check_df(ntcs, StartDate=idx_std[0], StopDate=idx_std[-1],
             name='NTCs')
    # Line ramping rates
    check_df(LineHourlyRampUp, StartDate=idx_std[0], StopDate=idx_std[-1],
             name='LineHourlyRampUp')
    check_df(LineHourlyRampDown, StartDate=idx_std[0], StopDate=idx_std[-1],
             name='LineHourlyRampDown')
    # Node ramping rates
    check_df(NodeHourlyRampUp, StartDate=idx_std[0], StopDate=idx_std[-1],
             name='NodeHourlyRampUp')
    check_df(NodeHourlyRampDown, StartDate=idx_std[0], StopDate=idx_std[-1],
             name='NodeHourlyRampDown')
    # Storage
    check_df(ReservoirLevels, StartDate=idx_std[0], StopDate=idx_std[-1],
             name='ReservoirLevels')
    check_df(ReservoirScaledInflows, StartDate=idx_std[0], StopDate=idx_std[-1],
             name='ReservoirScaledInflows')

    # %%%

    # Extending the data to include the look-ahead period (with constant values assumed)
    enddate_long = idx_std[-1] + dt.timedelta(days=config['LookAhead'])
    idx_long = pd.DatetimeIndex(pd.date_range(start=idx_std[0], end=enddate_long, freq=commons['TimeStep']))
    Nhours_long = len(idx_long)

    # re-indexing with the longer index and filling possibly missing data at the beginning and at the end::
    AFDemandOrder = AFDemandOrder.reindex(idx_long, method='nearest').fillna(method='bfill')
    AFSimpleOrder = AFSimpleOrder.reindex(idx_long, method='nearest').fillna(method='bfill')
    AFBlockOrder = AFBlockOrder.reindex(idx_long, method='nearest').fillna(method='bfill')
    PriceDemandOrder = PriceDemandOrder.reindex(idx_long, method='nearest').fillna(method='bfill')
    PriceSimpleOrder = PriceSimpleOrder.reindex(idx_long, method='nearest').fillna(method='bfill')
    Inter_RoW = Inter_RoW.reindex(idx_long, method='nearest').fillna(method='bfill')
    ntcs = ntcs.reindex(idx_long, method='nearest').fillna(method='bfill')
    LineHourlyRampUp = LineHourlyRampUp.reindex(idx_long, method='nearest').fillna(method='bfill')
    LineHourlyRampDown = LineHourlyRampDown.reindex(idx_long, method='nearest').fillna(method='bfill')
    NodeHourlyRampUp = NodeHourlyRampUp.reindex(idx_long, method='nearest').fillna(method='bfill')
    NodeHourlyRampDown = NodeHourlyRampDown.reindex(idx_long, method='nearest').fillna(method='bfill')
    ReservoirLevels = ReservoirLevels.reindex(idx_long, method='nearest').fillna(method='bfill')
    ReservoirScaledInflows = ReservoirScaledInflows.reindex(idx_long, method='nearest').fillna(method='bfill')
    #    for key in FuelPrices:
    #        FuelPrices[key] = FuelPrices[key].reindex(idx_long, method='nearest').fillna(method='bfill')
    #    ReservoirLevels_merged = ReservoirLevels_merged.reindex(idx_long, method='nearest').fillna(method='bfill')
    #    ReservoirScaledInflows_merged = ReservoirScaledInflows_merged.reindex(idx_long, method='nearest').fillna(
    #        method='bfill')
    ##    for tr in Renewables:
    ##        Renewables[tr] = Renewables[tr].reindex(idx_long, method='nearest').fillna(method='bfill')
    #
    # %%###############################################################################################################
    ############################################   Sets    ############################################################
    ###################################################################################################################

    # The sets are defined within a dictionary:
    sets = {'d': demands['Unit'].tolist(),
            'u': plants['Unit'].tolist(),
            'o': ['Simple', 'Block', 'Flexible', 'Storage'],
            'n': config['zones'],
            'l': Interconnections,
            't': commons['Technologies'],
            'tr': commons['tech_renewables'],
            'f': commons['Fuels'],
            's': plants_sto['Unit'].tolist(),
            'h': [str(x + 1) for x in range(Nhours_long)],
            'z': [str(x + 1) for x in range(Nhours_long - config['LookAhead'] * 24)],
            'sk': commons['Sectors']
            }

    ###################################################################################################################
    ############################################   Parameters    ######################################################
    ###################################################################################################################

    Nunits = len(plants)
    Ndems = len(demands)
    parameters = {}

    # Each parameter is associated with certain sets, as defined in the following list:
    sets_param = {'AccaptanceBlockOrdersMin': ['u'],
                  'AvailabilityFactorDemandOrder': ['d', 'h'],
                  'AvailabilityFactorSimpleOrder': ['u', 'h'],
                  'AvailabilityFactorBlockOrder': ['u', 'h'],
                  'AvailabilityFactorFlexibleOrder': ['u'],
                  'MaxDemand': ['d'],
                  'Fuel': ['u', 'f'],
                  'LocationDemandSide': ['d', 'n'],
                  'LocationSupplySide': ['u', 'n'],
                  'OrderType': ['u', 'o'],
                  'PowerCapacity': ['u'],
                  'PriceDemandOrder': ['d', 'h'],
                  'PriceSimpleOrder': ['u', 'h'],
                  'PriceBlockOrder': ['u'],
                  'PriceFlexibleOrder': ['u'],
                  'Sector': ['d', 'sk'],
                  'Technology': ['u', 't'],
                  'LineNode': ['l', 'n'],
                  'FlowMaximum': ['l', 'h'],
                  'FlowMinimum': ['l', 'h'],
                  'UnitRampUp': ['u'],
                  'UnitRampDown': ['u'],
                  'NodeHourlyRampUp': ['n', 'h'],
                  'NodeHourlyRampDown': ['n', 'h'],
                  'NodeDailyRampUp': ['n'],
                  'NodeDailyRampDown': ['n'],
                  'LineHourlyRampUp': ['l', 'h'],
                  'LineHourlyRampDown': ['l', 'h'],
                  'LineDailyRampUp': ['l'],
                  'LineDailyRampDown': ['l'],
                  'NodeInitial': ['n'],
                  'LineInitial': ['l'],
                  'StorageCapacity': ['s'],
                  'StorageChargingCapacity': ['s'],
                  'StorageChargingEfficiency': ['s'],
                  'StorageDischargeEfficiency': ['s'],
                  'StorageSelfDischarge': ['s'],
                  'StorageInflow': ['s','h'],
                  'StorageInitial': ['s'],
                  'StorageMinimum': ['s'],
                  'StorageOutflow': ['s', 'h'],
                  'StorageProfile': ['s','h']
                  }

    # Define all the parameters and set a default value of zero:
    for var in sets_param:
        parameters[var] = define_parameter(sets_param[var], sets, value=0)

    # Boolean parameters:
    for var in ['Fuel', 'LocationDemandSide', 'LocationSupplySide', 'OrderType', 'Sector', 'Technology']:
        parameters[var] = define_parameter(sets_param[var], sets, value='bool')

    # %%
    # List of parameters whose value is known, and provided in the dataframe plants.
    for var in ['PowerCapacity', 'UnitRampUp', 'UnitRampDown', 'PriceBlockOrder', 'PriceFlexibleOrder',
                'AccaptanceBlockOrdersMin', 'AvailabilityFactorFlexibleOrder']:
        parameters[var]['val'] = plants[var].values
    # List of parameters whose value is known, and provided in the dataframe demands.
    for var in ['MaxDemand']:
        parameters[var]['val'] = demands[var].values

    # List of parameters whose value is know and provided for each zone
    for var in ['NodeDailyRampUp', 'NodeDailyRampDown', 'LineDailyRampUp', 'LineDailyRampDown']:
        if var in ['NodeDailyRampUp', 'NodeDailyRampDown']:
            parameters[var]['val'] = NodeDailyRamp[var].values
        if var in ['LineDailyRampUp', 'LineDailyRampDown']:
            parameters[var]['val'] = LineDailyRamp[var].values

    # List of parameters whose value is known, and provided in the availability factors.
    for i, d in enumerate(sets['d']):
        if d in AFDemandOrder.columns:
            parameters['AvailabilityFactorDemandOrder']['val'][i, :] = AFDemandOrder[d]
    for i, u in enumerate(sets['u']):
        if u in AFSimpleOrder.columns:
            parameters['AvailabilityFactorSimpleOrder']['val'][i, :] = AFSimpleOrder[u]
    for i, u in enumerate(sets['u']):
        if u in AFBlockOrder.columns:
            parameters['AvailabilityFactorBlockOrder']['val'][i, :] = AFBlockOrder[u]
    for i, d in enumerate(sets['d']):
        if d in PriceDemandOrder.columns:
            parameters['PriceDemandOrder']['val'][i, :] = PriceDemandOrder[d]
    for i, u in enumerate(sets['u']):
        if u in PriceSimpleOrder.columns:
            parameters['PriceSimpleOrder']['val'][i, :] = PriceSimpleOrder[u]

    #    # List of parameters whose value is not necessarily specified in the dataframe Plants_merged
    #    for var in ['Nunits']:
    #        if var in Plants_merged:
    #            parameters[var]['val'] = Plants_merged[var].values

    # List of parameters whose value is known, and provided in the dataframe Plants_sto.
    for var in ['StorageCapacity', 'StorageChargingCapacity', 'StorageChargingEfficiency', 'StorageSelfDischarge']:
        parameters[var]['val'] = plants_sto[var].values

    # The storage discharge efficiency is actually given by the unit efficiency:
    parameters['StorageDischargeEfficiency']['val'] = plants_sto['Efficiency'].values

    # Storage profile and initial state:
    for i, s in enumerate(sets['s']):
        if s in ReservoirLevels and any(ReservoirLevels[s] > 0) and all(ReservoirLevels[s] -1 <= 1e-11):
            # get the time series
            parameters['StorageProfile']['val'][i, :] = ReservoirLevels[s][idx_long].values
        elif s in ReservoirLevels and any(ReservoirLevels[s] > 0) and any(ReservoirLevels[s] -1 > 1e-11):
            logging.critical(s + ': The reservoir level is sometimes higher than its capacity (>1) !')
            sys.exit(1)
        else:
            logging.warning(
                'Could not find reservoir level data for storage plant ' + s + '. Using the provided default initial '
                                                                               'and final values')
            # parameters['StorageProfile']['val'][i, :] = np.linspace(config['default']['ReservoirLevelInitial'],
            #                                                         config['default']['ReservoirLevelFinal'],
            #                                                         len(idx_long))
            parameters['StorageProfile']['val'][i, :] = np.linspace(0,
                                                                    0,
                                                                    len(idx_long))
        # The initial level is the same as the first value of the profile:
        parameters['StorageInitial']['val'][i] = parameters['StorageProfile']['val'][i, 0] * \
                                                 plants_sto.loc[plants_sto['Unit'] == s]['StorageCapacity']
                                                 # plants_sto['StorageCapacity'][s]
                                                 # finalTS['AvailabilityFactors'][s][idx_long[0]] * \
                                                 # * plants_sto['Nunits'][s]

    # Storage Inflows:
    for i, s in enumerate(sets['s']):
        if s in ReservoirScaledInflows:
            parameters['StorageInflow']['val'][i, :] = ReservoirScaledInflows[s][idx_long].values * \
                                                       plants_sto.loc[plants_sto['Unit'] == s]['PowerCapacity'].values

    # %%#################################################################################################################################################################################################

    # Maximum Line Capacity
    for i, l in enumerate(sets['l']):
        if l in ntcs.columns:
            parameters['FlowMaximum']['val'][i, :] = ntcs[l]
        if l in Inter_RoW.columns:
            parameters['FlowMaximum']['val'][i, :] = Inter_RoW[l]
            parameters['FlowMinimum']['val'][i, :] = Inter_RoW[l]
        if l in LineHourlyRampUp.columns:
            parameters['LineHourlyRampUp']['val'][i, :] = LineHourlyRampUp[l]
        if l in LineHourlyRampDown.columns:
            parameters['LineHourlyRampDown']['val'][i, :] = LineHourlyRampDown[l]
    # Check values:
    check_MinMaxFlows(parameters['FlowMinimum']['val'], parameters['FlowMaximum']['val'])

    parameters['LineNode'] = incidence_matrix(sets, 'l', parameters, 'LineNode')

    # Maximum hourly ramp rates per node
    for i, n in enumerate(sets['n']):
        if n in NodeHourlyRampUp.columns:
            parameters['NodeHourlyRampUp']['val'][i, :] = NodeHourlyRampUp[n]
        if n in NodeHourlyRampDown.columns:
            parameters['NodeHourlyRampDown']['val'][i, :] = NodeHourlyRampDown[n]

    # Orders
    for unit in range(Nunits):
        idx = sets['o'].index(plants['OrderType'][unit])
        parameters['OrderType']['val'][unit, idx] = True

    # Sectors
    for dem in range(Ndems):
        idx = sets['sk'].index(demands['Sector'][dem])
        parameters['Sector']['val'][dem, idx] = True

    # Technologies
    for unit in range(Nunits):
        idx = sets['t'].index(plants['Technology'][unit])
        parameters['Technology']['val'][unit, idx] = True

    # Fuels
    for unit in range(Nunits):
        idx = sets['f'].index(plants['Fuel'][unit])
        parameters['Fuel']['val'][unit, idx] = True

    # Location Demand Side
    for i in range(len(sets['n'])):
        parameters['LocationDemandSide']['val'][:, i] = (demands['Zone'] == config['zones'][i]).values

    # Location Supply Side
    for i in range(len(sets['n'])):
        parameters['LocationSupplySide']['val'][:, i] = (plants['Zone'] == config['zones'][i]).values

    # Config variables:
    sets['x_config'] = ['FirstDay', 'LastDay', 'RollingHorizon Length', 'RollingHorizon LookAhead']
    sets['y_config'] = ['year', 'month', 'day', 'val']
    dd_begin = idx_long[4]
    dd_end = idx_long[-2]

    values = np.array([
        [dd_begin.year, dd_begin.month, dd_begin.day, 0],
        [dd_end.year, dd_end.month, dd_end.day, 0],
        [0, 0, config['HorizonLength'], 0],
        [0, 0, config['LookAhead'], 0]
    ])
    parameters['Config'] = {'sets': ['x_config', 'y_config'], 'val': values}

    # %%###############################################################################################################
    ######################################   Simulation Environment     ###############################################
    ###################################################################################################################

    # Output folder:
    sim = config['SimulationDirectory']

    # Clean SimData
    demands.set_index('Unnamed: 0', drop=True, inplace=True)

    # Simulation data:
    SimData = {'sets': sets,
               'parameters': parameters,
               'config': config,
               'units': plants,
               'demands': demands,
               'version': darko_version
               }

    # list_vars = []
    gdx_out = "Inputs.gdx"
    if config['WriteGDX']:
        write_variables(config['GAMS_folder'], gdx_out, [sets, parameters])

    # if the sim variable was not defined:
    if 'sim' not in locals():
        logging.error('Please provide a path where to store the DispaSET inputs ' +
                      '(in the "sim" variable)')
        sys.exit(1)

    if not os.path.exists(sim):
        os.makedirs(sim)
    #    if LP:
    #        fin = open(os.path.join(GMS_FOLDER, 'UCM_h.gms'))
    #        fout = open(os.path.join(sim,'UCM_h.gms'), "wt")
    #        for line in fin:
    #            fout.write(line.replace('$setglobal LPFormulation 0', '$setglobal LPFormulation 1'))
    #        fin.close()
    #        fout.close()
    #        # additionally allso copy UCM_h_simple.gms
    #        shutil.copyfile(os.path.join(GMS_FOLDER, 'UCM_h_simple.gms'),
    #                        os.path.join(sim, 'UCM_h_simple.gms'))
    #    else:
    shutil.copyfile(os.path.join(GMS_FOLDER, 'DARKO.gms'),
                    os.path.join(sim, 'DARKO.gms'))
    # additionally allso copy UCM_h_simple.gms
    #    shutil.copyfile(os.path.join(GMS_FOLDER, 'UCM_h_simple.gms'),
    #                    os.path.join(sim, 'UCM_h_simple.gms'))
    gmsfile = open(os.path.join(sim, 'DARKO.gpr'), 'w')
    gmsfile.write(
        '[PROJECT] \n \n[RP:DARKO] \n1= \n[OPENWINDOW_1] \nFILE0=DARKO.gms \nFILE1=DARKO.gms \nMAXIM=1 \nTOP=50 '
        '\nLEFT=50 \nHEIGHT=400 \nWIDTH=400')
    gmsfile.close()
    #    shutil.copyfile(os.path.join(GMS_FOLDER, 'writeresults.gms'),
    #                    os.path.join(sim, 'writeresults.gms'))
    # Create cplex option file
    cplex_options = {'epgap': 0.05,  # TODO: For the moment hardcoded, it has to be moved to a config file
                     'numericalemphasis': 0,
                     'scaind': 1,
                     'lpmethod': 0,
                     'relaxfixedinfeas': 0,
                     'mipstart': 1,
                     'epint': 0}

    lines_to_write = ['{} {}'.format(k, v) for k, v in cplex_options.items()]
    with open(os.path.join(sim, 'cplex.opt'), 'w') as f:
        for line in lines_to_write:
            f.write(line + '\n')

    logging.debug('Using gams file from ' + GMS_FOLDER)
    if config['WriteGDX']:
        shutil.copy(gdx_out, sim + '/')
        os.remove(gdx_out)
    # Copy bat file to generate gdx file directly from excel:
    shutil.copy(os.path.join(GMS_FOLDER, 'makeGDX.bat'),
                os.path.join(sim, 'makeGDX.bat'))

    #    if config['WriteExcel']:
    #        write_to_excel(sim, [sets, parameters])

    if config['WritePickle']:
        try:
            import cPickle as pickle
        except ImportError:
            import pickle
        with open(os.path.join(sim, 'Inputs.p'), 'wb') as pfile:
            pickle.dump(SimData, pfile, protocol=pickle.HIGHEST_PROTOCOL)
    logging.info('Build finished')

    if os.path.isfile(commons['logfile']):
        shutil.copy(commons['logfile'], os.path.join(sim, 'warn_preprocessing.log'))

    return SimData
