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

"""Contains the :class:`Output` class for decorating getter methods"""

from connectors._common import Parallelization
from .._proxies import OutputProxy
from ._baseclasses import ConnectorDecorator, default_executor

__all__ = ("Output",)


class Output(ConnectorDecorator):
    """A decorator, that marks a method as an output connector.
    These connections can be used to automatically update a processing chain
    when a value has changed.
    The decorated method must not take any arguments.
    """

    def __init__(self,
                 caching=True,
                 parallelization=Parallelization.default_output_parallelization(),
                 executor=default_executor):
        """
        :param caching: True, if caching shall be enabled, False otherwise. See
                        the :class:`~connectors.connectors.OutputConnector`'s
                        :meth:`~connectors.connectors.OutputConnector.set_caching`
                        method for details
        :param parallelization: a flag from the :class:`connectors.Parallelization` enum.
                                See the :class:`~connectors.connectors.OutputConnector`'s
                                :meth:`~connectors.connectors.OutputConnector.set_parallelization`
                                method for details
        :param executor: an :class:`~connectors._common._executors.Executor` instance,
                         that can be created with the :func:`connectors.executor`
                         function. See the :class:`~connectors.connectors.OutputConnector`'s
                         :meth:`~connectors.connectors.OutputConnector.set_executor`
                         method for details
        """
        ConnectorDecorator.__init__(self, parallelization, executor)
        self.__caching = caching

    def __get__(self, instance, instance_type):
        """Is called, when the decorated method is accessed.

        :param instance: the instance of which a method shall be replaced
        :param instance_type: the type of the instance
        :returns: an :class:`~connectors.proxies.OutputProxy` instance, that mimics
                  the decorated method and adds the connector functionality
        """
        return OutputProxy(instance=instance,
                           method=self._method,
                           caching=self.__caching,
                           parallelization=self._parallelization,
                           executor=self._executor)
