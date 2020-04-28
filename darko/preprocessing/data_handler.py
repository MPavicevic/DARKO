import logging
import os
import sys

import numpy as np
import pandas as pd

from six.moves import reload_module

try:
    from future.builtins import int
except ImportError:
    pass


def NodeBasedTable(path, idx, zones, tablename='', default=None):
    """
    This function loads the tabular data stored in csv files relative to each
    zone of the simulation.

    :param path:                Path to the data to be loaded
    :param idx:                 Pandas datetime index to be used for the output
    :param zones:               List with the zone codes to be considered
    :param tablename:           String with the name of the table being processed
    :param default:             Default value to be applied if no data is found

    :return:           Dataframe with the time series for each unit
    """

    paths = {}
    if os.path.isfile(path):
        paths['all'] = path
        SingleFile = True
    elif '##' in path:
        for z in zones:
            path_c = path.replace('##', str(z))
            if os.path.isfile(path_c):
                paths[str(z)] = path_c
            else:
                logging.error(
                    'No data file found for the table ' + tablename + ' and zone ' + z + '. File ' + path_c +
                    ' does not exist')
                sys.exit(1)
        SingleFile = False
    data = pd.DataFrame(index=idx)
    if len(paths) == 0:
        logging.info('No data file found for the table ' + tablename + '. Using default value ' + str(default))
        if default is None:
            pass
        elif isinstance(default, (float, int)):
            data = pd.DataFrame(default, index=idx, columns=zones)
        else:
            logging.error('Default value provided for table ' + tablename + ' is not valid')
            sys.exit(1)
    elif SingleFile:
        # If it is only one file, there is a header with the zone code
        tmp = load_csv(paths['all'], index_col=0, parse_dates=True)
        if not tmp.index.is_unique:
            logging.error('The index of data file ' + paths['all'] + ' is not unique. Please check the data')
            sys.exit(1)
        if len(tmp.columns) == 1:  # if there is only one column, assign its value to all the zones, whatever the header
            try:  # if the column header is numerical, there was probably no header. Load the file again.
                float(tmp.columns[0])  # this will fail if the header is not numerical
                tmp = pd.read_csv(paths['all'], header=None, index_col=0, parse_dates=True)
                tmp = tmp.tz_localize(None)
            except:
                pass
            for key in zones:
                data[key] = tmp.iloc[:, 0]
        else:
            for key in zones:
                if key in tmp:
                    data[key] = tmp[key]
                else:
                    logging.error(
                        'Zone ' + key + ' could not be found in the file ' + path + '. Using default value ' + str(
                            default))
                    if default is None:
                        pass
                    elif isinstance(default, (float, int)):
                        data[key] = default
                    else:
                        logging.error('Default value provided for table ' + tablename + ' is not valid')
                        sys.exit(1)
    else:  # assembling the files in a single dataframe:
        for z in paths:
            path = paths[z]
            # In case of separated files for each zone, there is no header
            tmp = load_csv(path, index_col=0, parse_dates=True)
            # check that the loaded file is ok:
            if not tmp.index.is_unique:
                logging.error('The index of data file ' + paths['all'] + ' is not unique. Please check the data')
                sys.exit(1)
            data[z] = tmp.iloc[:, 0]

    return data


