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
from .. import _common as common
from ._baseclasses import InputConnector

__all__ = ("MultiInputConnector", "ConditionalMultiInputConnector")


class MultiInputConnector(InputConnector):
    """A Connector-class that replaces special setter methods, that allow to pass
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
                         the :meth:`set_laziness` method for details
        :param parallelization: a flag from the :class:`connectors.Parallelization` enum.
                                See the :meth:`set_parallelization` method for details
        :param executor: an :class:`Executor` instance, that can be created with the
                         :func:`connectors.executor` function. See the :meth:`set_executor`
                         method for details
        """
        InputConnector.__init__(self, instance, method, laziness, parallelization, executor)
        self.__remove = remove_method
        self.__replace = replace_method
        self.__observers = common.resolve_observers(instance=instance, observers=observers)
        self._connections = weakref.WeakKeyDictionary()
        self.__announcements = set()
        self.__notifications = collections.OrderedDict()
        self.__running = False              # is used to prevent, that the setter is executed multiple times for the same changes
        self.__computable = common.Event()  # is set, when there is no pending announcement
        self.__computable.set()

    def __call__(self, *args, **kwargs):
        """By making the object callable, it mimics the replaced method.
        This method also notifies the output method that are affected by this call (observers).

        :param args, kwargs: parameters with which the replaced method has been called
        :returns: the return value of the replaced method
        """
        # announce the value change
        non_lazy_inputs = common.NonLazyInputs(common.Laziness.ON_ANNOUNCE)
        for o in self.__observers:
            o._announce(self, non_lazy_inputs)
        # call the replaced method
        self._executor.run_coroutine(self._request(self._executor))    # retrieve the announced values from the connectors first, so that everything is added in the correct order
        result = self._method(self._instance(), *args, **kwargs)
        # notify observers about the value change
        self._conditional_observer_notification(result, *args, **kwargs)
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
        :returns: a MultiinputItem, which enhances the decorated method with the
                  functionality of the virtual single-input connector
        """
        return common.MultiinputItem(connector=self,
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
        self._connections[connector] = key
        self.__announcements.add(connector)
        self.__notifications[connector] = None  # create a placeholder in the notifications dict
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
        data_id = self._connections[connector]
        if data_id is not None:
            self.__remove(self._instance(), data_id)
        del self._connections[connector]
        self._conditional_observer_notification(data_id)
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
        self.__computable.clear()
        self.__announcements.add(connector)
        common.forward_announcement(connector=self,
                                    observers=self.__observers,
                                    non_lazy_inputs=non_lazy_inputs,
                                    laziness=self._laziness)

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
        if not self.__announcements:
            self.__computable.set()
        if self._laziness == common.Laziness.ON_NOTIFY:
            await self._request(executor)

    def _cancel(self, connector):
        """Notifies this input connector, that an announced value change is not
        going to happen.

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

        :param executor: the :class:`Executor` instance, that manages the current computations
        """
        if not self.__running:
            self.__running = True
            try:
                # wait for the announced value changes
                if self.__announcements:
                    await asyncio.wait([a._request(executor) for a in self.__announcements])
                    await self.__computable.wait(executor)
                # execute the setter
                if self.__notifications:
                    for output_connector in self.__notifications:
                        data_id = self._connections[output_connector]
                        value = self.__notifications[output_connector]
                        if data_id is None:
                            self._connections[output_connector] = await executor.run_method(self._parallelization,
                                                                                            self._method,
                                                                                            self._instance(),
                                                                                            value)
                        else:
                            await executor.run_method(self._parallelization, self.__replace,
                                                      self._instance(), data_id, value)
                        self._conditional_observer_notification(data_id, value)
                        self._add_to_notification_condition_checks(data_id, value)
                    self.__notifications.clear()
                    if self._check_notification_condition():
                        for o in self.__observers:
                            o._notify(self)
            finally:
                self.__running = False

    def _conditional_observer_notification(self, data_id, *args, **kwargs):   # pylint: disable=unused-argument; this method has to be compatible with other input connectors
        """Notifies the observing output connectors, that this input has changed
        the instance's state.

        This method can be overridden by derived classes, for example to implement
        a conditional notification of the outputs.

        :param *args, **kwargs: the parameters, with which the replaced setter
                                method has been called (excluding ``self``)
        """
        for o in self.__observers:
            o._notify(self)

    def _add_to_notification_condition_checks(self, data_id, value):
        """A protected helper method to determine, if the observing output connectors
        have to be notified at the end of the :meth:`~connectors.MultiInputConnector._request`
        method.

        This method is meant to be overridden in derived classes, that implement
        a conditional notification of the observing output connectors.
        """
        pass

    def _check_notification_condition(self):   # pylint: disable=no-self-use; this method is a hook for derived classes
        """A protected helper method to determine, if the observing output connectors
        have to be notified at the end of the :meth:`~connectors.MultiInputConnector._request`
        method.

        This method is meant to be overridden in derived classes, that implement
        a conditional notification of the observing output connectors.
        """
        return True


class ConditionalMultiInputConnector(MultiInputConnector):
    """A variant of the :class:`~connectors.MultiInputConnector`, in which it
    depends on externally defined conditions, if the value changes are announced
    to the observing output connectors, and if the output connectors are notified
    about value changes.

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
        :param executor: an :class:`Executor` instance, that can be created with the
                         :func:`connectors.executor` function. See the :meth:`set_executor`
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
        :param non_lazy_inputs: a NonLazyInputs instance to which input connectors
                                can be appended, if they request an immediate
                                re-computation (see the InputConnector's
                                :meth:`set_laziness` method for more about lazy execution)
        """
        if self.__announce_condition(self._instance(), self._connections[connector]):
            super()._announce(connector, non_lazy_inputs)

    def _conditional_observer_notification(self, data_id, *args, **kwargs):
        """Notifies the observing output connectors, that this input has changed
        the instance's state.

        This method can be overridden by derived classes, for example to implement
        a conditional notification of the outputs.

        :param *args, **kwargs: the parameters, with which the replaced setter
                                method has been called (excluding ``self``)
        """
        value = common.get_first_argument(self._method, *args, **kwargs)
        if self.__notify_condition(self._instance(), data_id, value):
            super()._conditional_observer_notification(data_id, value)
        else:
            super()._cancel(None)

    def _add_to_notification_condition_checks(self, data_id, value):
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
