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

"""Base classes for the connector classes"""

import weakref
from .._lib import Laziness, NonLazyInputs

__all__ = ("Connector", "InputConnector")


class Connector:
    """Base class for connectors.
    Connectors are objects that replace methods of a class so that they can be
    connected to each other. This way changing data at one end of a connection
    chain will automatically cause the data at the other end of the chain to be
    updated, when that data is retrieved the next time.
    """
    def __init__(self, instance, method, parallelization, executor):
        """
        :param instance: the instance in which the method is replaced by this connector
        :param method: the unbound method that is replaced by this connector
        :param parallelization: a flag from the :class:`connectors.Parallelization` enum.
                                See the :meth:`set_parallelization` method for details
        :param executor: an :class:`Executor` instance, that can be created with the
                         :func:`connectors.executor` function. See the :meth:`set_executor`
                         method for details
        """
        self.__doc__ = method.__doc__           # This way the docstring of the decorated method remains the same
        self._instance = weakref.ref(instance)  # the weak reference avoids reference counting errors due to circular references
        self._method = method
        self._parallelization = parallelization
        self._executor = executor

    def __call__(self, *args, **kwargs):
        """By making the object callable, it mimics the replaced method.
        This is a virtual method which shall be overridden so it calls the
        replaced method in the expected manner.

        :param *args, **kwargs: arguments for the replaced method
        """
        raise NotImplementedError("This method should have been implemented in a derived class")

    def connect(self, connector):
        """Abstract method that defines the interface of a :class:`Connector` for
        connecting it with other connectors.

        :param connector: the :class:`Connector` instance to which this connector shall be connected
        :returns: the instance of which this :class:`Connector` has replaced a method
        """
        raise NotImplementedError("This method should have been implemented in a derived class")

    def disconnect(self, connector):
        """Abstract method that defines the interface of a :class:`Connector` for
        disconnecting it from a connector, to which it is currently connected.

        :param connector: a :class:`Connector` instance from which this connector shall be disconnected
        :returns: the instance of which this :class:`Connector` has replaced a method
        """
        raise NotImplementedError("This method should have been implemented in a derived class")

    def set_parallelization(self, parallelization):
        """Specifies, if and how the execution of this connector can be parallelized.
        The choices are no parallelization, the execution in a separate thread
        and the execution in a separate process.
        This method specifies a hint, which level of parallelization is possible
        with the connector. If the executor of the connector, through which the
        computation is started, does not support the specified level, the next simpler
        one will be chosen. E.g. if a connector can be parallelized in a separate
        process, but the executor only allows threads or sequential execution, the
        connector will be executed in a separate thread.

        :param parallelization: a flag from the :class:`connectors.Parallelization` enum
        """
        self._parallelization = parallelization

    def set_executor(self, executor):
        """Sets the executor, which handles the computations, when the data is
        retrieved through this connector.
        An executor can be created with the :func:`connectors.executor` function. It
        manages the order and the parallelization of the computations, when updating
        the data in a processing chain.
        If multiple connectors in a processing chain need to be computed, the
        executor of the connector, which started the computations, is used for
        all computations.

        :param executor: an :class:`Executor` instance, that can be created with
                         the :func:`connectors.executor` function
        """
        self._executor = executor

    def _announce(self, connector, non_lazy_inputs):
        """This method is to notify other connectors in a processing chain,
        when a value is about to change.
        This way, this connector knows, that it has to retrieve new data from the
        given connector and recompute its own value, when that value is requested.

        :param connector: a connector on whose value change this connector's value depends
        :param non_lazy_inputs: a NonLazyInputs instance to which input connectors
                                can be appended, if they request an immediate
                                re-computation (see the InputConnector's
                                :meth:`set_laziness` method for more about lazy execution)
        """
        raise NotImplementedError("This method should have been implemented in a derived class")

    def _get_instance(self):
        """A method, that is used internally by the *Connectors* package to
        retrieve the object instance of which the connector has replaced a method.
        Even though the connectors store weak references to the instance, the return
        value of this method is a strong reference.

        :returns: a Python object
        """
        return self._instance()

    def _get_connector(self):
        """A method, that is used internally by the *Connectors* package for
        compatibility with :class:`ConnectorProxy` instances.
        In a :class:`ConnectorProxy`, this method creates the connector for the corresponding
        method, replaces that method with it and returns the connector. With this
        method, a Connector mimics this behavior, so it is not necessary to check,
        whether a method has already been replaced by its connector, or if it is
        still managed by a :class:`ConnectorProxy`.

        :returns: ``self``
        """
        return self


