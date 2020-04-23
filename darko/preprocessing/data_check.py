"""
This files gathers different functions used in the DARKO to check the input
data

__author__ = Matija Pavičević
"""

import os
import sys
import numpy as np
import pandas as pd
import logging


def isVRE(tech):
    '''
    Function that returns true the technology is a variable renewable energy technology
    '''
    return tech in ['SOTH','WSHE','GETH']

def isStorage(tech):
    '''
    Function that returns true the technology is a storage technology
    '''
    return tech in ['THMS']

def check_AvailabilityFactorsDemands(demands,AF):
    '''
    Function that checks the validity of the provided availability factors and warns
    if a default value of 100% is used.
    '''
#    for t in ['SOTH','GETH','WSHE','THMS']:
    for i in demands['Unit'].index:
        d = demands.loc[i,'Unit']
        if d in AF:
            if (AF[d].values == 1).all():
                logging.critical('The availability factor of unit ' + str(d) + 
                                 'is always 100%!')
            if (AF[d].values == np.inf).any():
                logging.critical('The Availability factor of unit ' + str(d) + 
                                 'is of type +Inf. Inputs must be checked carefully')
            if (AF[d].values == -np.inf).any():
                logging.critical('The Availability factor of unit ' + str(d) + 
                                 'is of type -Inf. Inputs must be checked carefully')
            if (AF[d].values > 1).any():
                logging.critical('The Availability factor of unit ' + str(d) + 
                                 'is higher than 1. Inputs must be checked carefully')
            if (AF[d].values < 0).any():
                logging.critical('The Availability factor of unit ' + str(d) + 
                                 'is lower than 0. Inputs must be checked carefully')
        else:
            logging.critical('Unit ' + str(d) + ' does not appear in the ' + 
                             'availbilityFactors table. Its values will be set to 100%!')
    if (AF.dropna().values < 0).any():
        logging.error('Some Availaibility factors are negative')
        sys.exit(1)
    if (AF.dropna().values > 1).any():
        logging.warning('Some Availability factors are higher than one. They ' + 
                        'must be carefully checked')


def check_AvailabilityFactorsUnits(plants,AF):
    '''
    Function that checks the validity of the provided availability factors and warns
    if a default value of 100% is used.
    '''
    for t in ['SOTH','GETH','WSHE','THMS']:
        for i in plants[plants['Technology']==t].index:
            u = plants.loc[i,'Unit']
            if u in AF:
                if (AF[u].values == 1).all():
                    logging.critical('The availability factor of unit ' + str(u) + 
                                     ' + for technology ' + t + ' is always 100%!')
                if (AF[u].values == np.inf).any():
                    logging.critical('The Availability factor of unit ' + str(u) + 
                                     ' + for technology ' + t + ' is of type +Inf. ' + 
                                     'Inputs must be checked carefully')
                if (AF[u].values == -np.inf).any():
                    logging.critical('The Availability factor of unit ' + str(u) + 
                                     ' + for technology ' + t + ' is of type -Inf. ' + 
                                     'Inputs must be checked carefully')
                if (AF[u].values > 1).any():
                    logging.critical('The Availability factor of unit ' + str(u) + 
                                     ' + for technology ' + t + ' is higher than 1. ' + 
                                     'Inputs must be checked carefully')
                if (AF[u].values < 0).any():
                    logging.critical('The Availability factor of unit ' + str(u) + 
                                     ' + for technology ' + t + ' is lower than 0. ' + 
                                     'Inputs must be checked carefully')
            else:
                logging.critical('Unit ' + str(u) + ' (technology ' + t + 
                                 ') does not appear in the availbilityFactors table. ' + 
                                 'Its values will be set to 100%!')
    if (AF.dropna().values < 0).any():
        logging.error('Some Availaibility factors are negative')
        sys.exit(1)
    if (AF.dropna().values > 1).any():
        logging.warning('Some Availability factors are higher than one. They must ' + 
                        'be carefully checked')

