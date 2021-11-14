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

"""Contains a base class for the test classes"""

from ..helper import ignore


class BaseTestClass:
    """A base class, that provides basic infrastructure for the test classes"""

    def __init__(self, call_logger=None):
        """
        :param call_logger: a :class:`CallLogger` instance
        """
        self.__call_logger = call_logger
        self._initialize()

    def _initialize(self):
        """This method is called in the constructor and can be overridden by derived classes"""

    def _register_call(self, method_name, parameters=ignore, return_value=ignore):
        """Adds an entry to the call log.
        :param methodname: the name of the method, that has been called as a string
        :param parameters: optional value for a list of parameter values, with which the method has been called
        :param return_value: optional value for the return value of the method call
        """
        if self.__call_logger is not None:
            self.__call_logger.register_call(instance=self,
                                             method_name=method_name,
                                             parameters=parameters,
                                             return_value=return_value)
