# -*- coding: utf-8 -*-
"""
This file defines a dictionary with global variables to be used in DARKO such as fluids, technologies, etc.
"""
import datetime
import os
import shutil

commons = {}
# Timestep
commons['TimeStep'] = '1h'
# Technologies
commons['Technologies'] = ['HOBO', 'HEPU', 'ELHE', 'SOTH', 'GETH', 'WSHE', 'THMS', 'STUR', 'GTUR', 'COMC', 'ICEN',
                           'SCSP', 'WTON', 'WTOF', 'PHOT','HROR']
# List of renewable technologies:
commons['tech_renewables'] = ['SOTH', 'GETH', 'WSHE', 'SCSP', 'WTON', 'WTOF', 'PHOT', 'HROR']
# List of storage technologies:
commons['tech_storage'] = ['THMS']
# List of CHP types:
commons['Sectors'] = ['IND', 'REZ', 'COM']
# DARKO fuels:
commons['Fuels'] = ['BIO', 'GAS', 'HRD', 'LIG', 'NUC', 'OIL', 'PEA', 'SUN', 'WAT', 'WIN', 'WST', 'OTH', 'GEO', 'ELE',
                    'WTH']
# Ordered list of fuels for plotting (the first ones are negative):
commons['MeritOrder'] = ['Storage', 'FlowOut', 'GEO', 'NUC', 'LIG', 'HRD', 'BIO', 'GAS', 'OIL', 'PEA', 'WST', 'OTH',
                         'SUN', 'WIN', 'FlowIn', 'WAT']
# Colors associated with each fuel:
commons['colors'] = {'LIG': '#af4b9180',
                     'PEA': '#af4b9199',
                     'HRD': 'darkviolet',
                     'OIL': 'magenta',
                     'GAS': '#d7642dff',
                     'NUC': '#466eb4ff',
                     'SUN': '#e6a532ff',
                     'WIN': '#41afaaff',
                     'WAT': '#00a0e1ff',
                     'HYD': '#A0522D',
                     'BIO': '#7daf4bff',
                     'AMO': '#ffff00ff',
                     'GEO': '#7daf4bbf',
                     'Storage': '#b93c46ff',
                     'FlowIn': '#b93c46b2',
                     'FlowOut': '#b93c4666',
                     'OTH': '#57D53B',
                     'WST': '#b9c337ff',
                     'HDAM': '#00a0e1ff',
                     'HPHS': 'blue',
                     'THMS': '#C04000ff',
                     'BATS': '#41A317ff',
                     'BEVS': '#b9c33799',
                     'SCSP': '#e6a532ff',
                     'P2GS': '#A0522D',
                     'ShedLoad': '#ffffffff',
                     'AIR': '#aed6f1ff',
                     'WHT': '#a93226ff',
                     'ELE': '#2C75FFff',
                     'THE': '#c70509ff',
                     'HeatSlack': '#943126ff',
                     'WTH' : '#B21900ff'}
commons['colors']['curtailment'] = 'red'
# Hatches associated with each fuel:
commons['hatches'] = {'LIG': '', 'PEA': '', 'HRD': '', 'OIL': '', 'GAS': '', 'NUC': '', 'SUN': '', 'WIN': '', 'WAT': '',
                      'BIO': '', 'AMO': '', 'GEO': '', 'Storage': '', 'WST': '', 'OTH': '', 'HYD': '',
                      'FlowIn': '/', 'FlowOut': '\\', 'HDAM': '/', 'HPHS': '/', 'SCSP': '/', 'THMS': '', 'BATS': '/',
                      'BEVS': '/', 'P2GS': '/', 'AIR': '', 'WHT': '', 'HeatSlack': '/', 'ELE': '', 'THE': '', 'WTH' : ''
                      }


commons['logfile'] = str(datetime.datetime.now()).replace(':', '-').replace(' ', '_') + '.darko.log'


def get_git_revision_tag():
    """Get version of DARKO used for this run. tag + commit hash"""
    from subprocess import check_output
    try:
        return check_output(["git", "describe", "--tags", "--always"]).strip()
    except:
        return 'NA'


def set_log_name(sim_folder, name):
    """
    Sets log file name
    :param sim:  sim folder
    :param name: can be warn_preprocessing, warn_solve....
    :return:
    """
    if os.path.isfile(commons['logfile']):
        shutil.copy(commons['logfile'], os.path.join(sim_folder, name + '.log'))
