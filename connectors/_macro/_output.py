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

"""Contains the decorator and connector classes for the macro output connector."""

import functools
from ._baseclass import MacroDecorator

__all__ = ("MacroOutput",)


class MacroOutput(MacroDecorator):
    """A decorator to replace a method with a macro output connector.

    Macro connectors are useful, when a processing network shall be encapsulated
    in a class. In such a case, macro output connectors are used to export output
    connectors from the internal processing network to be accessible as connectors
    of the encapsulating class's instance.

    The decorated method must not take any parameters and return the output connector
    from the internal processing network, that it exports.

    The resulting connector will behave like an output connector, which is very
    different from the decorated method:

    - the connector takes no argument.
    - when called, the connector returns the result of the exported connector.
    """

    def __get__(self, instance, instance_type):
        """Is called, when the decorated method is accessed.

        :param instance: the instance of which a method shall be replaced
        :param instance_type: the type of the instance
        :returns: a :class:`MacroInputConnector` instance
        """
        return MacroOutputConnector(instance=instance, method=self._method)


class MacroOutputConnector:
    """A Connector-class that exports an output connector from an internal processing
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

    def __call__(self):
        """Calls the output connector, that is exported by this.

        :returns: the return value from the call
        """
        return self.__method(self.__instance)()

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
        self.__method(self.__instance).set_caching(caching)

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
        self.__method(self.__instance).set_parallelization(parallelization)

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
        self.__method(self.__instance).set_executor(executor)

    def connect(self, connector):
        """Connects the exported output connector to the given input.

        :param connector: the input connector to which the exported connector shall be connected
        :returns: the instance of which this connector has replaced a method
        """
        self.__method(self.__instance).connect(connector)
        return self.__instance

    def disconnect(self, connector):
        """Disconnects the exported output connector from the given input.

        :param connector: the input connector from which the exported connector shall be disconnected
        :returns: the instance of which this connector has replaced a method
        """
        self.__method(self.__instance).disconnect(connector)
        return self.__instance
