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

"""Contains a base class for the macro connector decorators."""


class MacroDecorator:
    """Base class for the decorators for macro connectors"""

    def __init__(self):
        self._method = None

    def __call__(self, method):
        """Is called in order to replace the decorated method with this decorator.

        :param method: the unbound method, that was decorated with this decorator
        :returns: this decorator
        """
        self._method = method
        return self

    def __get__(self, instance, instance_type):
        """Is called, when the decorated method is accessed.

        :param instance: the instance of which a method shall be replaced
        :param instance_type: the type of the instance
        :returns: a :class:`MacroInputConnector` or :class:`MacroOutputConnector` instance
        """
        raise NotImplementedError("This method should have been implemented in a derived class")
