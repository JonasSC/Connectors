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

"""Contains the MultiInputConnector class"""

import asyncio
import weakref
from .. import _common as common
from . import _multioutput as multioutput
from ._baseclasses import InputConnector

__all__ = ("MultiInputConnector", "ConditionalMultiInputConnector")


class MultiInputConnector(InputConnector):
    """A connector-class that replaces special setter methods, that allow to pass
    multiple values, so they can be used to connect different objects in a processing
    chain.
    """

    def __init__(self, instance, method, remove_method, replace_method, observers, laziness, parallelization, executor):
        """
        :param instance: the instance of which the method is replaced by this connector
        :param method: the unbound method, that is replaced by this connector
        :param remove_method: an unbound method, that is used to remove data, that
                              has been added through this connector
        :param replace_method: an unbound method, that is used to replace data,
                               that has been added through this connector
        :param observers: the names of output methods that are affected by passing a value to this connector
        :param laziness: a flag from the :class:`connectors.Laziness` enum. See
                         the :meth:`~connectors.connectors.MultiInputConnector.set_laziness`
                         method for details
        :param parallelization: a flag from the :class:`connectors.Parallelization` enum.
                                See the :meth:`~connectors.connectors.MultiInputConnector.set_parallelization`
                                method for details
        :param executor: an :class:`~connectors._common._executors.Executor` instance,
                         that can be created with the :func:`connectors.executor`
                         function. See the :meth:`~connectors.connectors.MultiInputConnector.set_executor`
                         method for details
        """
        InputConnector.__init__(self, instance, method, laziness, parallelization, executor)
        self.__remove = remove_method
        self.__replace = replace_method
        self.__observers = common.resolve_observers(instance=instance, observers=observers)
        self._connections = weakref.WeakKeyDictionary()
        self._multi_connections = weakref.WeakKeyDictionary()
        self.__announcements = set()        # stores output connectors, that announced a value change
        self.__notifications = {}           # maps output connectors, that notified about a value change, to pending input values
        self.__multi_notifications = {}     # maps data ids to pending input values; is used, when a multi-output notifies this connector
        self.__running = False              # is used to prevent, that the setter is executed multiple times for the same changes
        self.__computable = common.Event()  # is set, when there is no pending announcement
        self.__computable.set()

    def __call__(self, *args, **kwargs):
        """By making the object callable, it mimics the replaced method.
        This method also notifies the output method that are affected by this call (observers).

        :param `*args,**kwargs`: parameters with which the replaced method has been called
        :returns: the return value of the replaced method
        """
        # announce the value change
        non_lazy_inputs = common.NonLazyInputs(common.Laziness.ON_ANNOUNCE)
        for o in self.__observers:
            o._announce(self, non_lazy_inputs)
        # call the replaced method
        self.__running = True
        try:
            changed = self._executor.run_coroutine(self.__request_pending(self._executor))    # retrieve the announced values from the connectors first, so that everything is added in the correct order
        finally:
            self.__running = False
        result = self._method(self._instance(), *args, **kwargs)
        # notify observers about the value change
        for data_id, value in changed.items():
            self._add_to_notification_condition_checks(data_id, value)
        value = common.get_first_argument(self._method, *args, **kwargs)
        self._add_to_notification_condition_checks(data_id=result, value=value)
        self._notify_observers()
        # execute the non-lazy inputs
        non_lazy_inputs.execute(self._executor)
        # return the result of the method call
        return result

    def __getitem__(self, key):
        """Allows to use a multi-input connector as multiple single-input connectors.

        The key, under which a virtual single-input connector is accessed, shall
        also be returned the data ID, under which the result of the connected
        output is stored.

        :param key: a key for accessing a particular virtual single-input connector
        :returns: a :class:`~connectors._common._multiinput_item.MultiInputItem`, which enhances
                  the decorated method with the functionality of the virtual
                  single-input connector
        """
        return common.MultiInputItem(connector=self,
                                     instance=self._instance(),
                                     replace_method=self.__replace,
                                     key=key,
                                     observers=self.__observers,
                                     executor=self._executor)

    def _connect(self, connector, key=None):    # pylint: disable=arguments-differ; the key is only used by the multi-input connector
        """This method is called from an :class:`~connectors.OutputConnector`,
        when it is  being connected to this :class:`~connectors.MultiInputConnector`.

        :param connector: the output connector that shall be connected to this multi-input connector
        :param key: the data ID, under which the data of the given connector is stored
        :returns: yields self (see the :class:`~connectors.MacroInputConnector`,
                  where :meth:`~connectors.MacroInputConnector._connect` yields
                  all the :class:`~connectors.SingleInputConnector`s that it exports)
        """
        yield self
        self.__announcements.add(connector)
        if isinstance(connector, multioutput.MultiOutputConnector):
            self._multi_connections[connector] = set()
        else:
            self._connections[connector] = key
            self.__notifications[connector] = None  # create a placeholder to add the values in the correct order
        non_lazy_inputs = common.NonLazyInputs(situation=common.Laziness.ON_CONNECT)
        self._announce(connector, non_lazy_inputs=non_lazy_inputs)
        non_lazy_inputs.execute(self._executor)

    def _disconnect(self, connector):
        """This method is called from an :class:`~connectors.OutputConnector`,
        when it is  being disconnected from this :class:`~connectors.MultiInputConnector`.

        :param connector: the output connector from which this connector shall be disconnected
        :returns: yields self (see the :class:`~connectors.MacroInputConnector`,
                  where :meth:`~connectors.MacroInputConnector._disconnect` yields
                  all the :class:`~connectors.SingleInputConnector`s that it exports)
        """
        self.__announcements.discard(connector)
        if connector in self.__notifications:
            del self.__notifications[connector]
        non_lazy_inputs = common.NonLazyInputs(situation=common.Laziness.ON_CONNECT)
        common.forward_announcement(connector=self,
                                    observers=self.__observers,
                                    non_lazy_inputs=non_lazy_inputs,
                                    laziness=self._laziness)
        if isinstance(connector, multioutput.MultiOutputConnector):
            for data_id in self._multi_connections[connector]:
                self.__remove(self._instance(), data_id)
                self._add_to_notification_condition_checks(data_id)
            del self._multi_connections[connector]
        else:
            data_id = self._connections[connector]
            if data_id is not None:
                self.__remove(self._instance(), data_id)
            self._add_to_notification_condition_checks(data_id)
            del self._connections[connector]
        self._notify_observers()
        non_lazy_inputs.execute(self._executor)
        yield self

    def _announce(self, connector, non_lazy_inputs):
        """This method is to notify this multi-input connector, when a connected
        output connector can produce updated data.

        :param connector: the output connector whose value is about to change
        :param non_lazy_inputs: a :class:`~connectors._common._non_lazy_inputs.NonLazyInputs`
                                instance to which input connectors can be appended,
                                if they request an immediate re-computation (see
                                the :meth:`~connectors.connectors.MultiInputConnector.set_laziness`
                                method for more about lazy execution)
        """
        self.__computable.clear()
        self.__announcements.add(connector)
        common.forward_announcement(connector=self,
                                    observers=self.__observers,
                                    non_lazy_inputs=non_lazy_inputs,
                                    laziness=self._laziness)

    async def _notify(self, connector, value, executor):
        """This method is to notify this multi-input connector, when a connected
        output connector has produced updated data.

        :param connector: the output connector whose value has changed
        :param value: the updated data from the output connector
        :param executor: the :class:`~connectors._common._executors.Executor`
                         instance, which managed the computation of the output
                         connector, and which shall be used for the computation
                         of this connector, in case it is not lazy.
        """
        self.__notifications[connector] = value
        self.__announcements.discard(connector)
        if not self.__announcements:
            self.__computable.set()
        if self._laziness == common.Laziness.ON_NOTIFY:
            await self._request(executor)

    async def _notify_multi(self, connector, values, executor):
        """This method is to notify this multi-input connector, when a connected
        multi-output connector has produced updated data.

        :param connector: the output connector whose value has changed
        :param values: a dictionary, that maps data ids to the updated values
        :param executor: the :class:`~connectors._common._executors.Executor`
                         instance, which managed the computation of the output
                         connector, and which shall be used for the computation
                         of this connector, in case it is not lazy.
        """
        self.__multi_notifications[connector] = values
        self.__announcements.discard(connector)
        if not self.__announcements:
            self.__computable.set()
        if self._laziness == common.Laziness.ON_NOTIFY:
            await self._request(executor)

    def _cancel(self, connector):
        """Notifies this multi-input connector, that an announced value change
        is not going to happen.

        :param connector: the output connector whose value change is canceled
        """
        self.__announcements.discard(connector)
        if not self.__announcements:
            self.__computable.set()
            for o in self.__observers:
                o._cancel(self)     # pylint: disable=protected-access; the _cancel method is meant to be called from other connectors, but not from outside this package

    async def _request(self, executor):
        """This method retrieves the updated data from the connected output connectors
        and recomputes this connector (if necessary).
        It is called by the output connectors, that are affected by this connector,
        (observers) when their values have to be computed.

        :param executor: the :class:`~connectors._common._executors.Executor` instance,
                         that manages the current computations
        """
        if not self.__running:
            self.__running = True
            try:
                changed = await self.__request_pending(executor)
                # notify the observers
                for data_id, value in changed.items():
                    self._add_to_notification_condition_checks(data_id, value)
                self._notify_observers()
            finally:
                self.__running = False

    async def __request_pending(self, executor):
        """This method retrieves the updated data from the connected output connectors
        and recomputes this connector (if necessary).

        This is basically the :meth:`~connectors.connectors.MultiInputConnector._request`
        method, but without notifying the observing output connectors. It returns
        a dictionary, that maps data_ids to updated values, which can be used to
        trigger the notifications.

        :param executor: the :class:`~connectors._common._executors.Executor` instance,
                         that manages the current computations
        :returns: a dictionary, that maps data_ids to updated values
        """
        # wait for the announced value changes
        if self.__announcements:
            await asyncio.gather(*(a._request(executor) for a in self.__announcements))
            await self.__computable.wait(executor)
        # execute the setter
        single_tasks = {}
        if self.__notifications:
            for connector, value in self.__notifications.items():
                data_id = self._connections[connector]
                if data_id is None:
                    task = executor.run_method(self._parallelization,
                                               self._method,
                                               self._instance(),
                                               value)
                else:
                    task = executor.run_method(self._parallelization,
                                               self.__replace,
                                               self._instance(),
                                               data_id,
                                               value)
                single_tasks[connector] = (task, value)
            self.__notifications.clear()
        remove_tasks = []
        multi_tasks = {}
        if self.__multi_notifications:
            for connector, data in self.__multi_notifications.items():
                to_remove = self._multi_connections[connector] - data.keys()
                remove_tasks += [executor.run_method(self._parallelization,
                                                     self.__remove,
                                                     self._instance(),
                                                     data_id)
                                 for data_id in to_remove]
                multi_tasks[connector] = [(executor.run_method(self._parallelization,
                                                               self.__replace,
                                                               self._instance(),
                                                               data_id,
                                                               value),
                                           value)
                                          for data_id, value in data.items()]
            self.__multi_notifications.clear()
        # save the data ids
        if remove_tasks:
            await asyncio.gather(*remove_tasks)
        changed = {}
        for connector, (task, value) in single_tasks.items():
            data_id = await task
            self._connections[connector] = data_id
            changed[data_id] = value
        for connector, tasks in multi_tasks.items():
            data_ids = set()
            for task, value in tasks:
                data_id = await task
                changed[data_id] = value
                data_ids.add(data_id)
            self._multi_connections[connector] = data_ids
        return changed

    def _notify_observers(self):
        """Checks the notification condition and notifies the observers about value
        changes or cancellations.

        This method is not private, because it is also used by the :class:`~connectors._common.MultiInputItem`
        class.
        """
        if self._check_notification_condition():
            for o in self.__observers:
                o._notify(self)     # pylint: disable=protected-access; these methods are called by the connectors, but are not part of the public API.
        else:
            for o in self.__observers:
                o._cancel(self)     # pylint: disable=protected-access; these methods are called by the connectors, but are not part of the public API.

    def _add_to_notification_condition_checks(self, data_id, value=None):
        """A protected helper method to determine, if the observing output connectors
        have to be notified at the end of the :meth:`~connectors.connectors.MultiInputConnector._request`
        method.

        This method is meant to be overridden in derived classes, that implement
        a conditional notification of the observing output connectors.
        """

    def _check_notification_condition(self):   # pylint: disable=no-self-use; this method is a hook for derived classes
        """A protected helper method to determine, if the observing output connectors
        have to be notified at the end of the :meth:`~connectors.connectors.MultiInputConnector._request`
        method.

        This method is meant to be overridden in derived classes, that implement
        a conditional notification of the observing output connectors.
        """
        return True


