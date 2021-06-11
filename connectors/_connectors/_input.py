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

"""Contains the SingleInputConnector class"""

from .. import _common as common
from ._baseclasses import InputConnector

__all__ = ("SingleInputConnector", "ConditionalSingleInputConnector")


class SingleInputConnector(InputConnector):
    """A connector-class that replaces setter methods, so they can be used to connect
    different objects in a processing chain."""

    def __init__(self, instance, method, observers, laziness, parallelization, executor):
        """
        :param instance: the instance of which the method is replaced by this connector
        :param method: the unbound method, that is replaced by this connector
        :param observers: the names of output methods that are affected by passing a value to this connector
        :param laziness: a flag from the :class:`connectors.Laziness` enum. See
                         the :meth:`~connectors.connectors.SingleInputConnector.set_laziness`
                         method for details
        :param parallelization: a flag from the :class:`connectors.Parallelization` enum.
                                See the :meth:`~connectors.connectors.SingleInputConnector.set_parallelization`
                                method for details
        :param executor: an :class:`~connectors._common._executors.Executor` instance,
                         that can be created with the :func:`connectors.executor`
                         function. See the :meth:`~connectors.connectors.SingleInputConnector.set_executor`
                         method for details
        """
        InputConnector.__init__(self, instance, method, laziness, parallelization, executor)
        self.__observers = common.resolve_observers(instance=instance, observers=observers)
        self.__announcement = None
        self.__notification = None
        self.__notification_is_valid = False
        self.__running = False              # is used to prevent, that the setter is executed multiple times for the same changes
        self.__computable = common.Event()  # is set, when there is no pending announcement
        self.__computable.set()

    def __call__(self, *args, **kwargs):
        """By making the object callable, it mimics the replaced method.
        This method also notifies the output method that are affected by this call (observers).

        :param `*args,**kwargs`: parameters with which the replaced method shall be called
        :returns: the return value of the replaced method
        """
        # announce the value change
        non_lazy_inputs = common.NonLazyInputs(common.Laziness.ON_ANNOUNCE)
        for o in self.__observers:
            o._announce(self, non_lazy_inputs)
        # call the replaced method
        result = self._method(self._instance(), *args, **kwargs)
        self.__announcement = None
        self.__notification = None
        self.__notification_is_valid = False
        # notify observers about the value change
        self._conditional_observer_notification(*args, **kwargs)
        # execute the non-lazy inputs
        non_lazy_inputs.execute(self._executor)
        # return the result of the method call
        return result

    def _connect(self, connector):
        """This method is called from an :class:`~connectors.connectors.OutputConnector`,
        when it is  being connected to this :class:`~connectors.connectors.SingleInputConnector`.

        :param connector: the :class:`~connectors.connectors.OutputConnector` instance
                          to which this connector shall be connected
        :returns: yields ``self`` (see the :class:`~connectors.connectors.MacroInputConnector`,
                  where :meth:`~connectors.connectors.MacroInputConnector._connect`
                  yields all the :class:`~connectors.connectors.SingleInputConnector`
                  instances that it exports)
        """
        yield self
        non_lazy_inputs = common.NonLazyInputs(situation=common.Laziness.ON_CONNECT)
        self._announce(connector, non_lazy_inputs=non_lazy_inputs)
        non_lazy_inputs.execute(self._executor)

    def _disconnect(self, connector):   # pylint: disable=unused-argument; this method has to be compatible with other input connectors
        """This method is called from an :class:`~connectors.OutputConnector`,
        when it is  being disconnected from this :class:`~connectors.SingleInputConnector`.

        :param connector: the output connector from which this connector shall be disconnected
        :returns: yields self (see the :class:`~connectors.MacroInputConnector`,
                  where :meth:`~connectors.MacroInputConnector._disconnect` yields
                  all the :class:`~connectors.SingleInputConnector`s that it exports)
        """
        self._executor.run_coroutine(self._request(self._executor))
        yield self

    def _announce(self, connector, non_lazy_inputs):
        """This method is to inform this input connector, when a connected output
        connector can produce updated data.

        :param connector: the output connector whose value is about to change
        :param non_lazy_inputs: a :class:`~connectors._common._non_lazy_inputs.NonLazyInputs`
                                instance to which input connectors can be appended,
                                if they request an immediate re-computation (see
                                the :meth:`~connectors.connectors.SingleInputConnector.set_laziness`
                                method for more about lazy execution)
        """
        self.__announcement = connector
        self.__notification = None
        self.__notification_is_valid = False
        self.__computable.clear()
        common.forward_announcement(connector=self,
                                    observers=self.__observers,
                                    non_lazy_inputs=non_lazy_inputs,
                                    laziness=self._laziness)

    async def _notify(self, connector, value, executor):    # pylint: disable=unused-argument; this method has to be compatible with other input connectors
        """This method is to notify this input connector, when a connected output
        connector has produced updated data.

        :param connector: the output connector whose value has changed
        :param value: the updated data from the output connector
        :param executor: the :class:`~connectors._common._executors.Executor`
                         instance, which managed the computation of the output
                         connector, and which shall be used for the computation
                         of this connector, in case it is not lazy.
        """
        self.__notification = value
        self.__notification_is_valid = True
        self.__announcement = None
        self.__computable.set()
        if self._laziness == common.Laziness.ON_NOTIFY:
            await self._request(executor)

    def _cancel(self, connector):   # pylint: disable=unused-argument; this method has to be compatible with other input connectors
        """Notifies this input connector, that an announced value change is not
        going to happen.

        :param connector: the output connector whose value change is canceled
        """
        self.__announcement = None
        self.__computable.set()
        for o in self.__observers:
            o._cancel(self)     # pylint: disable=protected-access; the _cancel method is meant to be called from other connectors, but not from outside this package

    async def _request(self, executor):
        """This method retrieves the updated data from the connected output connector
        and recomputes this connector (if necessary).
        It is called by the output connectors, that are affected by this connector,
        (observers) when their values have to be computed.

        :param executor: the :class:`~connectors._common._executors.Executor`
                         instance, that manages the current computations
        """
        if not self.__running:
            self.__running = True
            try:
                # wait for the announced value change
                if self.__announcement is not None:
                    await self.__announcement._request(executor)
                    await self.__computable.wait(executor)
                # execute the setter
                if self.__notification_is_valid:
                    notification = self.__notification
                    await executor.run_method(self._parallelization, self._method, self._instance(), notification)
                    self.__notification_is_valid = False
                    self.__notification = None
                    # notify the observers
                    self._conditional_observer_notification(notification)
            finally:
                self.__running = False

    def _conditional_observer_notification(self, *args, **kwargs):  # pylint: disable=unused-argument; this method has to be compatible with other input connectors
        """Notifies the observing output connectors, that this input has changed
        the instance's state.

        This method can be overridden by derived classes, for example to implement
        a conditional notification of the outputs.

        :param `*args,**kwargs`: the parameters, with which the replaced setter
                                method has been called (excluding ``self``)
        """
        for o in self.__observers:
            o._notify(self)


