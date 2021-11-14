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

"""Contains test classes each of which features multiple outputs, that depend on the same input"""

import connectors
from ._baseclass import BaseTestClass

__all__ = ("MultipleOutputs", "MultiInputMultipleOutputs")


class MultipleOutputs(BaseTestClass):
    """Has two output connectors that depend on one input connector"""

    def _initialize(self):
        """is called in the super class's constructor"""
        self.__value = None

    @connectors.Input(("get_value", "get_bool"))
    def set_value(self, value):                 # pylint: disable=missing-docstring
        self._register_call(method_name="set_value", parameters=[value], return_value=self)
        self.__value = value
        return self

    @connectors.Output()
    def get_value(self):                        # pylint: disable=missing-docstring
        self._register_call(method_name="get_value", parameters=[], return_value=self.__value)
        return self.__value

    @connectors.Output()
    def get_bool(self):                         # pylint: disable=missing-docstring
        result = bool(self.__value)
        self._register_call(method_name="get_bool", parameters=[], return_value=result)
        return result


class MultiInputMultipleOutputs(BaseTestClass):
    """Has two output connectors that depend on one multi-input connector"""

    def _initialize(self):
        """is called in the super class's constructor"""
        self.__data = connectors.MultiInputData()

    @connectors.MultiInput(("get_values", "get_bools"))
    def add_value(self, value):                 # pylint: disable=missing-docstring
        data_id = self.__data.add(value)
        self._register_call(method_name="add_value", parameters=[value], return_value=data_id)
        return data_id

    @add_value.remove
    def remove_value(self, data_id):            # pylint: disable=missing-docstring
        self._register_call(method_name="remove_value", parameters=[data_id], return_value=self)
        del self.__data[data_id]
        return self

    @add_value.replace
    def replace_value(self, data_id, value):    # pylint: disable=missing-docstring
        self._register_call(method_name="replace_value", parameters=[data_id, value], return_value=data_id)
        self.__data[data_id] = value
        return data_id

    @connectors.Output()
    def get_values(self):                       # pylint: disable=missing-docstring
        result = tuple(self.__data.values())
        self._register_call(method_name="get_values", parameters=[], return_value=result)
        return result

    @connectors.Output()
    def get_bools(self):                        # pylint: disable=missing-docstring
        result = tuple(bool(v) for v in self.__data.values())
        self._register_call(method_name="get_bools", parameters=[], return_value=result)
        return result
