
# import numpy as np
import os
import pandas as pd     # type: ignore
from typing import cast, Optional
import io
import pkgutil
import xml.etree.ElementTree as xmlET
# from typing import Any,  Union, Dict, List, OrderedDict as OrderedDictType, Set

from ..prms_helpers import read_xml
from .Parameters import Parameters
# from ..constants import DATATYPE_TO_DTYPE, NHM_DATATYPES
from ..constants import NEW_PTYPE_TO_DTYPE, PARAMETERS_XML, DIMENSIONS_XML


class ParamDb(Parameters):
    def __init__(self, paramdb_dir: str,
                 metadata,
                 verbose: Optional[bool] = False):
        """Initialize ParamDb object.

        This object handles the monolithic parameter database.

        :param paramdb_dir: Path to the ParamDb directory
        :param verbose: Output additional debug information
        """

        super(ParamDb, self).__init__(metadata=metadata, verbose=verbose)
        self.__paramdb_dir = paramdb_dir
        self.__verbose = verbose

        # When restricted is false the package parameter xml file is used
        # otherwise the parameter database xml file is used.
        # TODO: 2023-03-28 not currently settable on init; not sure if we even need an option
        #       or if the package xml should always be used.
        self.__restricted = False

        # Read the parameters from the parameter database
        self._read()

    def _read(self):
        """Read a parameter database.
        """

        # Get the parameters available from the parameter database
        # Returns a dictionary of parameters and associated units and types

        # Read the parameters XML file
        if self.__restricted:
            global_params_file = f'{self.__paramdb_dir}/{PARAMETERS_XML}'
            params_root = read_xml(global_params_file)
        else:
            # Read the full list of possible parameters
            res = pkgutil.get_data('pyPRMS', 'xml/parameters.xml')

            assert res is not None
            xml_fh = io.StringIO(res.decode('utf-8'))
            self.__xml_tree = xmlET.parse(xml_fh)
            params_root = self.__xml_tree.getroot()

        # Read in the dimensions.xml file
        global_dimens_file = f'{self.__paramdb_dir}/{DIMENSIONS_XML}'
        dimens_root = read_xml(global_dimens_file)

        # Populate the global dimensions from the xml file
        for xml_dim in dimens_root.findall('dimension'):
            self.dimensions.add(name=cast(str, xml_dim.attrib.get('name')), size=cast(int, xml_dim.find('size').text))

        # Populate parameterSet with all available parameter names
        for param in params_root.findall('parameter'):
            xml_param_name = cast(str, param.attrib.get('name'))
            curr_file = f'{self.__paramdb_dir}/{xml_param_name}.csv'

            if self.exists(xml_param_name):
                # Sometimes the global parameter xml file has duplicates of parameters
                print(f'WARNING: {xml_param_name} is duplicated in {PARAMETERS_XML}; skipping')
                continue

            if os.path.exists(curr_file):
                self.add(xml_param_name)

                cdtype = NEW_PTYPE_TO_DTYPE[self.get(xml_param_name).meta['datatype']]
                tmp_data = pd.read_csv(curr_file,
                                       skiprows=0,
                                       usecols=[1],
                                       dtype={1: cdtype}).squeeze('columns').to_numpy()

                self.get(xml_param_name).data = tmp_data
            else:
                print(f'WARNING: {xml_param_name}, ParamDb file does not exist; skipping')

        self.adjust_bounded_parameters()
