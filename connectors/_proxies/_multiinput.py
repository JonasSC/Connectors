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

"""Contains classes for the multi-input proxies"""

from .. import _connectors as connectors
from .. import _common as common
from ._input import SingleInputProxy

__all__ = ("MultiInputProxy",)


class ReplaceMethod:
    """Mimics a replace method by removing the old value and adding the new one.
    Instances of this class will be created, when no replace method is specified
    for a multi-input connector.
    """

    def __init__(self, add_method, remove_method):
        """
        :param method: the unbound method, that is replaced by the multi-input connector
        :param remove_method: the unbound method, that is used to remove data, that
                              has been added through the multi-input connector
        """
        self.__add = add_method
        self.__remove = remove_method

    def __call__(self, instance, data_id, value):
        """
        :param instance: the instance in which the method has been replaced by the multi-input connector
        :param data_id: the ID under which the data, that shall be replaced, has been stored
        :param value: the new value
        :returns: the new data ID, under which the new data is stored
        """
        self.__remove(instance, data_id)
        return self.__add(instance, value)


class MultiInputProxy(SingleInputProxy):
    """A proxy class for multi-input connectors.
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

    def __init__(self, instance, method,                            # pylint: disable=too-many-arguments; this constructor may be complicated, since the class is instantiated through the decorators, which have a much simpler API
                 remove_method, replace_method,
                 observers, announce_condition, notify_condition,
                 laziness, parallelization, executor):
        """
        :param instance: the instance in which the method is replaced by this connector proxy
        :param method: the unbound method, that is replaced by this connector proxy
        :param remove_method: an unbound method, that is used to remove data, that
                              has been added through this connector proxy
        :param replace_method: an unbound method, that is used to replace data,
                               that has been added through this connector proxy
        :param observers: the names of output methods that are affected by passing
                          a value to this connector proxy
        :param announce_condition: a method, that defines the condition for the
                                   announcements to the observing output connectors.
                                   This method must accept the data ID of the changed
                                   output connector as an argument in addition to
                                   ``self``
        :param notify_condition: a method, that defines the condition for the
                                 notifications to the observing output connectors.
                                 This method must accept the data ID and the new
                                 input value as an argument in addition to ``self``
        :param laziness: a flag from the :class:`connectors.Laziness` enum. See the
                         :meth:`set_laziness` method for details
        :param parallelization: a flag from the :class:`connectors.Parallelization` enum.
                                See the :meth:`set_parallelization` method for details
        :param executor: an :class:`~connectors._common._executors.Executor` instance,
                         that can be created with the :func:`connectors.executor`
                         function. See the :class:`~connectors.connectors.MultiInputConnector`'s
                         :meth:`~connectors.connectors.MultiInputConnector.set_executor`
                         method for details
        """
        SingleInputProxy.__init__(self,
                                  instance=instance,
                                  method=method,
                                  observers=observers,
                                  announce_condition=announce_condition,
                                  notify_condition=notify_condition,
                                  laziness=laziness,
                                  parallelization=parallelization,
                                  executor=executor)
        self.__remove = remove_method
        if replace_method is None:
            self.__replace = ReplaceMethod(add_method=method, remove_method=remove_method)
        else:
            self.__replace = replace_method

    def __getitem__(self, key):
        """Allows to use a multi-input connector as multiple single-input connectors.

        The key, under which a virtual single-input connector is accessed, shall
        also be returned the data ID, under which the result of the connected
        output is stored.

        :param key: a key for accessing a particular virtual single-input connector
        :returns: a :class:`~connectors._common._multiinput_item.MultiInputItem`, which enhances
                  the decorated method with the functionality of the virtual
                  single-input connector
        """
        for o in self._observers:
            if isinstance(getattr(self._get_instance(), o), connectors.Connector):
                return self._get_connector()[key]
        return common.MultiInputItem(connector=self,
                                     instance=self._get_instance(),
                                     replace_method=self.__replace,
                                     key=key,
                                     observers=(),
                                     executor=self._executor)

    def _create_connector(self, instance, method, parallelization, executor):
        """Creates and returns the multi-input connector.

        :param instance: the instance in which the method is replaced by the connector
        :param method: the unbound method that is replaced by the connector
        :param parallelization: a flag from the :class:`connectors.Parallelization` enum.
                                See the :meth:`set_parallelization` method for details
        :param executor: an :class:`~connectors._common._executors.Executor` instance,
                         that can be created with the :func:`connectors.executor`
                         function. See the :class:`~connectors.connectors.MultiInputConnector`'s
                         :meth:`~connectors.connectors.MultiInputConnector.set_executor`
                         method for details
        :returns: an :class:`MultiInputConnector` instance
        """
        if self._announce_condition is None and self._notify_condition is None:
            return connectors.MultiInputConnector(instance=instance,
                                                  method=method,
                                                  remove_method=self.__remove,
                                                  replace_method=self.__replace,
                                                  observers=self._observers,
                                                  laziness=self._laziness,
                                                  parallelization=parallelization,
                                                  executor=executor)
        else:
            announce_condition, notify_condition = common.select_condition_methods(self._announce_condition,
                                                                                   self._notify_condition)
            return connectors.ConditionalMultiInputConnector(instance=instance,
                                                             method=method,
                                                             remove_method=self.__remove,
                                                             replace_method=self.__replace,
                                                             observers=self._observers,
                                                             announce_condition=announce_condition,
                                                             notify_condition=notify_condition,
                                                             laziness=self._laziness,
                                                             parallelization=parallelization,
                                                             executor=executor)
