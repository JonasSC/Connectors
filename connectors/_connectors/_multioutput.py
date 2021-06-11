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

"""Contains the :class:`~connectors.connectors.MultiOutputConnector` class"""

import asyncio
import collections
import weakref
from .. import _common as common
from . import _multiinput as multiinput
from .. import _proxies as proxies
from ._baseclasses import Connector

__all__ = ("MultiOutputConnector",)


class MultiOutputConnector(Connector):
    """A connector-class that replaces getter methods, which accept one parameter,
    so they can be used as a multi-output connector, which can be connected to
    different objects.

    Multi-output connectors can either be used to route a dynamic number of values
    to a multi-input connector. Or the argument for the ``[]``-operator can be used
    to parameterize the getter method.
    """

    def __init__(self, instance, method, caching, parallelization, executor, keys):
        """
        :param instance: the instance of which the method is replaced by this connector
        :param method: the unbound method that is replaced by this connector
        :param caching: True, if caching shall be enabled, False otherwise. See
                        the :meth:`~connectors.connectors.MultiOutputConnector.set_caching`
                        method for details
        :param parallelization: a flag from the :class:`connectors.Parallelization` enum.
                                See the :meth:`~connectors.connectors.MultiOutputConnector.set_parallelization`
                                method for details
        :param executor: an :class:`~connectors._common._executors.Executor` instance,
                         that can be created with the :func:`connectors.executor`
                         function. See the :meth:`~connectors.connectors.MultiOutputConnector.set_executor`
                         method for details
        :param keys: an unbound method, that returns the keys for which this multi-output
                     connector shall compute values, when it is connected to a
                     multi-input connector
        """
        Connector.__init__(self, instance, method, parallelization, executor)
        self.__caching = caching
        self.__keys = keys
        self.__announcements = weakref.WeakSet()
        self.__multi_connections = set()    # stores tuples (connector, instance). The instance is only saved to prevent its deletion through reference counting
        self.__single_connections = {}      # output key -> set([(connector, instance), ...])
        self.__items = {}                   # output key -> MultiOutputItem
        self.__results = {}                 # output key -> result. Cached results
        self.__valid_results = set()        # set of output keys, for which the cached results are still valid
        self.__running = set()              # set of output keys, is used to prevent, that the getter is executed multiple times for the same changes
        self.__computable = common.Event()  # is set, when there is no pending announcement
        self.__computable.set()

    def __call__(self, *args, **kwargs):
        """By making the object callable, it mimics the replaced method.
        This method also notifies the input connectors, that are connected to
        this output.

        :param `*args,**kwargs`: parameters with which the replaced method has been called
        :returns: the return value of the replaced method
        """
        key = common.get_first_argument(self._method, *args, **kwargs)
        if key in self.__valid_results:
            return self.__results[key]
        return self._executor.run_coroutine(self._request_key(self._executor, key, True, *args, **kwargs))

    def __getitem__(self, key):
        """Allows to use a multi-output connector as multiple single-output connectors.

        :param key: a key for accessing a particular virtual single-output connector
        :returns: a :class:`connectors._common._multioutput_item.MultiOutputItem`,
                  which enhances the decorated method with the functionality of
                  the virtual single-output connector
        """
        return common.MultiOutputItem(connector=self, instance=self._instance(), key=key)

    def connect(self, connector):
        """A method for connecting this output connector to an input connector.
        This is only allowed with multi-input connectors. In order to establish
        a connection to a single-input connector, use the ``[]`` operator to specify,
        which value shall be passed through the connection.

        :param connector: the input connector to which this connector shall be connected
        :returns: the instance of which this :class:`OutputConnector` has replaced a method
        """
        if isinstance(connector, (multiinput.MultiInputConnector, proxies.MultiInputProxy)):
            for c in connector._connect(self):
                self.__multi_connections.add((c, c._get_instance()))
            return self._instance()
        else:
            raise TypeError("MultiOutputConnectors can only be connected to MultiInputConnectors."
                            "Select a single output with the MultiOutputConnector's [] operator.")

    def disconnect(self, connector):
        """A method for disconnecting this output connector from an input connector,
        to which it is currently connected.

        :param connector: the input connector from which this connector shall be disconnected
        :returns: the instance of which this :class:`OutputConnector` has replaced a method
        """
        if isinstance(connector, (multiinput.MultiInputConnector, proxies.MultiInputProxy)):
            for c in connector._disconnect(self):
                self.__multi_connections.remove((c, c._get_instance()))
            return self._instance()
        else:
            raise TypeError("MultiOutputConnectors can only be connected to MultiInputConnectors."
                            "Select a single output with the MultiOutputConnector's [] operator.")

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
            self.__valid_results.clear()
            self.__results.clear()

    def _connect(self, item, connector):
        """Connects a virtual single output to the given input connector.

        This method is called from a :class:`connectors._common._multioutput_item.MultiOutputItem`
        instance.

        :param item: the :class:`connectors._common._multioutput_item.MultiOutputItem`
                     instance, from which this method is called
        :param connector: the input connector to which the connection shall be established
        """
        key = item.key()
        if key in self.__items:
            item = self.__items[key]
        else:
            item = common.MultiOutputItem(connector=self, instance=self._instance(), key=key)   # create a new MultiOutputItem, because the given one could come from a proxy
            self.__items[key] = item
        connections = self.__single_connections.setdefault(key, set())
        for c in connector._connect(item):
            connections.add((c, c._get_instance()))

    def _disconnect(self, item, connector):
        """Disconnects a virtual single output from the given input connector.

        This method is called from a :class:`connectors._common._multioutput_item.MultiOutputItem`
        instance.

        :param item: the :class:`connectors._common._multioutput_item.MultiOutputItem`
                     instance, from which this method is called
        :param connector: the input connector to which the connection shall be broken
        """
        key = item.key()
        item = self.__items.get(key, item)
        connections = self.__single_connections[key]
        for c in connector._disconnect(item):
            connections.remove((c, c._get_instance()))
        if not connections:
            del self.__single_connections[key]
            del self.__items[key]

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
        self.__valid_results.clear()
        self.__computable.clear()
        for c, _ in self.__multi_connections:
            c._announce(self, non_lazy_inputs)
        for key in self.__single_connections:
            item = self.__items[key]
            for c, _ in self.__single_connections[key]:
                c._announce(item, non_lazy_inputs)

    def _notify(self, connector):
        """This method is to notify this multi-output connector, when an observed
        input connector (a setter from the instance to which this connector belongs)
        has retrieved updated data.

        :param connector: the input connector, which has changed a value
        :param non_lazy_inputs: a :class:`~connectors._common._non_lazy_inputs.NonLazyInputs`
                                instance to which input connectors can be appended,
                                if they request an immediate re-computation (see
                                the :class:`~connectors._connectors._base_classes.InputConnector`'s
                                :meth:`~connectors._connectors._base_classes.InputConnector.set_laziness`
                                method for more about lazy execution)
        """
        self.__valid_results.clear()
        self.__results.clear()
        self.__announcements.discard(connector)
        if not self.__announcements:
            self.__computable.set()

    def _cancel(self, connector):
        """Notifies this multi-output connector, that an announced value change
        is not going to happen.

        :param connector: the observed input connector whose value change is canceled
        """
        self.__announcements.discard(connector)
        if not self.__announcements:
            self.__computable.set()
            self.__valid_results = set(self.__results.keys())   # if all announcements have been canceled, the cached results are still valid
            for c, _ in self.__multi_connections:
                c._cancel(self)         # pylint: disable=protected-access; the _cancel method is meant to be called from other connectors, but not from outside this package
            for key in self.__single_connections:
                item = self.__items[key]
                for c, _ in self.__single_connections[key]:
                    c._cancel(item)     # pylint: disable=protected-access; the _cancel method is meant to be called from other connectors, but not from outside this package

    async def _request(self, executor, *args, **kwargs):
        """Causes this multi-output connector to re-compute its values and notifies
        the connected input connectors.
        This method is called by a connected input connector, when it needs the
        result value of this output connector.

        The keys for which new values are computed are specified with the given
        ``keys`` method.

        :param executor: the :class:`~connectors._common._executors.Executor` instance,
                         that manages the current computations
        """
        await self.__request_announcements(executor)
        keys = self.__keys(self._instance())
        if not isinstance(keys, collections.abc.Sequence):  # repack to a tuple, if necessary, to allow multiple iteration passes
            keys = tuple(keys)
        values = await asyncio.gather(*(self.__compute_key(executor, key, False, *args, **kwargs) for key in keys))
        dictionary = {k: v for k, v in zip(keys, values)}
        await asyncio.gather(*(mi._notify_multi(self, dictionary, executor) for mi, _ in self.__multi_connections))         # pylint: disable=protected-access; these methods are called by the connectors, but are not part of the public API.

    async def _request_key(self, executor, key, key_in_args, *args, **kwargs):   # pylint: disable=too-many-branches
        """Causes this multi-output connector to re-compute one of its values and
        notifies the connected input connectors.
        This method is called by a connected input connector, when it needs the
        result value of this output connector.

        :param executor: the :class:`~connectors._common._executors.Executor` instance,
                         that manages the current computations
        :param key: the key for which the output shall be recomputed
        :param key_in_args: if the given key is already included in the *args or
                            **kwargs parameters
        :returns: the result value of the output connector
        """
        if not self.__running:
            await self.__request_announcements(executor)
            if key in self.__valid_results:     # this can happen, if all announcements have been canceled
                return self.__results[key]
        return await self.__compute_key(executor, key, key_in_args, *args, **kwargs)

    async def __compute_key(self, executor, key, key_in_args, *args, **kwargs):
        """Similar to :meth:`~connectors.connectors.MultiOutput._request_key`, but
        it assumes, that the announced value changes have already happened.
        """
        if key not in self.__running:
            self.__running.add(key)
            try:
                if key in self.__valid_results:
                    result = self.__results[key]
                else:
                    # execute the getter
                    if key_in_args:
                        result = await executor.run_method(self._parallelization, self._method,
                                                           self._instance(), *args, **kwargs)
                    else:
                        result = await executor.run_method(self._parallelization, self._method,
                                                           self._instance(), key, *args, **kwargs)
                    if self.__caching:
                        self.__results[key] = result
                        self.__valid_results.add(key)
                # notify the connected inputs
                if key in self.__single_connections:
                    item = self.__items[key]
                    tasks = [c._notify(item, result, executor) for c, _ in self.__single_connections[key]]
                    if tasks:
                        await asyncio.gather(*tasks)
                return result
            finally:
                self.__running.discard(key)

    async def __request_announcements(self, executor):
        """Requests the announced value changes from the observed inputs."""
        if self.__announcements:
            await asyncio.gather(*(a._request(executor) for a in self.__announcements))
            await self.__computable.wait(executor)
