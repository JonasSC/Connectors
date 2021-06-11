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

"""Contains the :class:`MultiInput` class for decorating special setter methods, with
which multiple values can be added.
Also contains a descriptor class for the remove and replace methods of a multi-input.
"""

from .. import _common as common
from .._proxies import MultiInputProxy
from ._baseclasses import InputDecorator, default_executor

__all__ = ("MultiInput",)


class MultiInput(InputDecorator):
    """A decorator, that marks a method as an input for multiple connections.
    These connections can be used to automatically update a processing chain
    when a value has changed.

    The decorated method must take exactly one argument and return a unique id.
    For every MultiInput-method a remove method has to be provided, which removes
    a value, that has previously been added.

    A replace method can be provided optionally. This method is called, when the
    value of a connected output has changed, rather than removing the old value and
    adding the new.

    See the :meth:`~connectors.MultiInput.remove` and :meth:`~connectors.MultiInput.replace`
    methods for documentation about how to define these methods for a multi-input connector.
    """

    def __init__(self,
                 observers=(),
                 laziness=common.Laziness.default(),
                 parallelization=common.Parallelization.default_multiinput_parallelization(),
                 executor=default_executor):
        """
        :param observers: the names of output methods that are affected by passing
                          a value to this connector. For convenience it is also
                          possible to pass a string here, if only one output
                          connector depends on this input.
        :param laziness: a flag from the :class:`connectors.Laziness` enum. See the
                         :class:`~connectors.connectors.MultiInputConnector`'s
                         :meth:`~connectors.connectors.MultiInputConnector.set_laziness`
                         method for details
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
        InputDecorator.__init__(self,
                                observers=observers,
                                laziness=laziness,
                                parallelization=parallelization,
                                executor=executor)
        self.__remove_method = None
        self.__replace_method = None

    def __get__(self, instance, instance_type):
        """Is called, when the decorated method is accessed.

        :param instance: the instance of which a method shall be replaced
        :param instance_type: the type of the instance
        :returns: a :class:`MultiInputProxy` instance, that mimics the decorated
                  method and adds the connector functionality
        """
        return MultiInputProxy(instance=instance,
                               method=self._method,
                               remove_method=self.__remove_method,
                               replace_method=self.__replace_method,
                               observers=self._observers,
                               announce_condition=self._announce_condition,
                               notify_condition=self._notify_condition,
                               laziness=self._laziness,
                               parallelization=self._parallelization,
                               executor=self._executor)

    def remove(self, method):
        """A method of the decorated method to decorate the remove method, with
        which data, that has been added through the decorated method can be removed.

        A remove method has to take the ID, which has been returned by the multi-input
        method as a parameter, so it knows which value has to be removed.

        The usage is described by the following example: if `A` is the name of
        the method, that is decorated with :class:`MultiInput`, the remove method
        has to be decorated with ``@A.remove``.

        :param method: the decorated remove method
        :returns: a MultiInputAssociateDescriptor, that generates a MultiInputAssociateProxy,
                  which enhances the decorated method with the functionality, that
                  is required for the multi-input connector
        """
        self.__remove_method = method
        return common.MultiInputAssociateDescriptor(method=method,
                                                    observers=self._observers,
                                                    parallelization=self._parallelization,
                                                    executor=self._executor)

    def replace(self, method):
        """A method of the decorated method to decorate the replace method, with
        which data, that has been added through the decorated method, can be replaced
        with new data without changing the ID under which it is stored.

        A replace method has to take the ID, under which the old data is stored,
        as first parameter and the new data as second parameter. It is strongly
        recommended, that this method stores the new data under the same ID as
        the old data. And this method must return the ID, under which the new
        data is stored.

        Also, if no data has been stored under the given ID, yet, the replace method
        shall simply store the data under the given ID instead of raising an error.

        Specifying a replace method is optional. If no method has been decorated
        to be a replace method, the :class:`MultiInput` connector falls back to removing
        the old data and adding the updated one, whenever updated data is propagated
        through its connections.

        The usage is described by the following example: if `A` is the name of
        the method, that is decorated with :class:`MultiInput`, the remove method
        has to be decorated with ``@A.replace``.

        :param method: the decorated replace method
        :returns: a MultiInputAssociateDescriptor, that generates a MultiInputAssociateProxy,
                  which enhances the decorated method with the functionality, that
                  is required for the multi-input connector
        """
        self.__replace_method = method
        return common.MultiInputAssociateDescriptor(method=method,
                                                    observers=self._observers,
                                                    parallelization=self._parallelization,
                                                    executor=self._executor)
