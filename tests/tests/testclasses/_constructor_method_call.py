# This file is a part of the "Connectors" package
# Copyright (C) 2017-2019 Jonas Schulte-Coerne
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

"""Contains test classes, that call their connectors during their initialization,
which could provoke cyclic references or weak references to deleted objects."""

import connectors
from ._baseclass import BaseTestClass
from ._simple import Simple

__all__ = ("ConstructorMethodCall",
           "ConstructorLazinessChange",
           "ConstructorCachingChange",
           "ConstructorParallelizationChange",
           "ConstructorExecutorChange")


class ConstructorMethodCall(BaseTestClass):
    """Calls connectors within the constructor"""

    def _initialize(self):
        self.__values = connectors.MultiInputData()
        self.set_first_value(None)
        data_id = self.add_value(None)
        self.replace_value(data_id, 0.0)
        self.remove_value(data_id)
        assert self.get_values() == [None]

    @connectors.Input("get_values")
    def set_first_value(self, value):           # pylint: disable=missing-docstring
        self._register_call(methodname="set_first_value", value=value)
        self.__value = value
        return self

    @connectors.MultiInput("get_values")
    def add_value(self, value):                 # pylint: disable=missing-docstring
        self._register_call(methodname="add_value", value=value)
        return self.__values.add(value)

    @add_value.remove
    def remove_value(self, data_id):            # pylint: disable=missing-docstring
        self._register_call(methodname="remove_value", value=data_id)
        del self.__values[data_id]
        return self

    @add_value.replace
    def replace_value(self, data_id, value):    # pylint: disable=missing-docstring
        self._register_call(methodname="replace_value", value=data_id)
        self.__values[data_id] = value
        return self

    @connectors.Output()
    def get_values(self):                       # pylint: disable=missing-docstring
        result = [self.__value] + list(self.__values.values())
        self._register_call(methodname="get_values", value=result)
        return result


class ConstructorLazinessChange(Simple):
    """Changes a connectors laziness within the constructor, which prevents calling
    other connectors from the same line as the instantiation of the object.
    """

    def _initialize(self):
        Simple._initialize(self)
        self.set_value.set_laziness(connectors.Laziness.ON_NOTIFY)


class ConstructorCachingChange(Simple):
    """Changes a connectors caching behavior within the constructor, which prevents
    calling other connectors from the same line as the instantiation of the object.
    """

    def _initialize(self):
        Simple._initialize(self)
        self.get_value.set_caching(False)


class ConstructorParallelizationChange(Simple):
    """Changes a connectors parallelization setting within the constructor, which
    prevents calling other connectors from the same line as the instantiation of
    the object.
    """

    def _initialize(self):
        Simple._initialize(self)
        self.get_value.set_parallelization(connectors.Parallelization.PROCESS)


class ConstructorExecutorChange(Simple):
    """Changes a connectors executor within the constructor, which prevents calling
    other connectors from the same line as the instantiation of the object.
    """

    def _initialize(self):
        Simple._initialize(self)
        self.get_value.set_executor(connectors.executor(processes=None))
