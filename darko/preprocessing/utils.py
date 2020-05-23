"""
This file gathers different functions used in the DARKO pre-processing tools

@author: Matija Pavičević
"""

from __future__ import division

import logging
import sys

import numpy as np
import pandas as pd

from ..misc.str_handler import clean_strings, shrink_to_64


def select_units(units, config):
    """
    Function returning a new list of units by removing the ones that have unknown
    technology, zero capacity, or unknown zone

    :param units:       Pandas dataframe with the original list of units
    :param config:      DARKO config dictionary
    :return:            New list of units
    """
    for unit in units.index:
        if units.loc[unit, 'Technology'] == 'Other':
            logging.warning('Removed Unit ' + str(units.loc[unit, 'Unit']) + ' since its technology is unknown')
            units.drop(unit, inplace=True)
        elif units.loc[unit, 'PowerCapacity'] == 0:
            logging.warning('Removed Unit ' + str(units.loc[unit, 'Unit']) + ' since it has a null capacity')
            units.drop(unit, inplace=True)
        elif units.loc[unit, 'Zone'] not in config['zones']:
            logging.warning('Removed Unit ' + str(units.loc[unit, 'Unit']) + ' since its zone (' + str(
                units.loc[unit, 'Zone']) + ') is not in the list of zones')
            units.drop(unit, inplace=True)
    units.index = range(len(units))
    return units


def select_demands(units, config):
    """
    Function returning a new list of units by removing the ones that have unknown
    technology, zero capacity, or unknown zone

    :param units:       Pandas dataframe with the original list of units
    :param config:      DARKO config dictionary
    :return:            New list of units
    """
    for unit in units.index:
        if units.loc[unit, 'MaxDemand'] == 0:
            logging.warning('Removed Demand ' + str(units.loc[unit, 'Unit']) +
                            ' since it has a null capacity')
            units.drop(unit, inplace=True)
        elif units.loc[unit, 'Zone'] not in config['zones']:
            logging.warning('Removed Demand ' + str(units.loc[unit, 'Unit']) +
                            ' since its zone (' + str(units.loc[unit, 'Zone']) +
                            ') is not in the list of zones')
            units.drop(unit, inplace=True)
    units.index = range(len(units))
    return units


def incidence_matrix(sets, set_used, parameters, param_used):
    """
    This function generates the incidence matrix of the lines within the nodes.
    A particular case is considered for the node "Rest Of the World", which is no explicitly defined in DARKO

    :param sets:        all sets
    :param set_used:    considered sets
    :param parameters:  all parameters
    :param param_used:  parameters used
    """
    for i in range(len(sets[set_used])):
        [from_node, to_node] = sets[set_used][i].split('->')
        if (from_node.strip() in sets['n']) and (to_node.strip() in sets['n']):
            parameters[param_used]['val'][i, sets['n'].index(to_node.strip())] = 1
            parameters[param_used]['val'][i, sets['n'].index(from_node.strip())] = -1
        else:
            logging.warning("The line " + str(sets[set_used][i]) + " contains unrecognized nodes")
    return parameters[param_used]


