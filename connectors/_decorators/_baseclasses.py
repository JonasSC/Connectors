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

"""Base classes for the connector decorators"""

from connectors import _common as lib

__all__ = ("ConnectorDecorator", "InputDecorator")

default_executor = lib.executor()   # this instance is for the default value of the connector decorator's constructors


class ConnectorDecorator:
    """An abstract base class for the decoration of methods so they can be used
    as connectors.
    """

    def __init__(self, parallelization, executor):
        """
        :param parallelization: a flag from the :class:`connectors.Parallelization` enum.
                                See the :class:`~connectors.connectors.Connector`'s
                                :meth:`~connectors.connectors.Connector.set_parallelization` method for details
        :param executor: an :class:`~connectors._common._executors.Executor` instance,
                         that can be created with the :func:`connectors.executor`
                         function. See the :class:`~connectors.connectors.Connector`'s
                         :meth:`~connectors.connectors.Connector.set_executor` method
                         for details
        """
        self._method = None     # Will be set in __call__
        self._parallelization = parallelization
        self._executor = executor

    def __call__(self, method):
        """Is called in order to replace the decorated method with this decorator.

        :param method: the unbound method, that was decorated with this decorator
        :returns: this decorator
        """
        self._method = method
        return self

    def __get__(self, instance, instance_type):
        """Is called, when the decorated method is accessed.

        :param instance: the instance of which a method shall be replaced
        :param instance_type: the type of the instance
        :returns: a :class:`connectors._proxies._baseclasses.ConnectorProxy` instance,
                  that mimics the decorated method and adds the connector functionality
        """
        raise NotImplementedError("This method should have been overridden in a derived class")


class InputDecorator(ConnectorDecorator):
    """An addition to a :class:`ConnectorDecorator` for input connectors that notify
    their instances' output connectors when an incoming value changes their result
    values.
    """
    # pylint: disable=abstract-method; pylint shall not complain, that the __get__-method is not overridden in InputDecorator

    def __init__(self,
                 observers=(),
                 laziness=lib.Laziness.default(),
                 parallelization=lib.Parallelization.default_input_parallelization(),
                 executor=default_executor):
        """
        :param observers: the names of output methods that are affected by passing
                          a value to this connector. For convenience it is also
                          possible to pass a string here, if only one output
                          connector depends on this input.
        :param laziness: a flag from the :class:`connectors.Laziness` enum. See the
                         :class:`~connectors.connectors.SingleInputConnector`'s
                         :meth:`~connectors.connectors.SingleInputConnector.set_laziness`
                         method for details
        :param parallelization: a flag from the :class:`connectors.Parallelization` enum.
                                See the :class:`~connectors.connectors.MultiInputConnector`'s
                                :meth:`~connectors.connectors.SingleInputConnector.set_parallelization`
                                method for details
        :param executor: an :class:`~connectors._common._executors.Executor` instance,
                         that can be created with the :func:`connectors.executor`
                         function. See the :class:`~connectors._connectors._baseclasses.InputConnector`'s
                         :meth:`~connectors._connectors._baseclasses.InputConnector.set_executor` method
                         for details
        """
        ConnectorDecorator.__init__(self, parallelization=parallelization, executor=executor)
        if isinstance(observers, str):
            self._observers = (observers,)
        else:
            self._observers = observers
        self._laziness = laziness
        self._announce_condition = None
        self._notify_condition = None

    def announce_condition(self, method):
        """A decorator, that can be used as a method of the connector method, to
        define a condition for the propagation of announcements through the
        input connector.

        The decorated method shall return ``True``, if the announcement shall be
        propagated and ``False``` otherwise. For normal input connectors, it shall
        not require any arguments, while for multi-input connectors, it must accept
        the data ID of the connection, through which the announcement was received.

        Before the values in a processing chain are updated, the value changes
        are announced to the downstream processors. Only if data is retrieved
        through an output connector, that has pending announcements, the actual
        value changes are requested from the upstream processors (lazy execution).
        If an input connector has defined a condition on the propagation of
        announcements and this condition evaluates to ``False``, the announcements
        are not forwarded to the downstream processors. This also prevents those
        processors from requesting updated values from upstream.

        The usage is described by the following example: if `A` is the name of
        the method, that is decorated with :class:`connectors.Input`
        or :class:`connectors.MultiInput`, the method for the condition has to be
        decorated with ``@A.announce_condition``.

        :param: the method, that defines the condition
        :returns: the same method
        """
        self._announce_condition = method
        return method

    def notify_condition(self, method):
        """A decorator, that can be used as a method of the connector method, to
        define a condition for notifying the observing output connectors about
        a value, that has been changed by this connector.

        The decorated method shall return ``True``, if the notification shall be
        sent and ``False`` otherwise. For normal input connectors, it shall accept
        the new value as an argument, while for multi-input connectors, it must
        accept the data ID of the connection, through which the announcement was
        received and the new value.

        This condition is checked after the input connector (the setter method)
        has been executed. If an input connector has defined a condition on the
        notification of its observing output connectors and this condition evaluates
        to ``False``, the output connectors are sent a cancel notification, that
        informs them, that the state of the object, to which the connectors belong,
        has not changed in a relevant way. This prevents the update of values
        further down the processing chain.

        The usage is described by the following example: if `A` is the name of
        the method, that is decorated with :class:`connectors.Input`
        or :class:`connectors.MultiInput`, the method for the condition has to be
        decorated with ``@A.notify_condition``.

        :param: the method, that defines the condition
        :returns: the same method
        """
        self._notify_condition = method
        return method
