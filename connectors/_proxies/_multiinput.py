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

"""Contains classes for the multi-input proxies"""

from ..connectors import MultiInputConnector
from .._lib import Laziness, NonLazyInputs
from ._input import SingleInputProxy

__all__ = ("MultiInputProxy", "MultiInputAssociateProxy")


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
    def __init__(self, instance, method, remove_method, replace_method, observers, laziness, parallelization, executor):
        """
        :param instance: the instance in which the method is replaced by this connector proxy
        :param method: the unbound method, that is replaced by this connector proxy
        :param remove_method: an unbound method, that is used to remove data, that
                              has been added through this connector proxy
        :param replace_method: an unbound method, that is used to replace data,
                               that has been added through this connector proxy
        :param observers: the names of output methods that are affected by passing
                          a value to this connector proxy
        :param laziness: a flag from the :class:`connectors.Laziness` enum. See the
                         :meth:`set_laziness` method for details
        :param parallelization: a flag from the :class:`connectors.Parallelization` enum.
                                See the :meth:`set_parallelization` method for details
        :param executor: an :class:`Executor` instance, that can be created with the
                         :func:`connectors.executor` function. See the :meth:`set_executor`
                         method for details
        """
        SingleInputProxy.__init__(self, instance, method, observers, laziness, parallelization, executor)
        self.__remove = remove_method
        if replace_method is None:
            self.__replace = ReplaceMethod(add_method=method, remove_method=remove_method)
        else:
            self.__replace = replace_method

    def _create_connector(self, instance, method, parallelization, executor):
        """Creates and returns the multi-input connector.
        :param instance: the instance in which the method is replaced by the connector
        :param method: the unbound method that is replaced by the connector
        :param parallelization: a flag from the :class:`connectors.Parallelization` enum.
                                See the :meth:`set_parallelization` method for details
        :param executor: an :class:`Executor` instance, that can be created with the
                         :func:`connectors.executor` function. See the :meth:`set_executor`
                         method for details
        :returns: an :class:`MultiInputConnector` instance
        """
        return MultiInputConnector(instance=instance,
                                   method=method,
                                   remove_method=self.__remove,
                                   replace_method=self.__replace,
                                   observers=self._observers,
                                   laziness=self._laziness,
                                   parallelization=parallelization,
                                   executor=executor)


class MultiInputAssociateProxy:
    """A proxy class for remove or replace methods of multi-input connectors.
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
    def __init__(self, instance, method, observers, executor):
        """
        :param instance: the instance in which the method is replaced by the multi-input connector proxy
        :param method: the unbound method, that is replaced by this proxy (the remove or replace method)
        :param observers: the names of output methods that are affected by passing
                          a value to the multi-input connector proxy
        :param executor: an :class:`Executor` instance, that can be created with the
                         :func:`connectors.executor` function. See the :meth:`set_executor`
                         method for details
        """
        self.__instance = instance
        self.__method = method
        self.__observers = observers
        self.__executor = executor

    def __call__(self, *args, **kwargs):
        """Executes the replaced method and notifies the observing output connectors.
        :param *args, **kwargs: possible arguments for the replaced method
        """
        result = self.__method(self.__instance, *args, **kwargs)
        instance = self.__instance
        non_lazy_inputs = NonLazyInputs(Laziness.ON_ANNOUNCE)
        for o in self.__observers:
            getattr(instance, o)._notify(self, non_lazy_inputs)
        non_lazy_inputs.execute(self.__executor)
        return result
