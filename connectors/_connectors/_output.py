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

"""Contains the OutputConnector class"""

import asyncio
import weakref
from ._baseclasses import Connector

__all__ = ("OutputConnector",)


class OutputConnector(Connector):
    """A Connector-class that replaces getter methods, so they can be used to
    connect different objects.
    """
    def __init__(self, instance, method, caching, parallelization, executor):
        """
        :param instance: the instance in which the method is replaced by this connector
        :param method: the unbound method that is replaced by this connector
        :param caching: True, if caching shall be enabled, False otherwise. See
                        the :meth:`set_caching` method for details
        :param parallelization: a flag from the :class:`connectors.Parallelization` enum.
                                See the :meth:`set_parallelization` method for details
        :param executor: an :class:`Executor` instance, that can be created with the
                         :func:`connectors.executor` function. See the :meth:`set_executor`
                         method for details
        """
        Connector.__init__(self, instance, method, parallelization, executor)
        self.__caching = caching
        self.__announcements = weakref.WeakSet()
        self.__connections = set()      # stores tuples (connector, instance). The instance is only saved to prevent its deletion through garbage collection
        self.__result = None
        self.__result_is_valid = False
        self.__lock = asyncio.Lock()    # is locked as long as the new output is being computed

    def __call__(self, *args, **kwargs):
        """By making the object callable, it mimics the replaced method.
        This method also notifies the input connectors, that are connected to
        this output.
        :param args, kwargs: parameters with which the replaced method has been called
        :returns: the return value of the replaced method
        """
        if self.__result_is_valid:
            return self.__result
        return self._executor.run_until_complete(self.__execute_and_notify(self._executor, *args, **kwargs))

    def connect(self, connector):
        """A method for connecting this output connector to an input connector.
        :param connector: the input connector to which this connector shall be connected
        :returns: the instance of which this :class:`OutputConnector` has replaced a method
        """
        for c in connector._connect(self):
            self.__connections.add((c, c._get_instance()))
        return self._instance()

    def disconnect(self, connector):
        """A method for disconnecting this output connector from an input connector,
        to which it is currently connected.
        :param connector: the input connector from which this connector shall be disconnected
        :returns: the instance of which this :class:`OutputConnector` has replaced a method
        """
        for c in connector._disconnect(self):
            self.__connections.remove((c, c._get_instance()))
        return self._instance()

    def set_caching(self, caching):
        """Specifies, if the result value of this output connector shall be cached.
        If caching is enabled and the result value is retrieved (e.g. through a
        connection or by calling the connector), the cached value is returned and
        the replaced getter method is not called unless the result value has to
        be re-computed, because an observed setter method has changed a parameter
        for the computation. In this case, the getter method is only called once,
        independent of the number of connections through which the result value
        has to be passed.
        :param caching: True, if caching shall be enabled, False otherwise
        """
        self.__caching = caching
        if not self.__caching:
            self.__result_is_valid = False
            self.__result = None

    def _announce(self, connector, non_lazy_inputs):
        """This method is to notify this output connector, when an observed input
        connector (a setter from self._instance) can retrieve updated data.
        :param connector: the input connector, which is about to change a value
        :param non_lazy_inputs: a NonLazyInputs instance to which input connectors
                                can be appended, if they request an immediate
                                re-computation (see the InputConnector's
                                :meth:`set_laziness` method for more about lazy execution)
        """
        self.__announcements.add(connector)
        self.__result_is_valid = False
        self.__result = None
        self.__announce_to_connected(non_lazy_inputs)

    def _notify(self, connector, non_lazy_inputs):
        """This method is to notify this output connector, when an observed input
        connector (a setter from self._instance) has retrieved updated data.
        :param connector: the input connector, which has changed a value
        :param non_lazy_inputs: a NonLazyInputs instance to which input connectors
                                can be appended, if they request an immediate
                                re-computation (see the InputConnector's
                                :meth:`set_laziness` method for more about lazy execution)
        """
        self.__announcements.discard(connector)
        self.__result_is_valid = False
        self.__result = None
        self.__announce_to_connected(non_lazy_inputs)

    async def _request(self, connector, executor):
        """Causes this output connector to re-compute its value and notifies the
        connected input connectors.
        This method is called by a connected input connector, when it needs the
        result value of this output connector.
        :param connector: the input connector, from which the request is issued
        :param executor: the :class:`Executor` instance, that manages the current computations
        :returns: the result value of the output connector
        """
        with await self.__lock:
            if self.__result_is_valid:
                return self.__result
            else:
                result = await self.__execute(executor)
                if len(self.__connections) > 1:
                    tasks = tuple(c._notify(self, result, executor) for c, _ in self.__connections if c != connector)   # the requesting input connector does not get notified, because it gets the value as a return value
                    await asyncio.wait(tasks)
                return result

    async def __execute(self, executor, *args, **kwargs):
        """Re-computes the result value of the output connector.
        If any observed input connectors have announced value changes, their execution
        is also triggered by this method.
        :param executor: the :class:`Executor` instance, that manages the current computations
        :param args, kwargs: parameters with which the replaced getter method shall be called
        :returns: the result value of the output connector
        """
        tasks = []
        while self.__announcements:
            s = self.__announcements.pop()
            tasks.append(executor.create_task(s._execute(executor)))
        for t in tasks:
            await t
        result = await executor.run_method(self._parallelization, self._method, self._instance(), *args, **kwargs)
        if self.__caching:
            self.__result = result
            self.__result_is_valid = True
        return result

    async def __execute_and_notify(self, executor, *args, **kwargs):
        """Calls the :meth:`__execute` method and notifies the connected input connectors.
        This is a helper method to invoke these actions through an Executor's
        :meth:`run_method` method.
        :param executor: the :class:`Executor` instance, that manages the current computations
        :param args, kwargs: parameters with which the replaced getter method shall be called
        :returns: the result value of the output connector
        """
        result = await self.__execute(executor, *args, **kwargs)
        if self.__connections:
            await asyncio.wait(tuple(c._notify(self, result, executor) for c, _ in self.__connections))
        return result

    def __announce_to_connected(self, non_lazy_inputs):
        """Announces, that the result value of this output connector has changed,
        to the connected input connectors.
        :param non_lazy_inputs: a NonLazyInputs instance to which input connectors
                                can be appended, if they request an immediate
                                re-computation (see the InputConnector's
                                :meth:`set_laziness` method for more about lazy execution)
        """
        for c in self.__connections:
            c[0]._announce(self, non_lazy_inputs)