def check_MinMaxFlows(df_min,df_max):
    '''
    Function that checks that there is no incompatibility between the minimum 
    and maximum flows
    '''
    if (df_min > df_max).any():
        pos = np.where(df_min > df_max)
        logging.critical('ERROR: At least one minimum flow is higher than the ' + 
                         'maximum flow, for example in line number ' + str(pos[0][0]) + 
                         ' and time step ' + str(pos[1][0]))
        sys.exit(1)

    if (df_max < 0).any():
        pos = np.where(df_max < 0)
        logging.critical('ERROR: At least one maximum flow is negative, for example ' + 
                         'in line number ' + str(pos[0][0]) + ' and time step ' + 
                         str(pos[1][0]))
        sys.exit(1)
    return True

def check_sto(config, plants,raw_data=True):
    """
    Function that checks the storage plant characteristics
    """
    if raw_data:
        keys = ['StorageCapacity','StorageSelfDischarge','StorageMaxChargingPower',
                'StorageChargingEfficiency']
        NonNaNKeys = ['StorageCapacity']
    else:
        keys = ['StorageCapacity','StorageSelfDischarge','StorageChargingCapacity',
                'StorageChargingEfficiency']
        NonNaNKeys = ['StorageCapacity']

    if 'StorageInitial' in plants:
        logging.warning('The "StorageInitial" column is present in the power plant ' + 
                        'table, although it is deprecated (it should now be defined ' + 
                        'in the ReservoirLevel data table). It will not be considered.')
  
    for key in keys:
        if key not in plants:
            logging.critical('The power plants data does not contain the field "' + key + 
                             '", which is mandatory for storage units')
            sys.exit(1)

    for key in NonNaNKeys:
        for u in plants.index:
            if 'Unit' in plants:
                unitname = plants.loc[u,'Unit']
            else:
                unitname = str(u)
            if isinstance(plants.loc[u, key], str):
                logging.critical('A non numeric value was detected in the power plants ' + 
                                 'inputs for parameter "' + key + '"')
                sys.exit(1)
            if np.isnan(plants.loc[u, key]):
                logging.critical('The power plants data is missing for unit ' + unitname + 
                                 ' and parameter "' + key + '"')
                sys.exit(1)

    return True

def check_demands(config, demands):
    """
    Function that checks the demand side characteristics
    """ 
    keys = ['Unit', 'Zone', 'Sector', 'MaxDemand']
    NonNaNKeys = ['MaxDemand']
    StrKeys = ['Unit', 'Zone', 'Sector']  
    
    for key in keys:
        if key not in demands:
            logging.critical('The demands data does not contain the field "' + 
                             key + '", which is mandatory')
            sys.exit(1)

    for key in NonNaNKeys:
        for u in demands.index:
            if type(demands.loc[u, key]) == str:
                logging.critical('A non numeric value was detected in the ' +
                                 'demands inputs for parameter "' + key + '"')
                sys.exit(1)
            if np.isnan(demands.loc[u, key]):
                logging.critical('The demands data is missing for unit number ' + 
                                 str(u) + ' and parameter "' + key + '"')
                sys.exit(1)

    for key in StrKeys:
        for u in demands.index:
            if not type(demands.loc[u, key]) == str:
                logging.critical(
                    'A numeric value was detected in the demands inputs for ' +
                    'parameter "' + key + '". This column should contain strings only.')
                sys.exit(1)
            elif demands.loc[u, key] == '':
                logging.critical('An empty value was detected in the demands ' +
                                 'inputs for unit "' + str(u) + 
                                 '" and parameter "' + key + '"')
                sys.exit(1)

    if len(demands['Unit'].unique()) != len(demands['Unit']):
        duplicates = demands['Unit'][demands['Unit'].duplicated()].tolist()
        logging.error('The names of the demands are not unique. The following ' +
                      'names are duplicates: ' + str(duplicates) + '. "' + 
                      str(duplicates[0] + '" appears for example in the following zones: ' + 
                      str(demands.Zone[demands['Unit']==duplicates[0]].tolist())))
        sys.exit(1)
            
    return True