class ConditionalMultiInputConnector(MultiInputConnector):
    """A variant of the :class:`~connectors.connectors.MultiInputConnector`, in
    which it depends on externally defined conditions, if the value changes are
    announced to the observing output connectors, and if the output connectors
    are notified about value changes.

    The conditions are defined as methods, which are called before sending an
    announcement or a notification to the observing output connectors and which
    shall return a Boolean, that is True, if the output connector shall be informed,
    about the (expected) value change, or False, if the output shall be sent a
    cancellation notice.
    """

    def __init__(self, instance, method,                            # pylint: disable=too-many-arguments; this constructor may be complicated, since the class is instantiated through the decorators, which have a much simpler API
                 remove_method, replace_method,
                 observers, announce_condition, notify_condition,
                 laziness, parallelization, executor):
        """
        :param instance: the instance of which the method is replaced by this connector
        :param method: the unbound method, that is replaced by this connector
        :param remove_method: an unbound method, that is used to remove data, that
                              has been added through this connector
        :param replace_method: an unbound method, that is used to replace data,
                               that has been added through this connector
        :param observers: the names of output methods that are affected by passing a value to this connector
        :param announce_condition: a method, that defines the condition for the
                                   announcements to the observing output connectors.
                                   This method must accept the data ID of the changed
                                   output connector as an argument in addition to
                                   ``self``
        :param notify_condition: a method, that defines the condition for the
                                 notifications to the observing output connectors.
                                 This method must accept the data ID and the new
                                 input value as an argument in addition to ``self``
        :param laziness: a flag from the :class:`connectors.Laziness` enum. See
                         the :meth:`set_laziness` method for details
        :param parallelization: a flag from the :class:`connectors.Parallelization` enum.
                                See the :meth:`set_parallelization` method for details
        :param executor: an :class:`~connectors._common._executors.Executor` instance,
                         that can be created with the :func:`connectors.executor`
                         function. See the :meth:`~connectors.connectors.MultiInputConnector.set_executor`
                         method for details
        """
        MultiInputConnector.__init__(self, instance, method,
                                     remove_method, replace_method,
                                     observers,
                                     laziness, parallelization, executor)
        self.__announce_condition = announce_condition
        self.__notify_condition = notify_condition
        self.__pending_notification_condition_checks = []

    def _announce(self, connector, non_lazy_inputs):
        """This method is to notify this input connector, when a connected output
        connector can produce updated data.

        :param connector: the output connector whose value is about to change
        :param non_lazy_inputs: a :class:`~connectors._common._non_lazy_inputs.NonLazyInputs`
                                instance to which input connectors can be appended,
                                if they request an immediate re-computation (see
                                the :meth:`~connectors.connectors.MultiInputConnector.set_laziness`
                                method for more about lazy execution)
        """
        if self.__announce_condition(self._instance(), self._connections[connector]):
            super()._announce(connector, non_lazy_inputs)

    def _add_to_notification_condition_checks(self, data_id, value=None):
        """A protected helper method to determine, if the observing output connectors
        have to be notified at the end of the :meth:`~connectors.MultiInputConnector._request`
        method.
        """
        self.__pending_notification_condition_checks.append((data_id, value))

    def _check_notification_condition(self):
        """A protected helper method to determine, if the observing output connectors
        have to be notified at the end of the :meth:`~connectors.MultiInputConnector._request`
        method.
        """
        result = False
        for data_id, value in self.__pending_notification_condition_checks:
            result = result or self.__notify_condition(self._instance(), data_id, value)
        self.__pending_notification_condition_checks.clear()
        return result
