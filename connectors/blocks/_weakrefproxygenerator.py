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

"""Contains the :class:`WeakrefProxyGenerator` class."""

import weakref
import connectors

__all__ = ("WeakrefProxyGenerator",)


class WeakrefProxyGenerator:
    """A helper class to reduce memory usage in certain processing chains by
    discarding intermediate results. It takes an object as input and outputs a
    weak reference proxy to it.
    The deletion of the strong reference to the input object can triggered by connecting
    the output connector for the final result to this class's :meth:`~WeakrefProxyGenerator.delete_reference`
    method. This will cause the input object to be garbage collected, if no further
    references to it exist.
    This class should be used in combination with the caching of the final result,
    since this prevents, that the deleted input data is required to re-compute the
    result, when it's retrieved repeatedly.
    """

    def __init__(self, data=None):
        """
        :param data: the input object
        """
        self.__data = data

    @connectors.Output(caching=False)
    def output(self):
        """
        Creates and returns a weak reference proxy to the input object.
        As long as the object has not been garbage collected, this proxy should
        behave exactly as the input object.

        :returns: a weak reference proxy to the input object, if it can be weakly
                  referenced, otherwise the object itself
        """
        try:
            return weakref.proxy(self.__data)
        except TypeError:       # if the data does not allow weak references to it
            return self.__data

    @connectors.Input("output")
    def input(self, data):
        """Specifies the input object.

        :param data: the input object
        :returns: the WeakrefProxyGenerator instance
        """
        self.__data = data
        return self

    @connectors.Input(laziness=connectors.Laziness.ON_NOTIFY)
    def delete_reference(self, *args, **kwargs):    # pylint: disable=unused-argument; passing arguments to the delete_reference method shall not raise an error, so it can be connected to any output
        """Causes the strong reference to the input object to be deleted, so that
        the input object can be garbage collected.
        This connector should be connected to the output of the final result, so
        it is notified, when the result has been computed and the input object is
        no longer required.

        :param `*args,**kwargs`: these parameters just there fore compatibility with
                                 other input connectors and are not used in this method
        :returns: the WeakrefProxyGenerator instance
        """
        self.__data = None
        return self