class InputConnector(Connector):
    """Base class for input connectors, that replace setter methods."""
    def __init__(self, instance, method, observers, laziness, parallelization, executor):
        """
        :param instance: the instance in which the method is replaced by this connector
        :param method: the unbound method that is replaced by this connector
        :param observers: the names of output methods that are affected by passing a value to this connector
        :param laziness: a flag from the :class:`connectors.Laziness` enum. See
                         the :meth:`set_laziness` method for details
        :param parallelization: a flag from the :class:`connectors.Parallelization` enum.
                                See the :meth:`set_parallelization` method for details
        :param executor: an :class:`Executor` instance, that can be created with the
                         :func:`connectors.executor` function. See the :meth:`set_executor`
                         method for details
        """
        Connector.__init__(self, instance, method, parallelization, executor)
        self._observers = []
        for o in observers:
            output_connector = getattr(self._instance(), o)
            self._observers.append(output_connector._get_connector())
        self._laziness = laziness

    def connect(self, connector):
        """Connects this :class:`InputConnector` to an output.

        :param connector: the :class:`Connector` instance to which this connector shall be connected
        :returns: the instance of which this :class:`InputConnector` has replaced a method
        """
        connector.connect(self)
        return self._instance()

    def disconnect(self, connector):
        """Disconnects this :class:`InputConnector` from an output, to which is has been connected.

        :param connector: a :class:`Connector` instance from which this connector shall be disconnected
        :returns: the instance of which this :class:`Connector` has replaced a method
        """
        connector.disconnect(self)
        return self._instance()

    def set_laziness(self, laziness):
        """Configures the lazy execution of the connector.
        Normally the connectors are executed lazily, which means, that any computation
        is only started, when the result of a processing chain is requested. For
        certain use cases it is necessary to disable this lazy execution, though,
        so that the values are updated immediately as soon as new data is available.
        There are different behaviors for the (non) lazy execution, which are
        described in the :class:`connectors.Laziness` enum.

        :param laziness: a flag from the :class:`connectors.Laziness` enum
        """
        self._laziness = laziness

    def _connect(self, connector):
        """This method is called from an :class:`OutputConnector`, when it is  being
        connected to this :class:`InputConnector`.

        :param connector: the :class:`OutputConnector` instance to which this connector shall be connected
        :returns: yields self (see the :class:`MacroInputConnector`, where :meth:`_connect`
                  yields all the :class:`InputConnector`s that it exports)
        """
        non_lazy_inputs = NonLazyInputs(situation=Laziness.ON_CONNECT)
        self._announce(connector, non_lazy_inputs=non_lazy_inputs)
        non_lazy_inputs.execute(self._executor)
        yield self

    def _disconnect(self, connector):
        """This method is called from an :class:`OutputConnector`, when it is  being
        disconnected from this :class:`InputConnector`.

        :param connector: a :class:`Connector` instance from which this connector shall be disconnected
        :returns: yields self (see the :class:`MacroInputConnector`, where :meth:`_connect`
                  yields all the :class:`InputConnector`s that it exports)
        """
        raise NotImplementedError("This method should have been implemented in a derived class")

    def _announce(self, connector, non_lazy_inputs):
        """Abstract method that defines the interface of an input connector to
        notify it, when a connected output connector can produce updated data.

        :param connector: the output connector whose value is about to change
        :param non_lazy_inputs: a NonLazyInputs instance to which input connectors
                                can be appended, if they request an immediate
                                re-computation (see the InputConnector's
                                :meth:`set_laziness` method for more about lazy execution)
        """
        initial_number_of_non_lazy_inputs = len(non_lazy_inputs)
        for o in self._observers:
            o._announce(self, non_lazy_inputs)
        if len(non_lazy_inputs) == initial_number_of_non_lazy_inputs:  # only add self, if no methods down the processing chain requests its execution anyway
            non_lazy_inputs.add(connector=self, laziness=self._laziness)

    async def _notify(self, connector, value, executor):
        """Abstract method that defines the interface of an input connector to
        notify it, when a connected output connector has produced updated data.

        :param connector: the output connector whose value has changed
        :param value: the updated data from the output connector
        :param executor: the :class:`Executor` instance, which managed the computation
                         of the output connector, and which shall be used for the
                         computation of this connector, in case it is not lazy.
        """
        raise NotImplementedError("this method should have been implemented in a derived class")

    async def _execute(self, executor):
        """Abstract method that defines the interface of an input connector for
        retrieving the updated data from the connected output connectors and
        recomputing itself (if necessary).
        It is called by the output connectors, that are affected by this connector,
        (observers) when their values have to be computed.

        :param executor: the :class:`Executor` instance, that manages the current computations
        """
        raise NotImplementedError("this method should have been implemented in a derived class")

    async def _announce_to_observers(self, executor):
        """Announces, that this input connector will receive a new value, to the
        observing output connectors.

        :param executor: the :class:`Executor` instance, that manages the current computations
        """
        non_lazy_inputs = NonLazyInputs(Laziness.ON_ANNOUNCE)
        for o in self._observers:
            o._notify(self, non_lazy_inputs)
        await non_lazy_inputs.execute_async(executor)

    def _notify_observers(self):
        """Notifies the observing output connectors, that the replaced setter method
        has been called.
        """
        non_lazy_inputs = NonLazyInputs(Laziness.ON_ANNOUNCE)
        for o in self._observers:
            o._notify(self, non_lazy_inputs)
        non_lazy_inputs.execute(self._executor)
