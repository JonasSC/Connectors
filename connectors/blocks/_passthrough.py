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

"""Contains the :class:`~connectors.blocks.PassThrough` class."""

import connectors

__all__ = ("PassThrough",)


class PassThrough:
    """A trivial processing block, that simply passes its input value to its output.
    Instances of this can be useful to distribute a single parameter to multiple
    inputs, if this parameter is used in several places in a processing chain.
    """

    def __init__(self, data=None):
        """
        :param data: the input object
        """
        self.__data = data

    @connectors.Output(caching=False)
    def output(self):
        """Returns the object, that has been passed with the :meth:`~connectors.blocks.PassThrough.input` method.

        :returns: the given object
        """
        return self.__data

    @connectors.Input("output")
    def input(self, data):
        """Specifies the input object.

        :param data: the input object
        :returns: the :class:`~connectors.blocks.PassThrough` instance
        """
        self.__data = data
        return self