def check_units(config, plants):
    """
    Function that checks the power plant characteristics
    """

    keys = ['Unit', 'Fuel', 'Zone', 'Sector', 'Technology', 'PowerCapacity', 'RampUp', 'RampDown',
            'OrderType', 'PriceBlockOrder', 'PriceFlexibleOrder',
            'AccaptanceBlockOrdersMin', 'AvailabilityFactorFlexibleOrder', 
            'Efficiency', 'CO2Intensity']
    NonNaNKeys = ['PowerCapacity']
    StrKeys = ['Unit', 'Fuel', 'Zone', 'Sector', 'Technology', 'OrderType']

    for key in keys:
        if key not in plants:
            logging.critical('The power plants data does not contain the field "' + 
                             key + '", which is mandatory')
            sys.exit(1)

    for key in NonNaNKeys:
        for u in plants.index:
            if type(plants.loc[u, key]) == str:
                logging.critical('A non numeric value was detected in the power ' + 
                                 'plants inputs for parameter "' + key + '"')
                sys.exit(1)
            if np.isnan(plants.loc[u, key]):
                logging.critical('The power plants data is missing for unit number ' + 
                                 str(u) + ' and parameter "' + key + '"')
                sys.exit(1)

    for key in StrKeys:
        for u in plants.index:
            if not type(plants.loc[u, key]) == str:
                logging.critical(
                    'A numeric value was detected in the power plants inputs for ' + 
                    'parameter "' + key + '". This column should contain strings only.')
                sys.exit(1)
            elif plants.loc[u, key] == '':
                logging.critical('An empty value was detected in the power plants inputs ' + 
                                 'for unit "' + str(u) + '" and parameter "' + key + '"')
                sys.exit(1)

    lower = {'PowerCapacity': 0}
    lower_hard = {'Efficiency': 0}
    higher = {'Efficiency': 1}
#    higher_time = {'MinUpTime': 0, 'MinDownTime': 0}

    if len(plants['Unit'].unique()) != len(plants['Unit']):
        duplicates = plants['Unit'][plants['Unit'].duplicated()].tolist()
        logging.error('The names of the power plants are not unique. The following ' + 
                      'names are duplicates: ' + str(duplicates) + '. "' + str(duplicates[0] + 
                      '" appears for example in the following zones: ' + 
                      str(plants.Zone[plants['Unit']==duplicates[0]].tolist())))
        sys.exit(1)

    for key in lower:
        if any(plants[key] < lower[key]):
            plantlist = plants[plants[key] < lower[key]]
            plantlist = plantlist['Unit'].tolist()
            logging.critical(
                'The value of ' + key + ' should be higher or equal to zero. A negative ' + 
                'value has been found for units ' + str(plantlist))
            sys.exit(1)

    for key in lower_hard:
        if any(plants[key] <= lower_hard[key]):
            plantlist = plants[plants[key] <= lower_hard[key]]
            plantlist = plantlist['Unit'].tolist()
            logging.critical(
                'The value of ' + key + ' should be strictly higher than zero. A null or ' + 
                'negative value has been found for units ' + str(plantlist))
            sys.exit(1)

    for key in higher:
        if any(plants[key] > higher[key]):
            plantlist = plants[plants[key] > higher[key]]
            plantlist = plantlist['Unit'].tolist()
            logging.critical(
                'The value of ' + key + ' should be lower or equal to one. A higher ' + 
                'value has been found for units ' + str(plantlist))
            sys.exit(1)

#    for key in higher_time:
#        if any(plants[key] >= config['HorizonLength'] * 24):
#            plantlist = plants[plants[key] >= config['HorizonLength'] * 24]
#            plantlist = plantlist['Unit'].tolist()
#            logging.critical('The value of ' + key + ' should be lower than the horizon length (' + str(
#                config['HorizonLength'] * 24) + ' hours). A higher value has been found for units ' + str(plantlist))
#            sys.exit(1)
            
    return True

def check_df(df, StartDate=None, StopDate=None, name=''):
    """
    Function that check the time series provided as inputs
    """

    if isinstance(df.index, pd.DatetimeIndex):
        if not StartDate in df.index:
            logging.warning('The start date ' + str(StartDate) + ' is not in ' + 
                            'the index of the provided dataframe')
        if not StopDate in df.index:
            logging.warning('The stop date ' + str(StopDate) + ' is not in ' + 
                            'the index of the provided dataframe')
    if any(np.isnan(df)):
        for key in df:
            missing = np.sum(np.isnan(df[key]))
            # pos = np.where(np.isnan(df.sum(axis=1)))
            # idx_pos = [df.index[i] for i in pos]
            if missing > 1:
                logging.warning('There are ' + str(missing) + 
                                ' missing entries in the column ' + key + 
                                ' of the dataframe ' + name)
    if not df.columns.is_unique:
        logging.error('The column headers of table "' + name + '" are not unique!. ' + 
                      'The following headers are duplicated: ' + 
                      str(df.columns.get_duplicates()))
        sys.exit(1)
    return True


