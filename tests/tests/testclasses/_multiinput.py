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

"""Contains test classes for multi-input connectors"""

import connectors
from ._baseclass import BaseTestClass

__all__ = ("NonReplacingMultiInput", "ReplacingMultiInput")


class NonReplacingMultiInput(BaseTestClass):
    """Features a multi-input connector without a replace method"""

    def _initialize(self):
        """is called in the super class's constructor"""
        self.__data = connectors.MultiInputData()

    @connectors.MultiInput("get_values")
    def add_value(self, value):
        """adds a value to the output list"""
        data_id = self.__data.add(value)
        self._register_call("add_value", [value], data_id)
        return data_id

    @add_value.remove
    def remove_value(self, data_id):
        """removes a value from the output list"""
        self._register_call("remove_value", [data_id], self)
        del self.__data[data_id]
        return self

    @connectors.Output()
    def get_values(self):
        """returns the output list"""
        result = tuple(self.__data.values())
        self._register_call("get_values", [], result)
        return result


class ReplacingMultiInput(BaseTestClass):
    """Features a multi-input connector with a replace method"""

    def _initialize(self):
        """is called in the super class's constructor"""
        self.__data = connectors.MultiInputData()

    @connectors.MultiInput("get_values")
    def add_value(self, value):
        """adds a value to the output list"""
        data_id = self.__data.add(value)
        self._register_call("add_value", [value], data_id)
        return data_id

    @add_value.remove
    def remove_value(self, data_id):
        """removes a value from the output list"""
        self._register_call("remove_value", [data_id], self)
        del self.__data[data_id]
        return self

    @add_value.replace
    def replace_value(self, data_id, value):
        """replaces a value in the output list"""
        self._register_call("replace_value", [data_id, value], data_id)
        self.__data[data_id] = value
        return data_id

    @connectors.Output()
    def get_values(self):
        """returns the output list"""
        result = tuple(self.__data.values())
        self._register_call("get_values", [], result)
        return result
