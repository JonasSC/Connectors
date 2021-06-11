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

"""Contains the OutputProxy class"""

from .. import _connectors as connectors
from .. import _common as common
from ._baseclasses import ConnectorProxy

__all__ = ("MultiOutputProxy",)


class MultiOutputProxy(ConnectorProxy):
    """A proxy class for multi-output connectors, that replace getter methods,
    which accept one parameter, so they can be used as a multi-output connector,
    which can be connected to different objects.

    Multi-output connectors can either be used to route a dynamic number of values
    to a multi-input connector. Or the argument for the ``[]``-operator can be used
    to parameterize the getter method.

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

    def __init__(self, instance, method, caching, parallelization, executor, keys):
        """
        :param instance: the instance in which the method is replaced by this connector proxy
        :param method: the unbound method that is replaced by this connector proxy
        :param caching: True, if caching shall be enabled, False otherwise. See
                        the :meth:`set_caching` method for details
        :param parallelization: a flag from the :class:`connectors.Parallelization` enum.
                                See the :meth:`set_parallelization` method for details
        :param executor: an :class:`~connectors._common._executors.Executor` instance,
                         that can be created with the :func:`connectors.executor`
                         function. See the :class:`~connectors.connectors.OutputConnector`'s
                         :meth:`~connectors.connectors.OutputConnector.set_executor`
                         method for details
        """
        ConnectorProxy.__init__(self, instance, method, parallelization, executor)
        self.__caching = caching
        self.__keys = keys

    def __getitem__(self, key):
        """Allows to use a multi-output connector as multiple single-output connectors.

        :param key: a key for accessing a particular virtual single-output connector
        :returns: a :class:`connectors._common._multioutput_item.MultiOutputItem`,
                  which enhances the decorated method with the functionality of
                  the virtual single-output connector
        """
        return common.MultiOutputItem(connector=self, instance=self._get_instance(), key=key)

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
        self._get_connector().set_caching(caching)

    def _create_connector(self, instance, method, parallelization, executor):
        """Creates and returns the output connector.

        :param instance: the instance in which the method is replaced by the connector
        :param method: the unbound method that is replaced by the connector
        :param parallelization: a flag from the :class:`connectors.Parallelization` enum.
                                See the :meth:`set_parallelization` method for details
        :param executor: an :class:`~connectors._common._executors.Executor` instance,
                         that can be created with the :func:`connectors.executor`
                         function. See the :class:`~connectors.connectors.OutputConnector`'s
                         :meth:`~connectors.connectors.OutputConnector.set_executor`
                         method for details
        :returns: an :class:`~connectors.connectors.OutputConnector` instance
        """
        return connectors.MultiOutputConnector(instance=instance,
                                               method=method,
                                               caching=self.__caching,
                                               parallelization=parallelization,
                                               executor=executor,
                                               keys=self.__keys)

    def _connect(self, key, connector):
        """Connects a virtual single output to the given input connector.

        This method is called from a :class:`connectors._common._multioutput_item.MultiOutputItem`
        instance.

        :param item: the :class:`connectors._common._multioutput_item.MultiOutputItem`
                     instance, from which this method is called
        :param connector: the input connector to which the connection shall be established
        """
        return self._get_connector()._connect(key, connector)

    def _announce(self, connector, non_lazy_inputs):
        """This method is to notify this output connector, when an observed input
        connector (a setter from the instance to which this connector belongs)
        can retrieve updated data.

        :param connector: the input connector, which is about to change a value
        :param non_lazy_inputs: a :class:`~connectors._common._non_lazy_inputs.NonLazyInputs`
                                instance to which input connectors can be appended,
                                if they request an immediate re-computation (see
                                the :class:`~connectors._connectors._base_classes.InputConnector`'s
                                :meth:`~connectors._connectors._base_classes.InputConnector.set_laziness`
                                method for more about lazy execution)
        """
        # nothing to do for a proxy

    def _notify(self, connector):
        """This method is to notify this multi-output connector, when an observed
        input connector (a setter from the instance to which this connector belongs)
        has retrieved updated data.

        :param connector: the input connector, which has changed a value
        :param non_lazy_inputs: a :class:`~connectors._common._non_lazy_inputs.NonLazyInputs`
                                instance to which input connectors can be appended,
                                if they request an immediate re-computation (see
                                the :class:`~connectors._connectors._base_classes.InputConnector`'s
                                :meth:`~connectors._connectors._base_classes.InputConnector.set_laziness`
                                method for more about lazy execution)
        """
        # nothing to do for a proxy