def UnitBasedTable(plants, path, idx, zones, fallbacks=['Unit'], tablename='', default=None, RestrictWarning=None):
    """
    This function loads the tabular data stored in csv files and assigns the
    proper values to each unit of the plants dataframe. If the unit-specific
    value is not found in the data, the script can fallback on more generic
    data (e.g. fuel-based, technology-based, zone-based) or to the default value.
    The order in which the data should be loaded is specified in the fallback
    list. For example, ['Unit','Technology'] means that the script will first
    try to find a perfect match for the unit name in the data table. If not found,
    a column with the unit technology as header is search. If not found, the
    default value is assigned.

    :param plants:              Dataframe with the units for which data is required
    :param path:                Path to the data to be loaded
    :param idx:                 Pandas datetime index to be used for the output
    :param zones:           List with the zone codes to be considered
    :param fallback:            List with the order of data source.
    :param tablename:           String with the name of the table being processed
    :param default:             Default value to be applied if no data is found
    :param RestrictWarning:     Only display the warnings if the unit belongs to the list of technologies provided in this parameter

    :return:           Dataframe with the time series for each unit
    """

    paths = {}
    if os.path.isfile(path):
        paths['all'] = path
        SingleFile = True
    elif '##' in path:
        for z in zones:
            path_c = path.replace('##', str(z))
            if os.path.isfile(path_c):
                paths[str(z)] = path_c
            else:
                logging.critical(
                    'No data file found for the table ' + tablename + ' and zone ' + z + '. File ' + path_c +
                    ' does not exist')
        #                sys.exit(1)
        SingleFile = False
    data = pd.DataFrame(index=idx)
    if len(paths) == 0:
        logging.info('No data file found for the table ' + tablename + '. Using default value ' + str(default))
        if default is None:
            out = pd.DataFrame(index=idx)
        elif isinstance(default, (float, int)):
            out = pd.DataFrame(default, index=idx, columns=plants['Unit'])
        else:
            logging.error('Default value provided for table ' + tablename + ' is not valid')
            sys.exit(1)
    else:  # assembling the files in a single dataframe:
        columns = []
        for z in paths:
            path = paths[z]
            tmp = load_csv(path, index_col=0, parse_dates=True)
            # check that the loaded file is ok:
            if not tmp.index.is_unique:
                logging.error('The index of data file ' + path + ' is not unique. Please check the data')
                sys.exit(1)
            if SingleFile:
                for key in tmp:
                    data[key] = tmp[key]
            else:  # use the multi-index header with the zone
                for key in tmp:
                    columns.append((z, key))
                    data[z + ',' + key] = tmp[key]
        if not SingleFile:
            data.columns = pd.MultiIndex.from_tuples(columns, names=['Zone', 'Data'])
        # For each plant and each fallback key, try to find the corresponding column in the data
        out = pd.DataFrame(index=idx)
        for j in plants.index:
            warning = True
            if not RestrictWarning is None:
                warning = False
                if plants.loc[j, 'Technology'] in RestrictWarning:
                    warning = True
            u = plants.loc[j, 'Unit']
            found = False
            for i, key in enumerate(fallbacks):
                if SingleFile:
                    header = plants.loc[j, key]
                else:
                    header = (plants.loc[j, 'Zone'], plants.loc[j, key])
                if header in data:
                    out[u] = data[header]
                    found = True
                    if i > 0 and warning:
                        logging.warning(
                            'No specific information was found for unit ' + u + ' in table ' + tablename +
                            '. The generic information for ' + str(header) + ' has been used')
                    break
            if not found:
                if warning:
                    logging.info(
                        'No specific information was found for unit ' + u + ' in table ' + tablename +
                        '. Using default value ' + str(default))
                if not default is None:
                    out[u] = default
    if not out.columns.is_unique:
        logging.error(
            'The column headers of table "' + tablename + '" are not unique!. The following headers are duplicated: ' +
            str(out.columns.get_duplicates()))
        sys.exit(1)
    return out


def define_parameter(sets_in, sets, value=0):
    """
    Function to define a DARKO parameter and fill it with a constant value

    :param sets_in:     List with the labels of the sets corresponding to the parameter
    :param sets:        dictionary containing the definition of all the sets (must comprise those referenced in sets_in)
    :param value:       Default value to attribute to the parameter
    """
    if value == 'bool':
        values = np.zeros([len(sets[setx]) for setx in sets_in], dtype='bool')
    elif value == 0:
        values = np.zeros([len(sets[setx]) for setx in sets_in])
    elif value == 1:
        values = np.ones([len(sets[setx]) for setx in sets_in])
    else:
        values = np.ones([len(sets[setx]) for setx in sets_in]) * value
    return {'sets': sets_in, 'val': values}


def load_csv(filename, TempPath='.pickle', header=0, skiprows=None, skipfooter=0, index_col=None, parse_dates=False):
    """
    Function that loads a csv sheet into a dataframe and saves a temporary pickle version of it.
    If the pickle is newer than the sheet, do no load the sheet again.

    :param filename: path to csv file
    :param TempPath: path to store the temporary data files
    """

    import hashlib
    m = hashlib.new('md5', filename.encode('utf-8'))
    resultfile_hash = m.hexdigest()
    filepath_pandas = TempPath + os.sep + resultfile_hash + '.p'

    if not os.path.isdir(TempPath):
        os.mkdir(TempPath)
    if not os.path.isfile(filepath_pandas):
        time_pd = 0
    else:
        time_pd = os.path.getmtime(filepath_pandas)
    if os.path.getmtime(filename) > time_pd:
        data = pd.read_csv(filename, header=header, skiprows=skiprows, skipfooter=skipfooter, index_col=index_col,
                           parse_dates=parse_dates)
        if parse_dates:
            data.index = data.index.tz_localize(None)
        data.to_pickle(filepath_pandas)
    else:
        data = pd.read_pickle(filepath_pandas)
    return data


def load_config(ConfigFile, AbsPath=True):
    """
    Wrapper function around load_config_excel and load_config_yaml
    """
    if ConfigFile.endswith(('.xlsx', '.xls')):
        config = load_config_excel(ConfigFile, AbsPath=True)
    # elif ConfigFile.endswith(('.yml','.yaml')):
    #     config = load_config_yaml(ConfigFile,AbsPath=True)
    else:
        logging.critical('The extension of the config file should be .xlsx or .yml')
        sys.exit(1)
    return config


