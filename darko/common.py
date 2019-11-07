# -*- coding: utf-8 -*-
"""
This file defines a dictionary with global variables to be used in DARKO such as fluids, technologies, etc.
"""
import datetime

commons={}
# Timestep
commons['TimeStep'] = '1h'

# TODO DARKO technologies:
commons['Technologies'] = ['HOBO','HEPU','ELHE','SOTH','GETH','WSHE','THMS']
# List of renewable technologies:
commons['tech_renewables'] = ['SOTH','GETH','WSHE']
# List of storage technologies:
commons['tech_storage'] = ['THMS']
# List of CHP types:
commons['Sectors'] = ['IND','REZ','COM']
# DARKO fuels:
commons['Fuels'] = ['BIO', 'GAS', 'HRD', 'LIG', 'NUC', 'OIL', 'PEA', 'SUN', 'WAT', 'WIN', 'WST', 'OTH', 'GEO']
# Ordered list of fuels for plotting (the first ones are negative):
commons['MeritOrder'] = ['Storage','FlowOut','GEO','NUC', 'LIG', 'HRD', 'BIO', 'GAS', 'OIL', 'PEA', 'WST', 'OTH', 'SUN', 'WIN', 'FlowIn', 'WAT']
# Colors associated with each fuel:
commons['colors'] = {'LIG': '#af4b9180', 'PEA': '#af4b9199', 'HRD': '#af4b91b2', 'OIL': '#af4b91ff',
                     'GAS': '#d7642dff',
                     'NUC': '#466eb4ff',
                     'SUN': '#e6a532ff',
                     'WIN': '#41afaaff',
                     'WAT': '#00a0e1ff',
                     'BIO': '#7daf4bff', 'GEO': '#7daf4bbf',
                     'Storage': '#b93c46ff', 'FlowIn': '#b93c46b2', 'FlowOut': '#b93c4666',
                     'OTH': '#b9c33799', 'WST': '#b9c337ff'}
commons['colors']['curtailment'] = 'red'
# Hatches associated with each fuel:
commons['hatches'] = {'LIG': '', 'PEA': '', 'HRD': '', 'OIL': '',
                      'GAS': '',
                      'NUC': '',
                      'SUN': '',
                      'WIN': '',
                      'WAT': '',
                      'BIO': '', 'GEO': '',
                      'Storage': '', 'FlowIn': '/', 'FlowOut': '\\',
                      'WST': '', 'OTH': ''
                      }

commons['logfile'] = str(datetime.datetime.now()).replace(':','-').replace(' ','_') + '.darko.log'