class ConditionalSingleInputConnector(SingleInputConnector):
    """A variant of the :class:`~connectors.SingleInputConnector`, in which it
    depends on externally defined conditions, if the value changes are announced
    to the observing output connectors, and if the output connectors are notified
    about value changes.

    The conditions are defined as methods, which are called before sending an
    announcement or a notification to the observing output connectors and which
    shall return a Boolean, that is True, if the output connector shall be informed,
    about the (expected) value change, or False, if the output shall be sent a
    cancellation notice.
    """

    def __init__(self, instance, method, observers,
                 announce_condition, notify_condition,
                 laziness, parallelization, executor):
        """
        :param instance: the instance of which the method is replaced by this connector
        :param method: the unbound method, that is replaced by this connector
        :param observers: the names of output methods that are affected by passing a value to this connector
        :param announce_condition: a method, that defines the condition for the
                                   announcements to the observing output connectors.
                                   This method must not require any arguments apart
                                   from ``self``
        :param notify_condition: a method, that defines the condition for the
                                 notifications to the observing output connectors.
                                 This method must accept the new input value as
                                 an argument in addition to ``self``
        :param laziness: a flag from the :class:`connectors.Laziness` enum. See
                         the :meth:`set_laziness` method for details
        :param parallelization: a flag from the :class:`connectors.Parallelization` enum.
                                See the :meth:`set_parallelization` method for details
        :param executor: an :class:`~connectors._common._executors.Executor` instance,
                         that can be created with the :func:`connectors.executor`
                         function. See the :meth:`~connectors.connectors.SingleInputConnector.set_executor`
                         method for details
        """
        SingleInputConnector.__init__(self, instance, method, observers, laziness, parallelization, executor)
        self.__announce_condition = announce_condition
        self.__notify_condition = notify_condition

    def _announce(self, connector, non_lazy_inputs):
        """This method is to inform this input connector, when a connected output
        connector can produce updated data.

        :param connector: the output connector whose value is about to change
        :param non_lazy_inputs: a :class:`~connectors._common._non_lazy_inputs.NonLazyInputs`
                                instance to which input connectors can be appended,
                                if they request an immediate re-computation (see
                                the :meth:`~connectors.connectors.SingleInputConnector.set_laziness`
                                method for more about lazy execution)
        """
        if self.__announce_condition(self._instance()):
            super()._announce(connector, non_lazy_inputs)

    def _conditional_observer_notification(self, *args, **kwargs):
        """Notifies the observing output connectors, that this input has changed
        the instance's state, if the condition is met.

        :param `*args,**kwargs`: the parameters, with which the replaced setter
                                method has been called (excluding **self**)
        """
        value = common.get_first_argument(self._method, *args, **kwargs)
        if self.__notify_condition(self._instance(), value):
            super()._conditional_observer_notification(value)
        else:
            super()._cancel(None)
