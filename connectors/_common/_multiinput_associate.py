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

"""Contains supplementary classes for the implementation of the remove and replace
methods of multi-input connectors.
"""

import functools
from ._flags import Laziness
from ._non_lazy_inputs import NonLazyInputs

__all__ = ("MultiInputAssociateDescriptor", "MultiInputAssociateProxy",)


class MultiInputAssociateDescriptor:
    """A descriptor class for associating remove and replace methods with their
    multi-input.
    Instances of this class are created by the decorator methods :meth:`~connectors.MultiInput.remove`
    and :meth:`~connectors.MultiInput.replace`.
    """

    def __init__(self, method, observers, parallelization, executor):
        """
        :param method: the unbound method, that is wrapped
        :param observers: the names of output methods that are affected by passing
                          a value to the multi-input connector.
        :param parallelization: a flag from the :class:`connectors.Parallelization` enum.
                                See the :class:`~connectors.connectors.MultiInputConnector`'s
                                :meth:`~connectors.connectors.MultiInputConnector.set_parallelization`
                                method for details
        :param executor: an :class:`~connectors._common._executors.Executor` instance,
                         that can be created with the :func:`connectors.executor`
                         function. See the :class:`~connectors.connectors.MultiInputConnector`'s
                         :meth:`~connectors.connectors.MultiInputConnector.set_executor`
                         method for details
        """
        self.__method = method
        self.__observers = observers
        self.__parallelization = parallelization
        self.__executor = executor

    def __get__(self, instance, instance_type):
        """Is called, when the decorated method is accessed.

        :param instance: the instance of which a method shall be replaced
        :param instance_type: the type of the instance
        :returns: a :class:`connectors._common._multiinput_associate.MultiInputAssociateProxy`
                  instance, that mimics the decorated method and adds the connector
                  functionality
        """
        return MultiInputAssociateProxy(instance=instance,
                                        method=self.__method,
                                        observers=self.__observers,
                                        executor=self.__executor)


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
        :param executor: an :class:`~connectors._common._executors.Executor` instance,
                         that can be created with the :func:`connectors.executor`
                         function. See the :meth:`~connectors.connectors.MultiInputConnector.set_executor`
                         method for details
        """
        self.__instance = instance
        self.__method = method
        self.__observers = observers
        self.__executor = executor
        functools.update_wrapper(self, method)

    def __call__(self, *args, **kwargs):
        """Executes the replaced method and notifies the observing output connectors.
        :param `*args,**kwargs`: possible arguments for the replaced method
        :returns: the return value of the method, that has been replaced by this
        """
        instance = self.__instance
        # announce the value change
        non_lazy_inputs = NonLazyInputs(Laziness.ON_ANNOUNCE)
        for o in self.__observers:
            getattr(instance, o)._announce(self, non_lazy_inputs)
        # call the replaced method
        result = self.__method(self.__instance, *args, **kwargs)
        # notify observers about the value change
        for o in self.__observers:
            getattr(instance, o)._notify(self)
        # execute the non-lazy inputs
        non_lazy_inputs.execute(self.__executor)
        # return the result of the method call
        return result
