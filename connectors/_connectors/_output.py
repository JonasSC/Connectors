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

"""Contains the :class:`~connectors.connectors.OutputConnector` class"""

import asyncio
import weakref
from .. import _common as common
from ._baseclasses import Connector

__all__ = ("OutputConnector",)


class OutputConnector(Connector):
    """A connector-class that replaces getter methods, so they can be used to
    connect different objects.
    """

    def __init__(self, instance, method, caching, parallelization, executor):
        """
        :param instance: the instance of which the method is replaced by this connector
        :param method: the unbound method that is replaced by this connector
        :param caching: True, if caching shall be enabled, False otherwise. See
                        the :meth:`~connectors.connectors.OutputConnector.set_caching`
                        method for details
        :param parallelization: a flag from the :class:`connectors.Parallelization` enum.
                                See the :meth:`~connectors.connectors.OutputConnector.set_parallelization`
                                method for details
        :param executor: an :class:`~connectors._common._executors.Executor` instance,
                         that can be created with the :func:`connectors.executor`
                         function. See the :meth:`~connectors.connectors.OutputConnector.set_executor`
                         method for details
        """
        Connector.__init__(self, instance, method, parallelization, executor)
        self.__caching = caching
        self.__announcements = weakref.WeakSet()
        self.__connections = set()          # stores tuples (connector, instance). The instance is only saved to prevent its deletion through reference counting
        self.__result = None
        self.__result_is_valid = False
        self.__observed_has_changed = True  # this is used to track, if all inputs, on which this output depends have canceled their announcements, in which case, the cached result remains valid
        self.__running = False              # is used to prevent, that the getter is executed multiple times for the same changes
        self.__computable = common.Event()  # is set, when there is no pending announcement
        self.__computable.set()

    def __call__(self, *args, **kwargs):
        """By making the object callable, it mimics the replaced method.
        This method also notifies the input connectors, that are connected to
        this output.

        :param `*args,**kwargs`: parameters with which the replaced method has been called
        :returns: the return value of the replaced method
        """
        if self.__result_is_valid:
            return self.__result
        return self._executor.run_coroutine(self._request(self._executor, *args, **kwargs))

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
        connector (a setter from the instance to which this connector belongs)
        can retrieve updated data.

        :param connector: the input connector, which is about to change a value
        :param non_lazy_inputs: a :class:`~connectors._common._non_lazy_inputs.NonLazyInputs`
                                instance to which input connectors can be appended,
                                if they request an immediate re-computation (see
                                the :class:`~connectors._connectors._base_classes.InputConnector`'s
                                :meth:`~connectors._connectors._base_classes.InputConnector.set_laziness`
                                method for more about lazy execution)
        """
        self.__announcements.add(connector)
        self.__result_is_valid = False
        self.__computable.clear()
        for c, _ in self.__connections:
            c._announce(self, non_lazy_inputs)

    def _notify(self, connector):
        """This method is to notify this output connector, when an observed input
        connector (a setter from the instance to which this connector belongs)
        has retrieved updated data.

        :param connector: the input connector, which has changed a value
        :param non_lazy_inputs: a :class:`~connectors._common._non_lazy_inputs.NonLazyInputs`
                                instance to which input connectors can be appended,
                                if they request an immediate re-computation (see
                                the :class:`~connectors._connectors._base_classes.InputConnector`'s
                                :meth:`~connectors._connectors._base_classes.InputConnector.set_laziness`
                                method for more about lazy execution)
        """
        self.__result_is_valid = False
        self.__observed_has_changed = True
        self.__result = None
        self.__announcements.discard(connector)
        if not self.__announcements:
            self.__computable.set()

    def _cancel(self, connector):
        """Notifies this output connector, that an announced value change is not
        going to happen.

        :param connector: the observed input connector whose value change is canceled
        """
        self.__announcements.discard(connector)
        if not self.__announcements:
            self.__computable.set()
            self.__result_is_valid = not self.__observed_has_changed    # if all announcements have been canceled, the cached result is still valid
            for c, _ in self.__connections:
                c._cancel(self)     # pylint: disable=protected-access; the _cancel method is meant to be called from other connectors, but not from outside this package

    async def _request(self, executor, *args, **kwargs):
        """Causes this output connector to re-compute its value and notifies the
        connected input connectors.
        This method is called by a connected input connector, when it needs the
        result value of this output connector.

        :param executor: the :class:`~connectors._common._executors.Executor` instance,
                         that manages the current computations
        :returns: the result value of the output connector
        """
        if not self.__running:
            self.__running = True
            try:
                if self.__result_is_valid:
                    if self.__connections:
                        await asyncio.gather(*(c._notify(self, self.__result, executor) for c, _ in self.__connections))
                    return self.__result
                else:
                    # wait for the announced value changes
                    if self.__announcements:
                        await asyncio.gather(*(a._request(executor) for a in self.__announcements))
                        await self.__computable.wait(executor)
                        if self.__result_is_valid:  # this can happen, if all announcements have been canceled
                            return self.__result
                    # execute the getter
                    result = await executor.run_method(self._parallelization, self._method,
                                                       self._instance(), *args, **kwargs)
                    if self.__caching:
                        self.__result = result
                        self.__result_is_valid = True
                        self.__observed_has_changed = False
                    # notify the connected inputs
                    if self.__connections:
                        await asyncio.gather(*(c._notify(self, result, executor) for c, _ in self.__connections))
                    return result
            finally:
                self.__running = False
