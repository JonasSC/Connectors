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

"""Contains the SingleInputConnector class"""

import asyncio
from .._lib import Laziness
from ._baseclasses import InputConnector

__all__ = ("SingleInputConnector",)


class SingleInputConnector(InputConnector):
    """A Connector-class that replaces setter methods, so they can be used to connect
    different objects in a processing chain."""
    def __init__(self, instance, method, observers, laziness, parallelization, executor):
        """
        :param instance: the instance in which the method is replaced by this connector
        :param method: the unbound method, that is replaced by this connector
        :param observers: the names of output methods that are affected by passing a value to this connector
        :param laziness: a flag from the :class:`connectors.Laziness` enum. See
                         the :meth:`set_laziness` method for details
        :param parallelization: a flag from the :class:`connectors.Parallelization` enum.
                                See the :meth:`set_parallelization` method for details
        :param executor: an :class:`Executor` instance, that can be created with the
                         :func:`connectors.executor` function. See the :meth:`set_executor`
                         method for details
        """
        InputConnector.__init__(self, instance, method, observers, laziness, parallelization, executor)
        self.__announcement = None
        self.__notification = None
        self.__lock = asyncio.Lock()    # is locked as long as the method is being executed

    def __call__(self, *args, **kwargs):
        """By making the object callable, it mimics the replaced method.
        This method also notifies the output method that are affected by this call (observers).

        :param args, kwargs: parameters with which the replaced method shall be called
        :returns: the return value of the replaced method
        """
        result = self._method(self._instance(), *args, **kwargs)
        self.__announcement = None
        self.__notification = None
        self._notify_observers()
        return result

    def _disconnect(self, connector):
        """This method is called from an :class:`OutputConnector`, when it is  being
        disconnected from this :class:`InputConnector`.

        :param connector: the output connector from which this connector shall be disconnected
        :returns: yields self (see the MacroInputConnector, where _connect yields
                  all the InputConnectors that it represents)
        """
        self._executor.run_until_complete(self._execute(self._executor))
        yield self

    def _announce(self, connector, non_lazy_inputs):
        """This method is to notify this input connector, when a connected output
        connector can produce updated data.

        :param connector: the output connector whose value is about to change
        :param non_lazy_inputs: a NonLazyInputs instance to which input connectors
                                can be appended, if they request an immediate
                                re-computation (see the InputConnector's
                                :meth:`set_laziness` method for more about lazy execution)
        """
        self.__announcement = connector
        self.__notification = None
        InputConnector._announce(self, connector, non_lazy_inputs)

    async def _notify(self, connector, value, executor):
        """This method is to notify this input connector, when a connected output
        connector has produced updated data.

        :param connector: the output connector whose value has changed
        :param value: the updated data from the output connector
        :param executor: the :class:`Executor` instance, which managed the computation
                         of the output connector, and which shall be used for the
                         computation of this connector, in case it is not lazy.
        """
        if self._laziness == Laziness.ON_NOTIFY:
            await executor.run_method(self._parallelization, self._method, self._instance(), value)
            self.__notification = None
            await self._announce_to_observers(executor)
        else:
            self.__notification = value
        self.__announcement = None

    async def _execute(self, executor):
        """This method retrieves the updated data from the connected output connectors
        and recomputes this connector (if necessary).
        It is called by the output connectors, that are affected by this connector,
        (observers) when their values have to be computed.

        :param executor: the :class:`Executor` instance, that manages the current computations
        """
        with await self.__lock:
            if self.__announcement is not None:
                value = await self.__announcement._request(self, executor)
                await executor.run_method(self._parallelization, self._method, self._instance(), value)
                self.__announcement = None
            elif self.__notification is not None:
                await executor.run_method(self._parallelization, self._method, self._instance(), self.__notification)
                self.__notification = None