def load_config_excel(ConfigFile, AbsPath=True):
    """
    Function that loads the DARKO excel config file and returns a dictionary
    with the values

    :param ConfigFile: String with (relative) path to the DARKO excel configuration file
    :param AbsPath:    If true, relative paths are automatically changed into absolute paths (recommended)
    """
    import xlrd
    wb = xlrd.open_workbook(filename=ConfigFile)  # Option for csv to be added later
    sheet = wb.sheet_by_name('main')

    config = {'SimulationDirectory': sheet.cell_value(17, 2),
              'WriteExcel': sheet.cell_value(18, 2),
              'WriteGDX': sheet.cell_value(19, 2),
              'WritePickle': sheet.cell_value(20, 2),
              'GAMS_folder': sheet.cell_value(21, 2),
              'cplex_path': sheet.cell_value(22, 2),
              'StartDate': xlrd.xldate_as_tuple(sheet.cell_value(30, 2), wb.datemode),
              'StopDate': xlrd.xldate_as_tuple(sheet.cell_value(31, 2), wb.datemode),
              'HorizonLength': int(sheet.cell_value(32, 2)),
              'LookAhead': int(sheet.cell_value(33, 2)),
              'SimulationType': sheet.cell_value(46, 2),
              'ReserveCalculation': sheet.cell_value(47, 2)}

    # List of parameters for which an external file path must be specified:
    params = ['QuantityDemandOrder', 'QuantitySimpleOrder', 'QuantityBlockOrder', 'QuantityFlexibleOrder',
              'PriceDemandOrder', 'PriceSimpleOrder', 'PriceBlockOrder', 'PriceFlexibleOrder',
              'PlayersDemandSide', 'PlayersSupplySide', 'Interconnections', 'NTC',
              'NodeHourlyRampUp', 'NodeHourlyRampDown', 'NodeDailyRampUp', 'NodeDailyRampDown',
              'LineHourlyRampUp', 'LineHourlyRampDown', 'LineDailyRampUp', 'LineDailyRampDown']
    for i, param in enumerate(params):
        config[param] = sheet.cell_value(61 + i, 2)

    if AbsPath:
        # Changing all relative paths to absolute paths. Relative paths must be defined
        # relative to the parent folder of the config file.
        abspath = os.path.abspath(ConfigFile)
        basefolder = os.path.abspath(os.path.join(os.path.dirname(abspath), os.pardir))
        if not os.path.isabs(config['SimulationDirectory']):
            config['SimulationDirectory'] = os.path.join(basefolder, config['SimulationDirectory'])
        for param in params:
            if not os.path.isabs(config[param]):
                config[param] = os.path.join(basefolder, config[param])

    config['default'] = {}
    config['default']['Availability - Flexible Order'] = sheet.cell_value(64, 5)
    config['default']['Price - Block Order'] = sheet.cell_value(67, 5)
    config['default']['Price - Flexible Order'] = sheet.cell_value(68, 5)
    config['default']['NodeHourlyRampUp'] = sheet.cell_value(73, 5)
    config['default']['NodeHourlyRampDown'] = sheet.cell_value(74, 5)
    config['default']['NodeDailyRampUp'] = sheet.cell_value(75, 5)
    config['default']['NodeDailyRampDown'] = sheet.cell_value(76, 5)
    config['default']['LineHourlyRampUp'] = sheet.cell_value(77, 5)
    config['default']['LineHourlyRampDown'] = sheet.cell_value(78, 5)
    config['default']['LineDailyRampUp'] = sheet.cell_value(79, 5)
    config['default']['LineDailyRampDown'] = sheet.cell_value(80, 5)

    # read the list of zones to consider:
    def read_truefalse(sheet, rowstart, colstart, rowstop, colstop):
        """
        Function that reads a two column format with a list of strings in the first
        columns and a list of true false in the second column
        The list of strings associated with a True value is returned
        """
        out = []
        for i in range(rowstart, rowstop):
            if sheet.cell_value(i, colstart + 1) == 1:
                out.append(sheet.cell_value(i, colstart))
        return out

    config['zones'] = read_truefalse(sheet, 86, 1, 111, 3)
    config['zones'] = config['zones'] + read_truefalse(sheet, 86, 4, 111, 6)
    #
    config['modifiers'] = {}
    config['modifiers']['Demand'] = sheet.cell_value(111, 2)
    #
    logging.info("Using config file " + ConfigFile + " to build the simulation environment")
    logging.info("Using " + config['SimulationDirectory'] + " as simulation folder")

    return config
