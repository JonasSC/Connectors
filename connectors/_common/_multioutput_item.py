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

"""Contains the :class:`connectors._common._multioutput_item.MultiOutputItem` class"""

__all__ = ("MultiOutputItem",)


class MultiOutputItem:
    """An object, that is returned by the :meth:`~connectors.connectors.MultiOutputConnector.__getitem__`
    overload.

    It simulates the behavior of a single-output connector, so it is possible to
    use a multi-output connector as arbitrarily many single-outputs.
    """

    def __init__(self, connector, instance, key):
        """
        :param connector: the multi-output connector
        :param instance: the instance of which the method was replaced by the
                         multi-output connector
        :param key: the key with which the multi-output has been accessed.
        """
        self.__connector = connector
        self.__instance = instance
        self.__key = key

    def __call__(self, *args, **kwargs):
        """Calls the given getter method with the given key as the first argument.

        :param `*args,**kwargs`: additional arguments for the method
        :returns: the return value of the getter method
        """
        return self.__connector(self.__key, *args, **kwargs)

    def connect(self, connector):
        """Connects this virtual single-output to an output.

        :param connector: the connector, to which this connector shall be connected
        :returns: the instance of which the method was replaced by the multi-output connector
        """
        self.__connector._connect(self, connector)
        return self.__instance

    def disconnect(self, connector):
        """Disconnects this virtual single-output from an input, to which is has been connected..

        :param connector: the connector, from which this connector shall be disconnected
        :returns: the instance of which the method was replaced by the multi-output connector
        """
        self.__connector._disconnect(self, connector)
        return self.__instance

    def key(self):
        """Returns the key, with which the multi-output connector has been accessed."""
        return self.__key

    async def _request(self, executor, *args, **kwargs):
        """Causes this multi-output connector to re-compute its value and notifies
        the connected input connectors.
        This method is called by a connected input connector, when it needs the
        result value of this output connector.

        :param executor: the :class:`~connectors._common._executors.Executor` instance,
                         that manages the current computations
        :returns: the result value of the output connector
        """
        await self.__connector._request_key(executor, self.__key, False, *args, **kwargs)   # pylint: disable=protected-access; this call stays within the context of a multi-output connector.