def interconnections(Simulation_list, NTC_inter, Historical_flows):
    """
    Function that checks for the possible interconnections of the zones included
    in the simulation. If the interconnections occurs between two of the zones
    defined by the user to perform the simulation with, it extracts the NTC between
    those two zones. If the interconnection occurs between one of the zones
    selected by the user and one country outside the simulation, it extracts the
    physical flows; it does so for each pair (country inside-country outside) and
    sums them together creating the interconnection of this country with the RoW.

    :param Simulation_list:     List of simulated zones
    :param NTC_inter:           Day-ahead net transfer capacities (pd dataframe)
    :param Historical_flows:    Historical flows (pd dataframe)
    """
    index = NTC_inter.index.tz_localize(None).intersection(Historical_flows.index.tz_localize(None))
    if len(index) == 0:
        logging.error(
            'The two input dataframes (NTCs and Historical flows) must have the same index. No common values have '
            'been found')
        sys.exit(1)
    elif len(index) < len(NTC_inter) or len(index) < len(Historical_flows):
        diff = np.maximum(len(Historical_flows), len(NTC_inter)) - len(index)
        logging.warning(
            'The two input dataframes (NTCs and Historical flows) do not share the same index, although some values '
            'are common. The intersection has been considered and ' + str(
                diff) + ' data points have been lost')
    # Checking that all values are positive:
    if (NTC_inter.values < 0).any():
        pos = np.where(NTC_inter.values < 0)
        logging.warning('WARNING: At least NTC value is negative, for example in line ' + str(
            NTC_inter.columns[pos[1][0]]) + ' and time step ' + str(NTC_inter.index[pos[0][0]]))
    if (Historical_flows.values < 0).any():
        pos = np.where(Historical_flows.values < 0)
        logging.warning('WARNING: At least one historical flow is negative, for example in line ' + str(
            Historical_flows.columns[pos[1][0]]) + ' and time step ' + str(Historical_flows.index[pos[0][0]]))
    all_connections = []
    simulation_connections = []
    # List all connections from the dataframe headers:
    ConList = Historical_flows.columns.tolist() + [x for x in NTC_inter.columns.tolist() if
                                                   x not in Historical_flows.columns.tolist()]
    for connection in ConList:
        z = connection.split(' -> ')
        if z[0] in Simulation_list:
            all_connections.append(connection)
            if z[1] in Simulation_list:
                simulation_connections.append(connection)
        elif z[1] in Simulation_list:
            all_connections.append(connection)

    df_zones_simulated = pd.DataFrame(index=index)
    for interconnection in simulation_connections:
        if interconnection in NTC_inter.columns:
            df_zones_simulated[interconnection] = NTC_inter[interconnection]
            logging.info(
                'Detected interconnection ' + interconnection + '. The historical NTCs will be imposed as maximum '
                                                                'flow value')
    interconnections1 = df_zones_simulated.columns

    # Display a warning if a zone is isolated:
    for z in Simulation_list:
        if not any([z in conn for conn in interconnections1]) and len(Simulation_list) > 1:
            logging.warning(
                'Zone ' + z + 'does not appear to be connected to any other zone in the NTC table. It should be '
                              'simulated in isolation')

    df_RoW_temp = pd.DataFrame(index=index)
    connNames = []
    for interconnection in all_connections:
        if interconnection in Historical_flows.columns and interconnection not in simulation_connections:
            df_RoW_temp[interconnection] = Historical_flows[interconnection]
            connNames.append(interconnection)

    compare_set = set()
    for k in connNames:
        if not k[0:2] in compare_set and k[0:2] in Simulation_list:
            compare_set.add(k[0:2])

    df_zones_RoW = pd.DataFrame(index=index)
    while compare_set:
        nameToCompare = compare_set.pop()
        exports = []
        imports = []
        for name in connNames:
            if nameToCompare[0:2] in name[0:2]:
                exports.append(connNames.index(name))
                logging.info(
                    'Detected interconnection ' + name + ', happening between a simulated zone and the rest of the '
                                                         'world. The historical flows will be imposed to the model')
            elif nameToCompare[0:2] in name[6:8]:
                imports.append(connNames.index(name))
                logging.info(
                    'Detected interconnection ' + name + ', happening between the rest of the world and a simulated '
                                                         'zone. The historical flows will be imposed to the model')

        flows_out = pd.concat(df_RoW_temp[connNames[exports[i]]] for i in range(len(exports)))
        flows_out = flows_out.groupby(flows_out.index).sum()
        flows_out.name = nameToCompare + ' -> RoW'
        df_zones_RoW[nameToCompare + ' -> RoW'] = flows_out
        flows_in = pd.concat(df_RoW_temp[connNames[imports[j]]] for j in range(len(imports)))
        flows_in = flows_in.groupby(flows_in.index).sum()
        flows_in.name = 'RoW -> ' + nameToCompare
        df_zones_RoW['RoW -> ' + nameToCompare] = flows_in
    interconnections2 = df_zones_RoW.columns
    inter = list(interconnections1) + list(interconnections2)
    return df_zones_simulated, df_zones_RoW, inter


# Helper functions
def _mylogspace(low, high, N):
    """
    Self-defined logspace function in which low and high are the first and last values of the space
    """
    # shifting all values so that low = 1
    space = np.logspace(0, np.log10(high + low + 1), N) - (low + 1)
    return space


def _find_nearest(array, value):
    """
    Self-defined function to find the index of the nearest value in a vector
    """
    idx = (np.abs(array - value)).argmin()
    return idx
