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

"""Contains :class:`ConnectorProxy`, the base class for connector proxies."""

import functools


class ConnectorProxy:
    """A base class for proxy objects of connectors.
    Connector proxies are returned by the connector decorators, while the methods
    are replaced by the actual connectors. Think of a connector proxy like of a
    bound method, which is also created freshly, whenever a method is accessed.
    The actual connector only has a weak reference to its instance, while this
    proxy has a hard reference, but mimics the connector in almost every other
    way. This makes constructions like ``value = Class().connector()`` possible.
    Without the proxy, the instance of the class would be deleted before the connector
    method is called, so that the weak reference of the connector would be expired
    during its call.
    """

    def __init__(self, instance, method, parallelization, executor):
        """
        :param instance: the instance in which the method is replaced by this connector proxy
        :param method: the unbound method that is replaced by this connector proxy
        :param parallelization: a flag from the :class:`connectors.Parallelization` enum.
                                See the :meth:`set_parallelization` method for details
        :param executor: an :class:`~connectors._common._executors.Executor` instance,
                         that can be created with the :func:`connectors.executor`
                         function. See the :meth:`~connectors._proxies._baseclasses.ConnectorProxy.set_executor`
                         method for details
        """
        self.__instance = instance
        self.__method = method
        self._parallelization = parallelization
        self._executor = executor
        self.__connector = None
        functools.update_wrapper(self, method)

    def __call__(self, *args, **kwargs):
        """By making the object callable, it mimics the replaced method.

        :param `*args,**kwargs`: possible arguments for the replaced method
        """
        return self.__method(self.__instance, *args, **kwargs)

    def connect(self, connector):
        """Connects this connector with another one.

        :param connector: the :class:`~connectors.connectors.Connector` instance
                          to which this connector shall be connected
        :returns: the instance of which this :class:`~connectors.connectors.Connector`
                  has replaced a method
        """
        return self._get_connector().connect(connector)

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
        self._get_connector().set_parallelization(parallelization)

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
        self._get_connector().set_executor(executor)

    def _get_instance(self):
        """A method, that is used internally by the *Connectors* package to retrieve
         the object instance of which the connector proxy has replaced a method.

        :returns: a Python object
        """
        return self.__instance

    def _get_connector(self):
        """Creates the actual connector, that is represented by this proxy, replaces
        the method with it and returns the connector. This proxy is no longer used
        after this.

        :returns: a Connector instance
        """
        self.__replace_method()
        return self.__connector

    def _create_connector(self, instance, method, parallelization, executor):
        """Abstract method, in which derived classes can implement the creation
        of their connectors.

        :param instance: the instance in which the method is replaced by the connector
        :param method: the unbound method that is replaced by the connector
        :param parallelization: a flag from the :class:`connectors.Parallelization` enum.
                                See the :meth:`set_parallelization` method for details
        :param executor: an :class:`~connectors._common._executors.Executor` instance,
                         that can be created with the :func:`connectors.executor`
                         function. See the :meth:`~connectors._proxies._baseclasses.ConnectorProxy.set_executor`
                         method for details
        :returns: a :class:`~connectors.connectors.Connector` instance
        """
        raise NotImplementedError("This method should have been implemented in a derived class")

    def __replace_method(self):
        """Replaces the method with the connector
        This proxy is no longer used after this.
        """
        if self.__connector is None:
            self.__connector = self._create_connector(instance=self.__instance,
                                                      method=self.__method,
                                                      parallelization=self._parallelization,
                                                      executor=self._executor)
            setattr(self.__instance, self.__method.__name__, self.__connector)
