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

"""Contains the MultiInputConnector class"""

import asyncio
import collections
import weakref
from .._lib import Laziness, NonLazyInputs
from ._baseclasses import InputConnector

__all__ = ("MultiInputConnector",)


class MultiInputConnector(InputConnector):
    """A Connector-class that replaces special setter methods, that allow to pass
    multiple values, so they can be used to connect different objects in a processing
    chain."""
    def __init__(self, instance, method, remove_method, replace_method, observers, laziness, parallelization, executor):
        """
        :param instance: the instance in which the method is replaced by this connector
        :param method: the unbound method, that is replaced by this connector
        :param remove_method: an unbound method, that is used to remove data, that
                              has been added through this connector
        :param replace_method: an unbound method, that is used to replace data,
                               that has been added through this connector
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
        self.__remove = remove_method
        self.__replace = replace_method
        self.__connections = weakref.WeakKeyDictionary()
        self.__announcements = set()
        self.__notifications = collections.OrderedDict()
        self.__lock = asyncio.Lock()    # is locked as long as the method is being executed

    def __call__(self, *args, **kwargs):
        """By making the object callable, it mimics the replaced method.
        This method also notifies the output method that are affected by this call (observers).
        :param args, kwargs: parameters with which the replaced method has been called
        :returns: the return value of the replaced method
        """
        self._executor.run_until_complete(self._execute(self._executor))    # retrieve the announced values from the connectors first, so that everything is added in the correct order
        result = self._method(self._instance(), *args, **kwargs)
        self._notify_observers()
        return result

    def _connect(self, connector):
        """This method is called from an :class:`OutputConnector`, when it is  being
        connected to this :class:`InputConnector`.
        :param connector: the output connector that shall be connected to this multi-input connector
        :returns: yields self (see the MacroInputConnector, where _connect yields
                  all the InputConnectors that it represents)
        """
        self.__connections[connector] = None
        self.__announcements.add(connector)
        self.__notifications[connector] = None  # create a placeholder in the notifications dict
        return InputConnector._connect(self, connector)

    def _disconnect(self, connector):
        """This method is called from an :class:`OutputConnector`, when it is  being
        disconnected from this :class:`InputConnector`.
        :param connector: the output connector from which this connector shall be disconnected
        :returns: yields self (see the MacroInputConnector, where _connect yields
                  all the InputConnectors that it represents)
        """
        self.__announcements.discard(connector)
        if connector in self.__notifications:
            del self.__notifications[connector]
        data_id = self.__connections[connector]
        if data_id is not None:
            self.__remove(self._instance(), data_id)
        del self.__connections[connector]
        non_lazy_inputs = NonLazyInputs(situation=Laziness.ON_CONNECT)
        InputConnector._announce(self, connector, non_lazy_inputs=non_lazy_inputs)
        non_lazy_inputs.execute(self._executor)
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
        self.__announcements.add(connector)
        self.__notifications[connector] = None  # create a placeholder in the notifications dict
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
        self.__notifications[connector] = value
        self.__announcements.discard(connector)
        if self._laziness == Laziness.ON_NOTIFY:
            await self._execute(executor)
            await self._announce_to_observers(executor)

    async def _execute(self, executor):
        """This method retrieves the updated data from the connected output connectors
        and recomputes this connector (if necessary).
        It is called by the output connectors, that are affected by this connector,
        (observers) when their values have to be computed.
        :param executor: the :class:`Executor` instance, that manages the current computations
        """
        with await self.__lock:
            # retrieve the values from the announcements
            tasks = {}
            while self.__announcements:
                output_connector = self.__announcements.pop()
                tasks[output_connector] = executor.create_task(output_connector._request(self, executor))
            for output_connector in tasks:
                self.__notifications[output_connector] = await tasks[output_connector]
            # update the multi input
            await executor.run_method(self._parallelization, self.__process_notifications, self._instance())

    def __process_notifications(self, _):
        """A private helper method to invoke the processing of the retrieved
        data from the connected output connectors through an Executor's
        :meth:`run_method` method.
        :param _: not used, but necessary to emulate the behavior of unbound
                  methods, that are also invoked through :meth:`run_method` and which
                  take their instance as a first parameter.
        """
        for output_connector in self.__notifications:
            data_id = self.__connections[output_connector]
            value = self.__notifications[output_connector]
            if data_id is None:
                self.__connections[output_connector] = self._method(self._instance(), value)
            else:
                self.__replace(self._instance(), data_id, value)
        self.__notifications.clear()
