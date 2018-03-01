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

"""Contains the SingleInputProxy class"""

from ..connectors import SingleInputConnector
from .._lib import Laziness, NonLazyInputs
from ._baseclasses import ConnectorProxy

__all__ = ("SingleInputProxy",)


class SingleInputProxy(ConnectorProxy):
    """A proxy class for input connectors.
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
    def __init__(self, instance, method, observers, laziness, parallelization, executor):
        """
        :param instance: the instance in which the method is replaced by this connector proxy
        :param method: the unbound method that is replaced by this connector proxy
        :param observers: the names of output methods that are affected by passing a value to this connector proxy
        :param laziness: a flag from the :class:`connectors.Laziness` enum. See
                         the :meth:`set_laziness` method for details
        :param parallelization: a flag from the :class:`connectors.Parallelization` enum.
                                See the :meth:`set_parallelization` method for details
        :param executor: an :class:`Executor` instance, that can be created with the
                         :func:`connectors.executor` function. See the :meth:`set_executor`
                         method for details
        """
        ConnectorProxy.__init__(self, instance, method, parallelization, executor)
        self._observers = observers
        self._laziness = laziness

    def __call__(self, *args, **kwargs):
        """Executes the replaced method and notifies the observing output connectors.
        :param *args, **kwargs: possible arguments for the replaced method
        """
        result = ConnectorProxy.__call__(self, *args, **kwargs)
        instance = self._get_instance()
        non_lazy_inputs = NonLazyInputs(Laziness.ON_ANNOUNCE)
        for o in self._observers:
            getattr(instance, o)._notify(self, non_lazy_inputs)
        non_lazy_inputs.execute(self._executor)
        return result

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
        self._get_connector().set_laziness(laziness)

    def _connect(self, connector):
        """A method for connecting another connector to this connector.
        Calling this method causes the actual connector, that is represented by
        this proxy, to be created and the method to be replaced. This proxy is no
        longer used after this.
        This method is meant to be used internally in the *Connectors* package.
        :param connector: the connector to which this connector shall be connected
        """
        return self._get_connector()._connect(connector)

    def _create_connector(self, instance, method, parallelization, executor):
        """Creates and returns the input connector.
        :param instance: the instance in which the method is replaced by the connector
        :param method: the unbound method that is replaced by the connector
        :param parallelization: a flag from the :class:`connectors.Parallelization` enum.
                                See the :meth:`set_parallelization` method for details
        :param executor: an :class:`Executor` instance, that can be created with the
                         :func:`connectors.executor` function. See the :meth:`set_executor`
                         method for details
        :returns: an :class:`SingleInputConnector` instance
        """
        return SingleInputConnector(instance=instance,
                                    method=method,
                                    observers=self._observers,
                                    laziness=self._laziness,
                                    parallelization=parallelization,
                                    executor=executor)
