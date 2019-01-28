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

"""Contains a base class for the test classes"""


class BaseTestClass:
    """A base class, that provides basic infrastructure for the test classes"""

    def __init__(self, call_logger=None, identifier=None):
        """
        :param call_logger: a :class:`CallLogger` instance
        :param identifier: a unique identifier, by which the instance of the
                           test class can be identified (e.g. in debug prints)
        """
        self.__call_logger = call_logger
        if identifier is None:
            self.__identifier = id(self)
        else:
            self.__identifier = identifier
        self._initialize()

    def __str__(self):
        """Returns a string, that describes the instance of the test class"""
        return "<{path}.{name} ({identifier}) object at {address:x})>".format(path=self.__module__,
                                                                              name=self.__class__.__name__,
                                                                              identifier=self.__identifier,
                                                                              address=id(self))

    def get_identifier(self):
        """Returns the unique identifier for this"""
        return self.__identifier

    def _initialize(self):
        """This method is called in the constructor and can be overridden by derived classes"""

    def _register_call(self, methodname, value=None):
        """Adds an entry to the call log.
        :param methodname: the name of the method, that has been called as a string
        :param value: the parameter value, with which the method has been called
        """
        if self.__call_logger is not None:
            self.__call_logger.register_call(instance=self, methodname=methodname, value=value)
