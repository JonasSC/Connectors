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

"""Contains a simple test class, that outputs its input"""

import connectors
from .baseclass import BaseTestClass

__all__ = ("Simple",)


class Simple(BaseTestClass):
    """Returns the input connectors parameter at the output and logs calls."""
    def _initialize(self):
        """is called in the super class's constructor"""
        self.__value = None

    @connectors.Input("get_value")
    def set_value(self, value):
        """sets the internal value"""
        self._register_call(methodname="set_value", value=value)
        self.__value = value
        return self

    @connectors.Output()
    def get_value(self):
        """returns the internal value"""
        self._register_call(methodname="get_value", value=self.__value)
        return self.__value
