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

"""Contains a derived class of asyncio.Event"""

import asyncio

__all__ = ("Event",)


class Event(asyncio.Event):
    """Extends asyncio.Event, so that the event loop for waiting for the Event
    is passed to the wait method.

    This makes it possible to create instances of this event before starting the
    event loop.
    """

    async def wait(self, executor):     # pylint: disable=arguments-differ; the whole point of this class is, that the executor is passed to the wait method
        """waits for the Event's value to be "True"

        :param executor: the executor instance, that manages the event loop
        :returns: True
        """
        self._loop = executor.get_event_loop()
        try:
            return await super().wait()
        finally:
            self._loop = None
