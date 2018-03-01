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

"""Base classes for the connector decorators"""

from .. import _lib as lib

__all__ = ("ConnectorDecorator", "InputDecorator")

default_executor = lib.executor()   # this instance is for the default value of the connector decorator's constructors


class ConnectorDecorator:
    """An abstract base class for the decoration of methods so they can be used
    as connectors.
    """
    def __init__(self, parallelization, executor):
        """
        :param parallelization: a flag from the :class:`connectors.Parallelization` enum.
                                See the Connector's :meth:`set_parallelization` method for details
        :param executor: an :class:`Executor` instance, that can be created with the
                         :func:`connectors.executor` function. See the Connector's
                         :meth:`set_executor` method for details
        """
        self._method = None     # Will be set in __call__
        self._parallelization = parallelization
        self._executor = executor

    def __call__(self, method):
        """Is called in order to replace the decorated method with this decorator.

        :param method: the unbound method, that was decorated with this decorator
        :returns: this decorator
        """
        self._method = method
        return self

    def __get__(self, instance, instance_type):
        """Is called, when the decorated method is accessed.

        :param instance: the instance of which a method shall be replaced
        :param instance_type: the type of the instance
        :returns: a :class:`ConnectorProxy` instance, that mimics the decorated
                  method and adds the connector functionality
        """
        raise NotImplementedError("This method should have been overridden in a derived class")


# pylint: disable=abstract-method; pylint shall not complain, that the __get__-method is not overridden in InputDecorator
class InputDecorator(ConnectorDecorator):
    """An addition to a :class:`ConnectorDecorator` for input connectors that notify
    their instances' output connectors when an incoming value changes their result
    values.
    """
    def __init__(self,
                 observers=(),
                 laziness=lib.Laziness.get_default(),
                 parallelization=lib.Parallelization.get_default_input_parallelization(),
                 executor=default_executor):
        """
        :param observers: the names of output methods that are affected by passing
                          a value to this connector. For convenience it is also
                          possible to pass a string here, if only one output
                          connector depends on this input.
        :param laziness: a flag from the :class:`connectors.Laziness` enum. See the
                         Connector's :meth:`set_laziness` method for details
        :param parallelization: a flag from the :class:`connectors.Parallelization` enum.
                                See the Connector's :meth:`set_parallelization` method for details
        :param executor: an :class:`Executor` instance, that can be created with the
                         :func:`connectors.executor` function. See the Connector's
                         :meth:`set_executor` method for details
        """
        ConnectorDecorator.__init__(self, parallelization=parallelization, executor=executor)
        if isinstance(observers, str):
            self._observers = (observers,)
        else:
            self._observers = observers
        self._laziness = laziness
