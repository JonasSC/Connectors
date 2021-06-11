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

"""Helper functions for input connectors"""

import inspect

__all__ = ("select_condition_methods", "resolve_observers", "forward_announcement", "get_first_argument")


def non_condition(*args, **kwargs):   # pylint: disable=unused-argument; this method has to be compatible with multiple input connector implementations
    """A condition function for the announce- or notify condition of an input
    connector, if that condition is not specified.

    :returns: True
    """
    return True


def select_condition_methods(announce_condition, notify_condition):
    """Selects the announce- and notify conditions, in case any of them is None

    :param announce_condition: a method for the announce condition or None
    :param notify_condition: a method for the notify condition or None
    :returns: a tuple of the announce- and notify condition methods, neither of which is None
    """
    return (non_condition if announce_condition is None else announce_condition,
            non_condition if notify_condition is None else notify_condition)


def resolve_observers(instance, observers):
    """Gets the observing output connectors for an input connector

    :param instance: the instance, to which the input and the output connectors belong
    :param observers: a sequence of string method names
    :returns: a tuple of OutputConnector instances
    """
    return [getattr(instance, o)._get_connector() for o in observers]


def forward_announcement(connector, observers, non_lazy_inputs, laziness):
    """Forwards the announcement, that an input connector has received, to the
    observing output connectors.

    :param connector: the input connector, that has received the announcement
    :param observers: a sequence of observing output connectors, to which the
                      announcement shall be forwarded
    :param non_lazy_inputs: a :class:`~connectors._common._non_lazy_inputs.NonLazyInputs`
                            instance to which input connectors can be appended,
                            if they request an immediate re-computation (see the
                            :class:`~connectors._connectors._base_classes.InputConnector`'s
                            :meth:`~connectors._connectors._base_classes.InputConnector.set_laziness`
                            method for more about lazy execution)
    :param laziness: the laziness setting of the input connector
    """
    initial_number_of_non_lazy_inputs = len(non_lazy_inputs)
    for o in observers:
        o._announce(connector, non_lazy_inputs)
    if len(non_lazy_inputs) == initial_number_of_non_lazy_inputs:   # only add self, if no methods down the processing chain requests its execution anyway
        non_lazy_inputs.add(connector=connector, laziness=laziness)


def get_first_argument(method, *args, **kwargs):
    """Gets the first argument, that has been passed to a method, from the *args
    and **kwargs parameters.

    When using this function for an unbound method, don't pass the 'self' argument
    to this function, because otherwise, this would be the one, that is always
    returned.

    :param method: the method, of whose call, the first parameter shall be determined
    :param `*args,**kwargs`: the parameters, that have been passed to the method
    :returns: the first argument, that has been passed to the method, or None if no argument has been passed
    """
    if args:
        return args[0]
    elif len(kwargs) == 1:  # a shortcut to avoid introspection
        return next(iter(kwargs.values()))
    else:                   # get the first argument of the method, that is given in the **kwargs dict
        for a in inspect.signature(method).parameters:
            if a in kwargs:
                return kwargs[a]
    return None
