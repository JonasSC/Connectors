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

"""Contains the :class:`~connectors.MultiOutput` class for decorating getter methods with an input parameter."""

from .._common import Parallelization
from .._proxies import MultiOutputProxy
from ._baseclasses import ConnectorDecorator, default_executor

__all__ = ("MultiOutput",)


def no_keys(self):  # pylint: disable=unused-argument; the self-parameter is needed to simulate an unbound method
    """This function is used for multi-output connectors, for which no keys method
    has been specified. It always returns an empty set.
    """
    return set()


class MultiOutput(ConnectorDecorator):
    """A decorator, that marks a method as an multi-output connector.
    These connections can be used to automatically update a processing chain
    when a value has changed.
    The decorated method must take one argument.

    Multi-output connectors can either be used to route a dynamic number of values
    to a multi-input connector. Or the argument for the ``[]``-operator can be used
    to parameterize the getter method.
    """

    def __init__(self,
                 caching=True,
                 parallelization=Parallelization.default_multioutput_parallelization(),
                 executor=default_executor):
        """
        :param caching: True, if caching shall be enabled, False otherwise. See
                        the :class:`~connectors.connectors.MultiOutputConnector`'s
                        :meth:`~connectors.connectors.MultiOutputConnector.set_caching`
                        method for details
        :param parallelization: a flag from the :class:`connectors.Parallelization` enum.
                                See the :class:`~connectors.connectors.MultiOutputConnector`'s
                                :meth:`~connectors.connectors.MultiOutputConnector.set_parallelization`
                                method for details
        :param executor: an :class:`~connectors._common._executors.Executor` instance,
                         that can be created with the :func:`connectors.executor`
                         function. See the :class:`~connectors.connectors.MultiOutputConnector`'s
                         :meth:`~connectors.connectors.MultiOutputConnector.set_executor`
                         method for details
        """
        ConnectorDecorator.__init__(self, parallelization, executor)
        self.__caching = caching
        self.__keys = no_keys

    def __get__(self, instance, instance_type):
        """Is called, when the decorated method is accessed.

        :param instance: the instance of which a method shall be replaced
        :param instance_type: the type of the instance
        :returns: a :class:`~connectors.proxies.MultiOutputProxy` instance, that
                  mimics the decorated method and adds the connector functionality
        """
        return MultiOutputProxy(instance=instance,
                                method=self._method,
                                caching=self.__caching,
                                parallelization=self._parallelization,
                                executor=self._executor,
                                keys=self.__keys)

    def keys(self, method):
        """A decorator for the keys-method of the multi-output.
        The decorated method shall return the keys for which this multi-output
        can compute values. These keys may be returned in an iterable, that supports
        only one iteration, like the :meth:`dict.keys` method. Also, the decorated
        method may be a generator.

        This allows a multi-output connector to be connected to a multi-input
        connector, while determining automatically, for which keys the values
        are passed through the connection.

        :param method: the unbound keys-method
        :returns: the given keys-method without any modifications
        """
        self.__keys = method
        return method
