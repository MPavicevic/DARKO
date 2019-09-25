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

def select_units(units,config):
    '''
    Function returning a new list of units by removing the ones that have unknown
    technology, zero capacity, or unknown zone
    
    :param units:       Pandas dataframe with the original list of units
    :param config:      DARKO config dictionnary
    :return:            New list of units
    '''
    for unit in units.index:
        if units.loc[unit,'Technology'] == 'Other':
            logging.warning('Removed Unit ' + str(units.loc[unit,'Unit']) + ' since its technology is unknown')
            units.drop(unit,inplace=True)
        elif units.loc[unit,'PowerCapacity'] == 0:
            logging.warning('Removed Unit ' + str(units.loc[unit,'Unit']) + ' since it has a null capacity')
            units.drop(unit,inplace=True)
        elif units.loc[unit,'Zone'] not in config['zones']:
            logging.warning('Removed Unit ' + str(units.loc[unit,'Unit']) + ' since its zone (' + str(units.loc[unit,'Zone'])+ ') is not in the list of zones')    
            units.drop(unit,inplace=True)
    units.index = range(len(units))
    return units

def incidence_matrix(sets, set_used, parameters, param_used):
    """
    This function generates the incidence matrix of the lines within the nodes
    A particular case is considered for the node "Rest Of the World", which is no explicitely defined in DARKO
    """

    for i in range(len(sets[set_used])):
        [from_node, to_node] = sets[set_used][i].split('->')
        if (from_node.strip() in sets['n']) and (to_node.strip() in sets['n']):
            parameters[param_used]['val'][i, sets['n'].index(to_node.strip())] = 1
            parameters[param_used]['val'][i, sets['n'].index(from_node.strip())] = -1
        else:
            logging.warning("The line " + str(sets[set_used][i]) + " contains unrecognized nodes")
    return parameters[param_used]

## Helpers

def _mylogspace(low, high, N):
    """
    Self-defined logspace function in which low and high are the first and last values of the space
    """
    # shifting all values so that low = 1
    space = np.logspace(0, np.log10(high + low + 1), N) - (low + 1)
    return (space)


def _find_nearest(array, value):
    """
    Self-defined function to find the index of the nearest value in a vector
    """
    idx = (np.abs(array - value)).argmin()
    return idx
