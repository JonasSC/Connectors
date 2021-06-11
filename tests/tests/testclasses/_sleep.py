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

"""Contains test classes with delays in their output connectors for testing the parallelization"""

import time
import connectors
from ._baseclass import BaseTestClass

__all__ = ("SleepInOutput", "SleepInInput", "SleepInMultiInput", "SleepInMultiOutput")


class SleepInOutput(BaseTestClass):
    """Sleeps one second, when the output connector is executed"""

    def _initialize(self):
        """is called in the super class's constructor"""
        self.__value = None

    @connectors.Input("get_value")
    def set_value(self, value):                 # pylint: disable=missing-docstring
        self._register_call(methodname="set_value", value=value)
        self.__value = value
        return self

    @connectors.Output()
    def get_value(self):                        # pylint: disable=missing-docstring
        self._register_call(methodname="get_value", value=self.__value)
        time.sleep(1.0)
        return self.__value


class SleepInInput(BaseTestClass):
    """Sleeps one second, when the input connector is executed"""

    def _initialize(self):
        """is called in the super class's constructor"""
        self.__value = None

    @connectors.Input("get_value", parallelization=connectors.Parallelization.THREAD)
    def set_value(self, value):                 # pylint: disable=missing-docstring
        self._register_call(methodname="set_value", value=value)
        self.__value = value
        time.sleep(1.0)
        return self

    @connectors.Output()
    def get_value(self):                        # pylint: disable=missing-docstring
        self._register_call(methodname="get_value", value=self.__value)
        return self.__value


class SleepInMultiInput(BaseTestClass):
    """Sleeps one second, when the multi-input connector is executed"""

    def _initialize(self):
        """is called in the super class's constructor"""
        self.__data = connectors.MultiInputData()

    @connectors.MultiInput("get_values", parallelization=connectors.Parallelization.THREAD)
    def add_value(self, value):                 # pylint: disable=missing-docstring
        time.sleep(1.0)
        self._register_call(methodname="add_value", value=value)
        return self.__data.add(value)

    @add_value.remove
    def remove_value(self, data_id):            # pylint: disable=missing-docstring
        self._register_call(methodname="remove_value", value=data_id)
        del self.__data[data_id]
        return self

    @add_value.replace
    def replace_value(self, data_id, value):    # pylint: disable=missing-docstring
        self._register_call(methodname="replace_value", value=data_id)
        self.__data[data_id] = value
        return self

    @connectors.Output()
    def get_values(self):                       # pylint: disable=missing-docstring
        self._register_call(methodname="get_values", value=list(self.__data.values()))
        return list(self.__data.values())


class SleepInMultiOutput(BaseTestClass):
    """Features a multi-output connector, that sleeps for a second before returning the result."""

    def _initialize(self):
        """is called in the super class's constructor"""
        self.__value = 0

    @connectors.Input("get_value")
    def set_value(self, value):
        """Sets the value"""
        self._register_call(methodname="set_value", value=value)
        self.__value = value
        return self

    @connectors.MultiOutput()
    def get_value(self, key):
        """Sleeps for a second and returns the product of the value and the key"""
        time.sleep(1.0)
        result = self.__value * key
        self._register_call(methodname="get_value", value=result)
        return result
