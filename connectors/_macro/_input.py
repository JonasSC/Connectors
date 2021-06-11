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

"""Contains the decorator and connector classes for the macro input connector."""

import functools
from ._baseclass import MacroDecorator

__all__ = ("MacroInput",)


class MacroInput(MacroDecorator):
    """A decorator to replace a method with a macro input connector.

    Macro connectors are useful, when a processing network shall be encapsulated
    in a class. In such a case, macro input connectors are used to export input
    connectors from the internal processing network to be accessible as connectors
    of the encapsulating class's instance.

    The decorated method must not take any parameters and yield all input connectors
    from the internal processing network, that it exports. Exporting multiple
    connectors through the same macro connector is possible and useful, when all
    of these connectors shall always receive the same input value.

    The resulting connector will behave like an input connector, which is very
    different from the decorated method:

    - the connector's arguments are passed to all the exported input connectors,
      when it is called.
    - when called, the connector returns the instance to which it belongs, so
      that changing a parameter and retrieving a result in one line is possible
    - when a behavior (e.g. laziness) of the connector is changed, the change
      is passed on to all the exported connectors.
    """

    def __get__(self, instance, instance_type):
        """Is called, when the decorated method is accessed.

        :param instance: the instance of which a method shall be replaced
        :param instance_type: the type of the instance
        :returns: a :class:`MacroInputConnector` instance
        """
        return MacroInputConnector(instance=instance, method=self._method)


class MacroInputConnector:
    """A Connector-class that exports input connectors from an internal processing
    network to the API of the class, that encapsulates the network.
    """

    def __init__(self, instance, method):
        """
        :param instance: the instance in which the method is replaced by this connector
        :param method: the unbound method, that is replaced by this connector
        """
        self.__instance = instance
        self.__method = method
        functools.update_wrapper(self, method)

    def __call__(self, *args, **kwargs):
        """Calls all input connectors, that are exported by this, with the given
        parameters.

        :param `*args,**kwargs`: parameters with which the exported input connectors shall be called
        :returns: the instance of which this connector has replaced a method
        """
        for connector in self.__method(self.__instance):
            connector(*args, **kwargs)
        return self.__instance

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
        for connector in self.__method(self.__instance):
            connector.set_laziness(laziness)

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
        for connector in self.__method(self.__instance):
            connector.set_parallelization(parallelization)

    def set_executor(self, executor):
        """Sets the executor, which handles the computations, when the data is
        retrieved through this connector.
        An executor can be created with the :func:`connectors.executor` function. It
        manages the order and the parallelization of the computations, when updating
        the data in a processing chain.
        If multiple connectors in a processing chain need to be computed, the
        executor of the connector, which started the computations, is used for
        all computations.

        :param executor: an :class:`~connectors._common._executors.Executor` instance,
                         that can be created with the :func:`connectors.executor`
                         function
        """
        for connector in self.__method(self.__instance):
            connector.set_executor(executor)

    def connect(self, connector):
        """Connects all exported input connectors to the given output.

        :param connector: the output connector to which the exported connectors shall be connected
        :returns: the instance of which this connector has replaced a method
        """
        connector.connect(self)
        return self.__instance

    def disconnect(self, connector):
        """Disconnects all exported input connectors from the given output.

        :param connector: the output connector from which the exported connectors shall be disconnected
        :returns: the instance of which this connector has replaced a method
        """
        connector.disconnect(self)
        return self.__instance

    def _connect(self, connector):
        """This method is called from an :class:`OutputConnector`, when it is  being
        connected to this :class:`MacroInputConnector`.

        :param connector: the :class:`OutputConnector` instance to which this connector shall be connected
        :returns: yields all the :class:`InputConnector`s that this exports
        """
        for c1 in self.__method(self.__instance):
            for c2 in c1._connect(connector):
                yield c2

    def _disconnect(self, connector):
        """This method is called from an :class:`OutputConnector`, when it is  being
        disconnected from this :class:`MacroInputConnector`.

        :param connector: the :class:`OutputConnector` instance from which this connector shall be disconnected
        :returns: yields all the :class:`InputConnector`s that this exports
        """
        for c1 in self.__method(self.__instance):
            for c2 in c1._disconnect(connector):
                yield c2
