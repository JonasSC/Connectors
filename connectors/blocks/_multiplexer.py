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

"""Contains the :class:`Multiplexer` class."""

import connectors

__all__ = ("Multiplexer",)


class Multiplexer:
    """A class, that routes one of arbitrarily many inputs to its output.

    Usage Example: (the assignments ``_ = ...`` are only to make :mod:`doctest`
    ignore the return values of the operations.)

    >>> import connectors
    >>> # Create some test objects
    >>> test1 = connectors.blocks.PassThrough(data="One")
    >>> test2 = connectors.blocks.PassThrough(data="Two")
    >>> multiplexer = connectors.blocks.Multiplexer()
    >>> # Connect the test objects to the multiplexer
    >>> # Note, how the input of the input connector of the multiplexer is accessed like a dictionary
    >>> _ = multiplexer.input["1"].connect(test1.output)
    >>> _ = test2.output.connect(multiplexer.input[2])    # the order, which is connected to which is not important
    >>> # Select the output with the same selector, that has been passed as key, during connecting
    >>> _ = multiplexer.select("1")
    >>> multiplexer.output()
    'One'
    >>> _ = multiplexer.select(2)
    >>> multiplexer.output()
    'Two'
    """

    def __init__(self, selector=None):
        """
        :param selector: the selector of the input, that shall be routed to the output
        """
        self.__selector = selector
        self.__data = connectors.MultiInputData()

    @connectors.Output()
    def output(self):
        """Returns the value from the selected input.
        If no data is found for the given selector, the first input data set, that
        was added, is returned.

        :returns: the selected input object
        """
        if self.__selector in self.__data:
            return self.__data[self.__selector]
        else:
            return None

    @connectors.Input("output")
    def select(self, selector):
        """Specifies, which input shall be routed to the output.

        :param selector: the selector of the input, that shall be routed to the output
        :returns: the Multiplexer instance
        """
        self.__selector = selector
        return self

    @connectors.MultiInput("output")
    def input(self, data):
        """Specifies an input object, that can be selected to be routed to the output.
        When connecting to this method, the selector, by which the given connection
        can be selected, can be specified with the :meth:`~connectors.connectors.MultiInputConnector.__getitem__`
        overload::

           multiplexer.input[selector].connect(generator.output())

        :param data: the input object
        :returns: an ID, that can be used as a selector value t
        """
        return self.__data.add(data)

    @input.remove
    def remove(self, data_id):
        """Is used to remove an input object from the collection, when the respective
        connector is disconnected from the input.

        :param data_id: the data_id under which the input object is stored
        :returns: the Multiplexer instance
        """
        del self.__data[data_id]
        return self

    @input.replace
    def replace(self, data_id, data):
        """Is used to replace an input object, when the respective connected
        connector has produced a new one.

        :param data_id: the data_id under which the input object is stored
        :param data: the new input object
        :returns: ``data_id``, because the ID does not change for the replaced data
        """
        self.__data[data_id] = data
        return data_id

    @input.notify_condition
    def __input_condition(self, data_id, value):   # pylint: disable=unused-argument; notify condition methods must accept the new value
        """Prevents, that the output is notified about changes of an input, that
        is not currently selected.
        """
        return data_id == self.__selector
