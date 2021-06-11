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

"""Contains test classes for multi-output connectors"""

import connectors
from ._baseclass import BaseTestClass

__all__ = ("MultiOutputWithKeys", "MultiOutputWithoutKeys", "MultiOutputWithVolatileKeys")


class MultiOutputWithKeys(BaseTestClass):
    """Features a multi-output connector with a keys method."""

    def _initialize(self):
        """is called in the super class's constructor"""
        self.__value = 0
        self.__keys = {2, 3, 5}

    @connectors.Input("get_value")
    def set_value(self, value):
        """Sets the value"""
        self._register_call(methodname="set_value", value=value)
        self.__value = value
        return self

    @connectors.Input("get_value")
    def set_keys(self, keys):
        """Changes the return value of the keys method"""
        self.__keys = keys

    @connectors.MultiOutput()
    def get_value(self, key):
        """Returns the product of the value and the key"""
        result = self.__value * key
        self._register_call(methodname="get_value", value=result)
        return result

    @get_value.keys
    def keys(self):
        """Returns a couple of example keys for the get_value method"""
        self._register_call(methodname="keys", value=self.__keys)
        return self.__keys


class MultiOutputWithoutKeys(BaseTestClass):
    """Features a multi-output connector without a keys method."""

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
        """Returns the product of the value and the key"""
        result = self.__value * key
        self._register_call(methodname="get_value", value=result)
        return result


class MultiOutputWithVolatileKeys(BaseTestClass):
    """Features a multi-output connector with a keys method, that supports only one iteration."""

    def _initialize(self):
        """is called in the super class's constructor"""
        self.__value = 0
        self.__keys = {2, 3, 5}

    @connectors.Input("get_value")
    def set_value(self, value):
        """Sets the value"""
        self._register_call(methodname="set_value", value=value)
        self.__value = value
        return self

    @connectors.Input("get_value")
    def set_keys(self, keys):
        """Changes the return value of the keys method"""
        self.__keys = keys

    @connectors.MultiOutput()
    def get_value(self, key):
        """Returns the product of the value and the key"""
        result = self.__value * key
        self._register_call(methodname="get_value", value=result)
        return result

    @get_value.keys
    def keys(self):
        """Returns a couple of example keys for the get_value method"""
        self._register_call(methodname="keys", value=self.__keys)
        for k in self.__keys:
            yield k
