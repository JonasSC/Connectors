# This file is a part of the "Connectors" package
# Copyright (C) 2017-2018 Jonas Schulte-Coerne
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

"""contains a test class with an output, that depends on multiple inputs"""

import connectors
from ._baseclass import BaseTestClass

__all__ = ("MultipleInputs",)


class MultipleInputs(BaseTestClass):
    """A test class with an output connector, that depends on two input connectors"""
    def _initialize(self):
        """is called in the super class's constructor"""
        self.__value1 = None
        self.__value2 = None

    @connectors.Input("get_values")
    def set_value1(self, value):    # pylint: disable=missing-docstring
        self._register_call(methodname="set_value1", value=value)
        self.__value1 = value
        return self

    @connectors.Input("get_values")
    def set_value2(self, value):    # pylint: disable=missing-docstring
        self._register_call(methodname="set_value2", value=value)
        self.__value2 = value
        return self

    @connectors.Output()
    def get_values(self):           # pylint: disable=missing-docstring
        self._register_call(methodname="get_values", value=(self.__value1, self.__value2))
        return (self.__value1, self.__value2)
