import functools
import numpy as np
import pandas as pd
from collections import namedtuple, OrderedDict
from typing import Any,  Union, List
import xml.etree.ElementTree as xmlET

# from pyPRMS.Exceptions_custom import ConcatError
from pyPRMS.constants import DATA_TYPES, DATATYPE_TO_DTYPE
from pyPRMS.Dimensions import ParamDimensions


class Parameter(object):
    """Container for a single Parameter object.

    A parameter has a name, datatype, optional units, one or more dimensions, and
    associated data.
    """

    # Container for a single parameter
    def __init__(self, name=None, datatype=None, units=None, model=None, description=None,
                 help=None, modules=None, minimum=None, maximum=None, default=None):
        """Initialize the Parameter object.

        :param str name: A valid PRMS parameter name
        :param int datatype: The datatype for the parameter (1-Integer, 2-Float, 3-Double, 4-String)
        :param str units: Option units string for the parameter
        :param str model: <<FILL IN LATER>>
        :param str description: Description of the parameter
        :param str help: Help text for the parameter
        :param modules: List of modules that require the parameter
        :type modules: list[str] or None
        :param minimum: Minimum value allowed in the parameter data
        :type minimum: int or float or None
        :param maximum: Maximum value allowed in the parameter data
        :type maximum: int or float or None
        :param default: Default value used for parameter data
        :type default: int or float or None
        """

        # Set the parameter name
        self.__name = name

        # Initialize internal variables
        self.__datatype = None
        self.__units = None
        self.__model = None
        self.__description = None
        self.__help = None
        self.__modules = None
        self.__minimum = None
        self.__maximum = None
        self.__default = None

        self.__dimensions = ParamDimensions()
        self.__data = None  # array

        self.__modified = False

        # Use setters for most internal variables
        self.datatype = datatype
        self.units = units
        self.model = model
        self.description = description
        self.help = help
        self.modules = modules
        self.minimum = minimum
        self.maximum = maximum
        self.default = default

    def __str__(self) -> str:
        """Pretty-print string representation of the parameter information.

        :return: Parameter information
        :rtype: str
        """
        out_text = 'name: {}\ndatatype: {}\nunits: {}\nndims: {}\ndescription: {}\nhelp: {}\n'
        outstr = out_text.format(self.name, self.datatype, self.units, self.ndims, self.description,
                                 self.help)

        if self.__minimum is not None:
            outstr += f'Minimum value: {self.__minimum}\n'

        if self.__maximum is not None:
            outstr += f'Maximum value: {self.__maximum}\n'

        if self.__default is not None:
            outstr += f'Default value: {self.__default}\n'

        outstr += 'Size of data: '
        if self.__data is not None:
            outstr += f'{self.data.size}\n'
        else:
            outstr += '<empty>\n'

        if self.__modules is not None:
            outstr += 'Modules: '

            for xx in self.__modules:
                outstr += f'{xx} '
            outstr += '\n'

        if self.ndims:
            outstr += 'Dimensions:\n' + self.__dimensions.__str__()
        return outstr

    @property
    def as_dataframe(self) -> pd.DataFrame:
        """Returns the parameter data as a pandas DataFrame."""

        if len(self.data.shape) == 2:
            df = pd.DataFrame(self.data)
            df.rename(columns=lambda xx: '{}_{}'.format(self.name, df.columns.get_loc(xx) + 1), inplace=True)
        else:
            # Assuming 1D array
            df = pd.DataFrame(self.data, columns=[self.name])
            # df.rename(columns={0: name}, inplace=True)

        return df

    @property
    def name(self) -> str:
        """Returns the parameter name."""
        return self.__name

    @property
    def datatype(self) -> int:
        """Returns the datatype of the parameter.

        :rtype: int"""
        return self.__datatype

    @datatype.setter
    def datatype(self, dtype: int):
        """Sets the datatype for the parameter.

        :param int dtype: The datatype for the parameter (1-Integer, 2-Float, 3-Double, 4-String)
        """

        # TODO: Should this be able to handle both string (e.g. 'I') and integer datatypes?
        # TODO: If datatype is changed should verify existing data can be cast to it
        if dtype in DATA_TYPES:
            self.__datatype = dtype
        elif dtype is None:
            self.__datatype = None
        else:
            # TODO: This should raise and error (what kind?)
            raise TypeError(f'Invalid datatype, {dtype}, specified for parameter')

    @property
    def units(self) -> str:
        """Returns the parameter units.

        :rtype: str
        """
        return self.__units

    @units.setter
    def units(self, unitstr: str):
        """Set the parameter units.

        :param str unitstr: String denoting the units for the parameter (e.g. mm)
        """
        self.__units = unitstr

    @property
    def modified(self) -> bool:
        return self.__modified

    @property
    def model(self) -> str:
        """Returns the model the parameter is used in.

        :rtype: str
        """
        return self.__model

    @model.setter
    def model(self, modelstr: str):
        """Set the model description for the parameter.

        :param str modelstr: String denoting the model (e.g. PRMS)
        """
        self.__model = modelstr

    @property
    def description(self) -> str:
        """Returns the parameter description.

        :rtype: str
        """
        return self.__description

    @description.setter
    def description(self, descstr: str):
        """Set the model description for the parameter.

        :param str descstr: Description string
        """
        self.__description = descstr

    @property
    def help(self) -> str:
        """Returns the help information for the parameter.

        :rtype: str
        """
        return self.__help

    @help.setter
    def help(self, helpstr: str):
        """Set the help string for the parameter.

        :param str helpstr: Help string
        """
        self.__help = helpstr

    @property
    def minimum(self) -> Union[int, float, str, None]:
        """Returns the minimum valid value for the parameter.

        :rtype: int or float or None
        """
        return self.__minimum

    @minimum.setter
    def minimum(self, value: Union[int, float, str, None]):
        """Set the minimum valid value for the parameter.

        :param value: The minimum value
        :type value: int or float or None
        """
        if self.__datatype is None or value is None:
            self.__minimum = value
        elif DATA_TYPES[self.__datatype] == 'float':
            self.__minimum = float(value)
        elif DATA_TYPES[self.__datatype] == 'integer':
            try:
                self.__minimum = int(value)
            except ValueError:
                # This happens with 'bounded' parameters
                self.__minimum = value
        else:
            self.__minimum = value

    @property
    def maximum(self) -> Union[int, float, str, None]:
        """Returns the maximum valid value for the parameter.

        :rtype: int or float or None
        """
        return self.__maximum

    @maximum.setter
    def maximum(self, value: Union[int, float, str, None]):
        """Set the maximum valid value for the parameter.

        :param value: The maximum value
        :type value: int or float or None
        """
        if self.__datatype is None or value is None:
            self.__maximum = value
        elif DATA_TYPES[self.__datatype] == 'float':
            self.__maximum = float(value)
        elif DATA_TYPES[self.__datatype] == 'integer':
            try:
                self.__maximum = int(value)
            except ValueError:
                # This happens with bounded parameters
                self.__maximum = value
        else:
            self.__maximum = value

    @property
    def default(self) -> Union[int, float, None]:
        """Returns the default value for the parameter.

        :rtype: int or float or None
        """
        return self.__default

    @default.setter
    def default(self, value: Union[int, float, None]):
        """Set the default value for the parameter.

        :param value: The default value
        :type value: int or float or None
        """
        # TODO: 2020-04-30 PAN: This should check if given value is between
        #                       min and max valid values (if set)
        if self.__datatype is None or value is None:
            self.__default = value
        elif DATA_TYPES[self.__datatype] == 'float':
            self.__default = float(value)
        elif DATA_TYPES[self.__datatype] == 'integer':
            self.__default = int(value)
        else:
            self.__default = value

    @property
    def modules(self) -> Union[List[str], None]:
        """Returns the names of the modules require the parameter.

        :rtype: list[str] or None
        """
        return self.__modules

    @modules.setter
    def modules(self, modulestr: Union[str, List[str], None]):
        """Set the names of the modules that require the parameter.

        :param modulestr: Single module name or list of module names to add
        :type modulestr: list[str] or str or None
        """
        if modulestr is not None:
            if isinstance(modulestr, list):
                self.__modules = modulestr
            else:
                self.__modules = [modulestr]
        else:
            self.__modules = None

    @property
    def dimensions(self) -> ParamDimensions:
        """Returns the Dimensions object associated with the parameter."""
        return self.__dimensions

    @property
    def ndims(self) -> int:
        """Returns the number of dimensions that are defined for the parameter.

        :rtype: int"""
        return self.__dimensions.ndims

    @property
    def data(self) -> np.ndarray:
        """Returns the data associated with the parameter.

        :rtype: np.ndarray
        """

        # TODO: Best way to prevent modification of data elements?
        if self.__data is not None:
            return self.__data
        raise ValueError(f'Parameter, {self.__name}, has no data')

    @data.setter
    def data(self, data_in):
        """Sets the data for the parameter.

        :param list data_in: A list containing the parameter data
        :raises TypeError: if the datatype for the parameter is invalid
        :raises ValueError: if the number of dimensions for the parameter is greater than 2
        """
        # Raise an error if no dimensions are defined for parameter
        if not self.ndims:
            raise ValueError(f'No dimensions have been defined for {self.name}; unable to append data')

        data_np = None

        if isinstance(data_in, list):
            data_np = np.array(data_in, dtype=DATATYPE_TO_DTYPE[self.datatype])
        elif isinstance(data_in, np.ndarray):
            data_np = data_in
        elif isinstance(data_in, pd.Series):
            data_np = data_in.to_numpy()

        if data_np.size == self.size:
            # The incoming size matches the expected size for the parameter
            if data_np.ndim < self.ndims:
                # A numpy scalar (size=1, ndim=0) should not be reshaped

                if data_np.ndim != 0:
                    # Assume data_np is 1D, parameter is 2D; there are no scalars
                    # order higher dimension possibilities.
                    data_np = data_np.reshape((-1, self.dimensions.get_dimsize_by_index(1),), order='F')
            elif data_np.ndim == self.ndims:
                # TODO: If dealing with 2D incoming data should make sure that
                #       the shape is correct compared to declared dimensions.
                pass
            else:
                raise ValueError(f'{self.__name}, source data ndim, {data_np.ndim} > parameter ndim, {self.ndims}')
        elif data_np.size > self.size and 'one' in self.__dimensions.dimensions.keys():
            # In certain circumstances it is possible for a one-dimensioned
            # parameter to be passed a data array with size > 1. If this happens
            # just use the first element from the array.
            print(f'WARNING: {self.__name}, with dimension "one" was passed {data_np.size} ' +
                  f'values; using first value only.')
            data_np = np.array(data_np[0], ndmin=1)
        else:
            err_txt = f'{self.name}: Number of dimensions for new data ({data_in.ndim}) ' + \
                      f'doesn\'t match old ({self.ndims})'
            raise IndexError(err_txt)

        if self.__data is None:
            self.__data = data_np
        elif np.array_equal(self.__data, data_np):
            pass
            # print(f'{self.__name}: updated value is equal to the old value')
        else:
            # Pre-existing data has been modified
            self.__data = data_np
            self.__modified = True

    @property
    def index_map(self):
        """Returns an ordered dictionary which maps data values to index position"""
        return OrderedDict((val, idx) for idx, val in enumerate(self.__data.tolist()))

    @property
    def size(self) -> int:
        """Return the total size of the parameter for the defined dimensions"""
        arr_shp = [dd.size for dd in self.dimensions.values()]

        # Compute the total size of the parameter
        return functools.reduce(lambda x, y: x * y, arr_shp)

    @property
    def xml(self) -> xmlET.Element:
        """Return the xml metadata for the parameter as an xml Element.

        :rtype: xmlET.Element
        """
        param_root = xmlET.Element('parameter')
        param_root.set('name', self.name)
        param_root.set('version', 'ver')
        param_root.append(self.dimensions.xml)
        return param_root

    def all_equal(self) -> bool:
        if self.__data.size > 1:
            return (self.__data == self.__data[0]).all()
        return False

    def update_element(self, index, value):
        # NOTE: index is zero-based
        # Update a single element or single row (e.g. nhru x nmonth) in the
        # parameter data array.
        if np.array_equal(self.__data, value):
            pass
            # print(f'{self.__name}: updated value is equal to the old value')
        else:
            self.__data[index] = value
            self.__modified = True

    def _value_index(self, value):
        # NOTE: returned indices are zero-based
        # Returns a list of indices where the data elements match value
        return np.where(self.__data == value)[0]

    def is_hru_param(self):
        return set(self.__dimensions.keys()).intersection({'nhru', 'ngw', 'nssr'})

    def is_seg_param(self):
        return set(self.__dimensions.keys()).intersection({'nsegment'})

    # def concat(self, data_in):
    #     """Takes a list of parameter data and concatenates it to the end of the existing parameter data.
    #
    #     This is useful when reading 2D parameter data by region where
    #     the ordering of the data must be correctly maintained in the final
    #     dataset
    #
    #     :param list data_in: Data to concatenate (or append) to existing parameter data
    #     :raises TypeError: if the datatype for the parameter is invalid
    #     :raises ValueError: if the number of dimensions for the parameter is greater than 2
    #     :raises ConcatError: if concatenation is attempted with a parameter of dimension 'one' (e.g. scalar)
    #     """
    #
    #     if not self.ndims:
    #         raise ValueError(f'No dimensions have been defined for {self.name}. Unable to concatenate data')
    #
    #     if self.__data is None:
    #         # Don't bother with the concatenation if there is no pre-existing data
    #         self.data = data_in
    #         return
    #
    #     # Convert datatype first
    #     datatype_conv = {1: self.__str_to_int, 2: self.__str_to_float,
    #                      3: self.__str_to_float, 4: self.__str_to_str}
    #
    #     if self.__datatype in DATA_TYPES.keys():
    #         data_in = datatype_conv[self.__datatype](data_in)
    #     else:
    #         raise TypeError(f'Defined datatype {self.__datatype} for parameter {self.__name} is not valid')
    #
    #     # Convert list to np.array
    #     if self.ndims == 2:
    #         data_np = np.array(data_in).reshape((-1, self.dimensions.get_dimsize_by_index(1),), order='F')
    #     elif self.ndims == 1:
    #         data_np = np.array(data_in)
    #     else:
    #         raise ValueError(f'Number of dimensions, {self.ndims}, is not supported')
    #
    #     if 'one' in self.__dimensions.dimensions.keys():
    #         # A parameter with the dimension 'one' should never have more
    #         # than 1 value. Output warning if the incoming value is different
    #         # from a pre-existing value
    #         if data_np[0] != self.__data[0]:
    #             raise ConcatError(f'Parameter, {self.__name}, with dimension "one" already ' +
    #                               f'has assigned value = {self.__data[0]}; ' +
    #                               f'Cannot concatenate additional value(s), {data_np[0]}')
    #             # print('WARNING: {} with dimension "one" has different '.format(self.__name) +
    #             #       'value ({}) from current ({}). Keeping current value.'.format(data_np[0], self.__data[0]))
    #     else:
    #         self.__data = np.concatenate((self.__data, data_np))
    #         # self.__data = data_np

    def check(self) -> str:
        """Verifies the total size of the data for the parameter matches the total declared dimension(s) size
        and returns a message.

        :rtype: str
        """

        # TODO: check that values are between min and max values
        # Check a variable to see if the number of values it has is
        # consistent with the given dimensions
        if self.has_correct_size():
            # The number of values for the defined dimensions match
            return f'{self.name}: OK'
        else:
            return f'{self.name}: BAD'

    def check_values(self) -> bool:
        """Returns true if all data values are within the min/max values for the parameter."""
        if self.__minimum is not None and self.__maximum is not None:
            # Check both ends of the range
            if not(isinstance(self.__minimum, str) or isinstance(self.__maximum, str)):
                return (self.__data >= self.__minimum).all() and (self.__data <= self.__maximum).all()
        return True

    def stats(self):
        """Returns basic statistics on parameter values"""
        Stats = namedtuple('Stats', ['name', 'min', 'max', 'mean', 'median'])

        if self.__name in ['poi_gage_id']:
            return Stats(self.__name, '', '', '', '')

        return Stats(self.__name, np.min(self.__data), np.max(self.__data),
                     np.mean(self.__data), np.median(self.__data))

    def has_correct_size(self) -> bool:
        """Verifies the total size of the data for the parameter matches the total declared dimension(s) sizes.

        :rtype: bool"""

        # Check a variable to see if the number of values it has is
        # consistent with the given dimensions

        # Get the defined size for each dimension used by the variable
        total_size = 1
        for dd in self.dimensions.keys():
            total_size *= self.dimensions.get(dd).size

        # This assumes a numpy array
        return self.data.size == total_size

    def remove_by_index(self, dim_name: str, indices):
        """Remove columns (nhru or nsegment) from data array given a list of indices"""

        if isinstance(indices, type(OrderedDict().values())):
            indices = list(indices)

        if self.__data.size == 1:
            print(f'{self.name}: Cannot reduce array of size one')
            return

        self.__data = np.delete(self.__data, indices, axis=self.dimensions.get_position(dim_name))
        self.dimensions[dim_name].size = self.__data.shape[self.dimensions.get_position(dim_name)]

    def reshape(self, new_dims):
        """Reshape a parameter, broadcasting existing values as necessary.

        :param collections.OrderedDict new_dims: Dimension names and sizes that will be used to reshape the parameter data
        """

        if self.dimensions.ndims == 1:
            if 'one' in self.dimensions.keys():
                # Reshaping from a scalar to a 1D or 2D array
                # print('Scalar to 1D or 2D')
                new_sizes = [vv.size for vv in new_dims.values()]
                tmp_data = np.broadcast_to(self.__data, new_sizes)

                # Remove the original dimension
                self.dimensions.remove('one')

                # Add the new ones
                for kk, vv in new_dims.items():
                    self.dimensions.add(kk, vv.size)

                self.__data = tmp_data
            elif set(self.dimensions.keys()).issubset(set(new_dims.keys())):
                # Reschaping a 1D to a 2D
                if len(new_dims) == 1:
                    print('ERROR: Cannot reshape from 1D array to 1D array')
                else:
                    # print('1D array to 2D array')
                    new_sizes = [vv.size for vv in new_dims.values()]
                    try:
                        tmp_data = np.broadcast_to(self.__data, new_sizes)
                    except ValueError:
                        # operands could not be broadcast together with remapped shapes
                        tmp_data = np.broadcast_to(self.__data, new_sizes[::-1]).T

                    old_dim = list(self.dimensions.keys())[0]
                    self.dimensions.remove(old_dim)

                    for kk, vv in new_dims.items():
                        self.dimensions.add(kk, vv.size)

                    self.__data = tmp_data

    def subset_by_index(self, dim_name: str, indices):
        """Reduce columns (nhru or nsegment) from data array given a list of indices"""

        if isinstance(indices, type(OrderedDict().values())):
            indices = list(indices)

        if self.__data.size == 1:
            print(f'{self.name}: Cannot reduce array of size one')
            return

        self.__data = self.__data[indices]
        self.dimensions[dim_name].size = self.__data.shape[self.dimensions.get_position(dim_name)]
        # self.__data = np.take(self.__data, indices, axis=0)
        # self.__data = np.delete(self.__data, indices, axis=self.dimensions.get_position(dim_name))

    def tolist(self) -> list:
        """Returns the parameter data as a list.

        :returns: Parameter data
        :rtype: list
        """

        # TODO: is this correct for snarea_curve?
        # Return a list of the data
        return self.__data.ravel(order='F').tolist()

    def toparamdb(self) -> str:
        """Outputs parameter data in the paramDb csv format.

        :rtype: str
        """

        outstr = '$id,{}\n'.format(self.name)

        ii = 0
        # Do not use self.tolist() here because it causes minor changes
        # to the values for floats.
        for dd in self.__data.ravel(order='F'):
            if self.datatype in [2, 3]:
                # Float and double types have to be formatted specially so
                # they aren't written in exponential notation or with
                # extraneous zeroes
                tmp = f'{dd:<20f}'.rstrip('0 ')
                if tmp[-1] == '.':
                    tmp += '0'
                outstr += f'{ii+1},{tmp}\n'
            else:
                outstr += f'{ii+1},{dd}\n'
            ii += 1
        return outstr

    def tostructure(self):
        """Returns a dictionary structure of the parameter.

        This is typically used for serializing parameters.

        :returns: dictionary structure of the parameter
        :rtype: dict
        """

        # Return all information about this parameter in the following form
        param = {'name': self.name,
                 'datatype': self.datatype,
                 'dimensions': self.dimensions.tostructure(),
                 'data': self.tolist()}
        return param

    def unique(self) -> np.ndarray:
        """Create array of unique values from the parameter data.

        :returns: Array of unique values
        :rtype: np.ndarray
        """
        return np.unique(self.__data)

    @staticmethod
    def __str_to_float(data):
        """Convert strings to a floats.

        :param list[str] data: list of data

        :returns: array of floats
        :rtype: list[float]
        """

        # Convert provide list of data to float
        return [float(vv) for vv in data]
        # try:
        #     return [float(vv) for vv in data]
        # except ValueError as ve:
        #     print(ve)

    @staticmethod
    def __str_to_int(data):
        """Converts strings to integers.

        :param list[str] data: list of data

        :returns: array of integers
        :rtype: list[int]
        """

        # Convert list of data to integer
        try:
            return [int(vv) for vv in data]
        except ValueError:
            # Perhaps it's a float, try converting to float and then integer
            tmp = [float(vv) for vv in data]
            return [int(vv) for vv in tmp]

    @staticmethod
    def __str_to_str(data):
        """Null op for string-to-string conversion.

        :param list[str] data: list of data

        :returns: unmodified array of data
        :rtype: list[str]
        """

        # nop for list of strings
        # 2019-05-22 PAN: For python 3 force string type to byte
        #                 otherwise they are treated as unicode
        #                 which breaks the write_netcdf() routine.
        # 2019-06-26 PAN: Removed the encode because it broken writing the ASCII
        #                 parameter files. Instead the conversion to ascii is
        #                 handled in the write_netcdf routine of ParameterSet
        # data = [dd.encode() for dd in data]
        if not all(isinstance(dd, str) for dd in data):
            return [str(vv) for vv in data]
        return data
