"""
This is the main file of the DARKO pre-processing tool. It comprises a single function that generated the DARKO simulation environment.

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

from ..misc.gdx_handler import write_variables, gdx_to_list, gdx_to_dataframe
from ..common import commons  # Load fuel types, technologies, timestep, etc:

GMS_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'GAMS')


def get_git_revision_tag():
    """Get version of DARKO used for this run. tag + commit hash"""
    from subprocess import check_output
    try:
        return check_output(["git", "describe", "--tags", "--always"]).strip()
    except:
        return 'NA'


def build_simulation(config):
    """
    This function reads the DARKO config, loads the specified data,
    processes it when needed, and formats it in the proper DARKO format.
    The output of the function is a directory with all inputs and simulation files required to run a DARKO simulation

    :param config:        Dictionary with all the configuration fields loaded from the excel file.
                          Output of the 'LoadConfig' function.
    :param plot_load:     Boolean used to display a plot of the demand curves in the different zones
    :param profiles:      Profiles from mid term scheduling simulations
    """
    darko_version = str(get_git_revision_tag())
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
    idx_std = pd.DatetimeIndex(pd.date_range(start=pd.datetime(*config['StartDate']),
                                             end=pd.datetime(*config['StopDate']),
                                             freq=commons['TimeStep'])
                               )
    idx_utc_noloc = idx_std - dt.timedelta(hours=1)
    idx_utc = idx_utc_noloc.tz_localize('UTC')

    # Indexes for the whole year considered in StartDate
    idx_utc_year_noloc = pd.DatetimeIndex(pd.date_range(
        start=pd.datetime(*(config['StartDate'][0], 1, 1, 0, 0)),
        end=pd.datetime(*(config['StartDate'][0], 12, 31, 23, 59, 59)),
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
    # reomve invalide power plants:
    plants = select_units(plants, config)
    plants[['PriceBlockOrder', 'PriceFlexibleOrder', 'AccaptanceBlockOrdersMin', 'AvailabilityFactorFlexibleOrder']] = \
        plants[['PriceBlockOrder', 'PriceFlexibleOrder', 'AccaptanceBlockOrdersMin', 'AvailabilityFactorFlexibleOrder']
        ].fillna(0)

    # check plant list:
    check_units(config, plants)
    # If not present, add the non-compulsory fields to the units table:
    for key in ['StorageCapacity', 'StorageSelfDischarge', 'StorageMaxChargingPower',
                'StorageChargingEfficiency']:
        if key not in plants.columns:
            plants[key] = np.nan

    # Defining the hydro storages:
    plants_sto = plants[[u in commons['tech_storage'] for u in plants['Technology']]]
    # check storage plants:
    check_sto(config, plants_sto)

    '''Demand side'''
    demands = pd.DataFrame()
    if os.path.isfile(config['PlayersDemandSide']):
        demands = load_csv(config['PlayersDemandSide'])
    elif '##' in config['PlayersDemandSide']:
        for z in config['zones']:
            path = config['PlayersDemandSide'].replace('##', str(z))
            tmp = load_csv(path)
            demands = demands.append(tmp, ignore_index=True)
    # reomve invalide power plants:
    demands = select_demands(demands, config)

    # check demands list:
    check_demands(config, demands)
    # If not present, add the non-compulsory fields to the units table:
    for key in ['StorageCapacity', 'StorageSelfDischarge', 'StorageMaxChargingPower', 'StorageChargingEfficiency']:
        if key not in demands.columns:
            demands[key] = np.nan

    # Load:
    AFDemandOrder = UnitBasedTable(demands, config['QuantityDemandOrder'],
                                   idx_utc_noloc, config['zones'],
                                   fallbacks=['Unit'],
                                   tablename='AvailabilityFactorsDemandOrder',
                                   default=0)
    AFSimpleOrder = UnitBasedTable(plants, config['QuantitySimpleOrder'],
                                   idx_utc_noloc, config['zones'],
                                   fallbacks=['Unit', 'Technology'],
                                   tablename='AvailabilityFactorsSimpleOrder',
                                   default=0)
    AFBlockOrder = UnitBasedTable(plants, config['QuantityBlockOrder'],
                                  idx_utc_noloc, config['zones'],
                                  fallbacks=['Unit', 'Technology'],
                                  tablename='AvailabilityFactorsBlockOrder',
                                  default=0)

    # Price:
    PriceDemandOrder = UnitBasedTable(demands, config['PriceDemandOrder'],
                                      idx_utc_noloc, config['zones'],
                                      fallbacks=['Unit'],
                                      tablename='PriceDemandOrder',
                                      default=0)
    PriceSimpleOrder = UnitBasedTable(plants, config['PriceSimpleOrder'],
                                      idx_utc_noloc, config['zones'],
                                      fallbacks=['Unit', 'Technology'],
                                      tablename='PriceSimpleOrder',
                                      default=0)

    # Interconnections:
    if os.path.isfile(config['Interconnections']):
        flows = load_csv(config['Interconnections'], index_col=0, parse_dates=True).fillna(0)
    else:
        logging.warning('No historical flows will be considered (no valid file provided)')
        flows = pd.DataFrame(index=idx_utc_noloc)
    if os.path.isfile(config['NTC']):
        ntc = load_csv(config['NTC'], index_col=0, parse_dates=True).fillna(0)
    else:
        logging.warning('No NTC values will be considered (no valid file provided)')
        ntc = pd.DataFrame(index=idx_utc_noloc)

    # data checks:
    check_AvailabilityFactorsDemands(demands, AFDemandOrder)
    check_AvailabilityFactorsUnits(plants, AFSimpleOrder)
    check_AvailabilityFactorsUnits(plants, AFBlockOrder)

    # Interconnections:
    [Interconnections_sim, Interconnections_RoW, Interconnections] = interconnections(config['zones'], ntc, flows)

    if len(Interconnections_sim.columns) > 0:
        ntcs = Interconnections_sim.reindex(idx_utc_noloc)
    else:
        ntcs = pd.DataFrame(index=idx_utc_noloc)
    Inter_RoW = Interconnections_RoW.reindex(idx_utc_noloc)

    # %%
    # checking data
    # Availability factors
    check_df(AFDemandOrder, StartDate=idx_utc_noloc[0], StopDate=idx_utc_noloc[-1],
             name='AvailabilityFactorsDemandOrder')
    check_df(AFBlockOrder, StartDate=idx_utc_noloc[0], StopDate=idx_utc_noloc[-1],
             name='AvailabilityFactorsBlockOrder')
    check_df(AFSimpleOrder, StartDate=idx_utc_noloc[0], StopDate=idx_utc_noloc[-1],
             name='AvailabilityFactorsSimpleOrder')
    # Prices
    check_df(PriceDemandOrder, StartDate=idx_utc_noloc[0], StopDate=idx_utc_noloc[-1],
             name='PriceDemandOrder')
    check_df(PriceSimpleOrder, StartDate=idx_utc_noloc[0], StopDate=idx_utc_noloc[-1],
             name='PriceSimpleOrder')
    # Interconnections
    check_df(Inter_RoW, StartDate=idx_utc_noloc[0], StopDate=idx_utc_noloc[-1],
             name='Inter_RoW')
    check_df(ntcs, StartDate=idx_utc_noloc[0], StopDate=idx_utc_noloc[-1],
             name='NTCs')

    # %%%

    # Extending the data to include the look-ahead period (with constant values assumed)
    enddate_long = idx_utc_noloc[-1] + dt.timedelta(days=config['LookAhead'])
    idx_long = pd.DatetimeIndex(pd.date_range(start=idx_utc_noloc[0], end=enddate_long, freq=commons['TimeStep']))
    Nhours_long = len(idx_long)

    # re-indexing with the longer index and filling possibly missing data at the beginning and at the end::
    AFDemandOrder = AFDemandOrder.reindex(idx_long, method='nearest').fillna(method='bfill')
    AFSimpleOrder = AFSimpleOrder.reindex(idx_long, method='nearest').fillna(method='bfill')
    AFBlockOrder = AFBlockOrder.reindex(idx_long, method='nearest').fillna(method='bfill')
    PriceDemandOrder = PriceDemandOrder.reindex(idx_long, method='nearest').fillna(method='bfill')
    PriceSimpleOrder = PriceSimpleOrder.reindex(idx_long, method='nearest').fillna(method='bfill')
    Inter_RoW = Inter_RoW.reindex(idx_long, method='nearest').fillna(method='bfill')
    ntcs = ntcs.reindex(idx_long, method='nearest').fillna(method='bfill')
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
            'o': ['Simple', 'Block', 'Flexible'],
            'n': config['zones'],
            'l': Interconnections,
            't': commons['Technologies'],
            'tr': commons['tech_renewables'],
            'f': commons['Fuels'],
            's': commons['tech_storage'],
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
                  'MaxDemand': ['d'], 'Fuel': ['u', 'f'],
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
                  'StorageCapacity': ['s'],
                  'StorageMaxChargingPower': ['s'],
                  'StorageChargingEfficiency': ['s'],
                  'StorageSelfDischarge': ['s']
                  }

    # Define all the parameters and set a default value of zero:
    for var in sets_param:
        parameters[var] = define_parameter(sets_param[var], sets, value=0)

    # Boolean parameters:
    for var in ['Fuel', 'LocationDemandSide', 'LocationSupplySide', 'OrderType', 'Sector', 'Technology']:
        parameters[var] = define_parameter(sets_param[var], sets, value='bool')

    # %%
    # List of parameters whose value is known, and provided in the dataframe plants.
    for var in ['PowerCapacity', 'PriceBlockOrder', 'PriceFlexibleOrder', 'AccaptanceBlockOrdersMin',
                'AvailabilityFactorFlexibleOrder']:
        parameters[var]['val'] = plants[var].values
    # List of parameters whose value is known, and provided in the dataframe demands.
    for var in ['MaxDemand']:
        parameters[var]['val'] = demands[var].values

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
    for var in ['StorageCapacity', 'StorageMaxChargingPower', 'StorageChargingEfficiency']:
        parameters[var]['val'] = plants_sto[var].values

    # The storage discharge efficiency is actually given by the unit efficiency:
    parameters['StorageSelfDischarge']['val'] = plants_sto['Efficiency'].values
    #
    #    # Storage profile and initial state:
    #    for i, s in enumerate(sets['s']):
    #        if s in ReservoirLevels_merged:
    #            # get the time
    #            parameters['StorageInitial']['val'][i] = ReservoirLevels_merged[s][idx_long[0]] * \
    #                                                     Plants_sto['StorageCapacity'][s] * Plants_sto['Nunits'][s]
    #            parameters['StorageProfile']['val'][i, :] = ReservoirLevels_merged[s][idx_long].values
    #            if any(ReservoirLevels_merged[s] > 1):
    #                logging.warning(s + ': The reservoir level is sometimes higher than its capacity!')
    #        else:
    #            logging.warning( 'Could not find reservoir level data for storage plant ' + s + '. Assuming 50% of capacity')
    #            parameters['StorageInitial']['val'][i] = 0.5 * Plants_sto['StorageCapacity'][s]
    #            parameters['StorageProfile']['val'][i, :] = 0.5
    #

    # %%#################################################################################################################################################################################################

    # Maximum Line Capacity
    for i, l in enumerate(sets['l']):
        if l in ntcs.columns:
            parameters['FlowMaximum']['val'][i, :] = ntcs[l]
        if l in Inter_RoW.columns:
            parameters['FlowMaximum']['val'][i, :] = Inter_RoW[l]
            parameters['FlowMinimum']['val'][i, :] = Inter_RoW[l]
    # Check values:
    check_MinMaxFlows(parameters['FlowMinimum']['val'], parameters['FlowMaximum']['val'])

    parameters['LineNode'] = incidence_matrix(sets, 'l', parameters, 'LineNode')

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

    # TODO: integrated the parameters (VOLL, Water value, etc) from the excel config file
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
        '[PROJECT] \n \n[RP:DARKO] \n1= \n[OPENWINDOW_1] \nFILE0=DARKO.gms \nFILE1=DARKO.gms \nMAXIM=1 \nTOP=50 \nLEFT=50 \nHEIGHT=400 \nWIDTH=400')
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
