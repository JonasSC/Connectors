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

"""Contains the :class:`Input` class for decorating setter methods"""

from .._proxies import SingleInputProxy
from ._baseclasses import InputDecorator

__all__ = ("Input",)


class Input(InputDecorator):
    """A decorator, that marks a method as an input for single connections.
    These connections can be used to automatically update a processing chain
    when a value has changed.
    The decorated method must take exactly one argument.
    """

    def __get__(self, instance, instance_type):
        """Is called, when the decorated method is accessed.

        :param instance: the instance of which a method shall be replaced
        :param instance_type: the type of the instance
        :returns: a :class:`~connectors.proxies.SingleInputProxy` instance, that mimics
                  the decorated method and adds the connector functionality
        """
        return SingleInputProxy(instance=instance,
                                method=self._method,
                                observers=self._observers,
                                announce_condition=self._announce_condition,
                                notify_condition=self._notify_condition,
                                laziness=self._laziness,
                                parallelization=self._parallelization,
                                executor=self._executor)
