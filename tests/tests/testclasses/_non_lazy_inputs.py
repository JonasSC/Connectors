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

"""Contains a test class with non-lazy input connectors"""

import connectors
from ._baseclass import BaseTestClass

__all__ = ("NonLazyInputs",)


class NonLazyInputs(BaseTestClass):
    """Has a non-lazy input connector and a non-lazy multi-input connector"""
    def _initialize(self):
        """is called in the super class's constructor"""
        self.__data = connectors.MultiInputData()

    @connectors.Input(laziness=connectors.Laziness.ON_ANNOUNCE)
    def set_value(self, value):         # pylint: disable=missing-docstring
        self._register_call(methodname="set_value", value=value)
        return self

    @connectors.MultiInput(laziness=connectors.Laziness.ON_ANNOUNCE)
    def add_value(self, value):         # pylint: disable=missing-docstring
        self._register_call(methodname="add_value", value=value)
        return self.__data.add(value)

    @add_value.remove
    def remove_value(self, data_id):    # pylint: disable=missing-docstring
        self._register_call(methodname="remove_value", value=data_id)
        del self.__data[data_id]
        return self

    @add_value.replace
    def replace_value(self, data_id, value):    # pylint: disable=missing-docstring
        self._register_call(methodname="replace_value", value=data_id)
        self.__data[data_id] = value
        return self
