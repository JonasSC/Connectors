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

"""Contains the :class:`~connectors._common._multiinput_item.MultiInputItem` class"""

from ._flags import Laziness
from ._non_lazy_inputs import NonLazyInputs
from ._input import get_first_argument

__all__ = ("MultiInputItem",)


class MultiInputItem:
    """An object, that is returned by the :meth:`~connectors.connectors.MultiInputConnector.__getitem__`
    overload.

    It simulates the behavior of a single-input connector, so it is possible to
    use a multi-input connector as arbitrarily many single-inputs.
    """

    def __init__(self, connector, instance, replace_method, key, observers, executor):
        """
        :param connector: the multi-input connector
        :param instance: the instance of which the method was replaced by the
                         multi-input connector
        :param replace_method: an unbound method, that is used to replace data,
                               that has been added through the multi-input connector
        :param key: the key with which the multi-input has been accessed.
        :param observers: a sequence of output connectors, that observe the
                          multi-input connector's value changes.
        :param executor: an :class:`~connectors._common._executors.Executor` instance,
                         that is used, when calling the instance of this class.
        """
        self.__connector = connector
        self.__instance = instance
        self.__replace = replace_method
        self.__key = key
        self.__observers = observers
        self.__executor = executor

    def __call__(self, *args, **kwargs):
        """Calls the given replace-method

        :param `*args,**kwargs`: arguments for the replace-method
        :returns: the instance of which the method was replaced by the multi-input connector
        """
        if self.__observers:
            non_lazy_inputs = NonLazyInputs(Laziness.ON_ANNOUNCE)
            for o in self.__observers:
                o._announce(self.__connector, non_lazy_inputs)
            data_id = self.__replace(self.__instance, self.__key, *args, **kwargs)
            value = get_first_argument(self.__replace, *args, **kwargs)
            self.__connector._add_to_notification_condition_checks(data_id=data_id, value=value)    # pylint: disable=protected-access; this call stays within the context of a multi-input connector.
            self.__connector._notify_observers()                                                    # pylint: disable=protected-access; this call stays within the context of a multi-input connector.
            non_lazy_inputs.execute(self.__executor)
        else:
            self.__replace(self.__instance, self.__key, *args, **kwargs)
        return self.__instance

    def connect(self, connector):
        """Connects this virtual single-input to an output.

        :param connector: the connector, to which this connector shall be connected
        :returns: the instance of which the method was replaced by the multi-input connector
        """
        connector.connect(self)
        return self.__instance

    def disconnect(self, connector):
        """Disconnects this virtual single-input from an output, to which is has been connected..

        :param connector: the connector, from which this connector shall be disconnected
        :returns: the instance of which the method was replaced by the multi-input connector
        """
        connector.disconnect(self)
        return self.__instance

    def _connect(self, connector):
        """This method is called from an :class:`OutputConnector`, when it is being
        connected to this virtual single-input.

        :param connector: the connector to which this connector shall be connected
        :returns: yields the instance, of which a method has been replaced by the multi-input connector
        """
        return self.__connector._get_connector()._connect(connector, key=self.__key)

    def _disconnect(self, connector):
        """This method is called from an :class:`OutputConnector`, when it is being
        disconnected from this virtual single-input.

        :param connector: the connector from which this connector shall be disconnected
        :returns: yields the instance, of which a method has been replaced by the multi-input connector
        """
        return self.__connector._disconnect(connector)