#def check_simulation_environment(SimulationPath, store_type='pickle', firstline=7):
#    """
#    Function to test the validity of disapset inputs
#    :param SimulationPath:          Path to the simulation folder
#    :param store_type:              choose between: "list", "excel", "pickle"
#    :param firstline:               Number of the first line in the data (only if type=='excel')
#    """
#
#    import cPickle
#
#    # minimum list of variable required for dispaSET:
#    list_sets = [
#        'h',
#        'd',
#        'mk',
#        'n',
#        'c',
#        'p',
#        'l',
#        'f',
#        's',
#        't',
#        'tr',
#        'u']
#
#    list_param = [
#        'AvailabilityFactor',
#        'CostFixed',
#        'CostShutDown',
#        'Curtailment',
#        'Demand',
#        'Efficiency',
#        'Fuel',
#        'CostVariable',
#        'FuelPrice',
#        'Markup',
#        'CostStartUp',
#        'EmissionMaximum',
#        'EmissionRate',
#        'FlowMaximum',
#        'FlowMinimum',
#        'LineNode',
#        'Location',
#        'LoadShedding',
#        'OutageFactor',
#        'PermitPrice',
#        'PriceTransmission',
#        'PowerCapacity',
#        'PartLoadMin',
#        'RampUpMaximum',
#        'RampDownMaximum',
#        'RampStartUpMaximum',
#        'RampShutDownMaximum',
#        'Reserve',
#        'StorageDischargeEfficiency',
#        'StorageCapacity',
#        'StorageInflow',
#        'StorageOutflow',
#        'StorageInitial',
#        'StorageMinimum',
#        'StorageChargingEfficiency',
#        'StorageChargingCapacity',
#        'Technology',
#        'TimeDownMinimum',
#        'TimeUpMinimum',
#        'TimeDownInitial',
#        'TimeUpInitial',
#        'PowerInitial']
#
#    if store_type == 'list':
#        if isinstance(SimulationPath, list):
#            # The list of sets and parameters has been passed directly to the function, checking that all are present:
#            SimulationPath_vars = [SimulationPath[i]['name'] for i in range(len(SimulationPath))]
#            for var in list_sets + list_param:
#                if var not in SimulationPath_vars:
#                    logging.critical('The variable "' + var + '" has not been found in the list of input variables')
#                    sys.exit(1)
#        else:
#            logging.critical('The argument must a list. Please correct or change the "type" argument')
#            sys.exit(1)
#
#    elif store_type == 'pickle':
#        if os.path.exists(SimulationPath):
#            if os.path.isfile(os.path.join(SimulationPath, 'Inputs.p')):
#                vars = cPickle.load(open(os.path.join(SimulationPath, 'Inputs.p'), 'rb'))
#                arg_vars = [vars[i]['name'] for i in range(len(vars))]
#                for var in list_sets + list_param:
#                    if var not in arg_vars:
#                        logging.critical('Found Pickle file but does not contain valid DispaSET input (' + var + ' missing)')
#                        sys.exit(1)
#            else:
#                logging.critical('Could not find the Inputs.p file in the specified directory')
#                sys.exit(1)
#        else:
#            logging.critical('The function argument is not a valid directory')
#            sys.exit(1)
#
#    elif store_type == 'excel':
#        if os.path.exists(SimulationPath):
#            if not os.path.isfile(os.path.join(SimulationPath, 'InputDispa-SET - Sets.xlsx')):
#                logging.critical("Could not find the file 'InputDispa-SET - Sets.xlsx'")
#                sys.exit(1)
#            for var in list_param:
#                if os.path.isfile(os.path.join(SimulationPath, 'InputDispa-SET - ' + var + '.xlsx')):
#                    a = 1
#                else:
#                    logging.critical("Could not find the file 'InputDispa-SET - " + var + ".xlsx'")
#                    sys.exit(1)
#
#        else:
#            logging.critical('The function argument is not a valid directory')
#            sys.exit(1)
#
#    else:
#        logging.critical('The "type" parameter must be one of the following : "list", "excel", "pickle"')
#        sys.exit(1)
#
#
