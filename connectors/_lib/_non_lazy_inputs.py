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

"""Defines a container class for tracking non-lazy input connectors"""

import asyncio

__all__ = ("NonLazyInputs",)


class NonLazyInputs(set):
    """A subclass of set, that is used internally to track the non-lazy input connectors,
    that request an immediate re-computation of the processing chain.
    """
    def __init__(self, situation):
        """
        :param situation: a flag from the Laziness enumeration to which the laziness
                          of the connectors is compared in order to decide, if it
                          shall be added to this set.
        """
        set.__init__(self)
        self.__situation = situation

    def add(self, connector, laziness):
        """Adds a connector to this container, if its laziness is low enough to
        cause immediate execution.

        :param connector: the InputConnector instance, that shall be added
        :param laziness: the laziness setting of that connector as a flag from the Laziness enumeration
        """
        if laziness >= self.__situation:
            set.add(self, connector)

    def execute(self, executor):
        """Executes the necessary computations, that are requested by the non-lazy
        input connectors.

        :param executor: the Executor instance, that manages the executions
        """
        if self:
            tasks = asyncio.wait(tuple(i._execute(executor) for i in self))
            executor.run_until_complete(tasks)

    async def execute_async(self, executor):
        """Executes the necessary computations, that are requested by the non-lazy
        input connectors.
        This method is a coroutine, that is meant to be called, when the executor is already active.

        :param executor: the Executor instance, that manages the executions
        """
        if self:
            await asyncio.wait(tuple(i._execute(executor) for i in self))
