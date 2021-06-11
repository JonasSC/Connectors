# This file is a part of the "Connectors" package
# Copyright (C) 2017-2021 Jonas Schulte-Coerne
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License along
# with this program. If not, see <http://www.gnu.org/licenses/>.

"""Contains the :class:`~connectors.MultiInputData` class"""

import collections

__all__ = ("MultiInputData",)


class MultiInputData(collections.OrderedDict):
    # pylint: disable=wrong-spelling-in-docstring;    avoid that the spell checker complains about the code in this comment
    """A container for data that is managed with a multi-input connector.
    This is basically an :class:`~collections.OrderedDict` with an add method,
    that stores the added data under a unique key.
    This facilitates the implementation of a class with a :class:`~connectors.MultiInput` connector:

    >>> import connectors
    >>> class ReplacingMultiInput:
    ...     def __init__(self):
    ...         self.__data = connectors.MultiInputData()
    ...
    ...     @connectors.MultiInput()
    ...     def add_value(self, value):
    ...         return self.__data.add(value)
    ...
    ...     @add_value.remove
    ...     def remove_value(self, data_id):
    ...         del self.__data[data_id]
    ...
    ...     @add_value.replace
    ...     def replace_value(self, data_id, value):
    ...         self.__data[data_id] = value
    ...         return data_id

    """

    def __init__(self, datas=()):
        """
        :param datas: an optional sequence of data objects, that shall be added to the container
        """
        collections.OrderedDict.__init__(self)
        self.__last_id = 0
        for data in datas:
            self.add(data)

    def add(self, data):
        """Adds a data set to the container.

        :param data: the data set that shall be added
        :returns: the id under which the data is stored
        """
        while self.__last_id in self:
            self.__last_id += 1
        self[self.__last_id] = data
        return self.__last_id
