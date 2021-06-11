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

"""Defines enumeration classes for flags, with which certain behaviors of the
connectors can be configured.
"""

import enum

__all__ = ("Laziness", "Parallelization")


@enum.unique
class Laziness(enum.IntEnum):
    """An enumeration type for defining the laziness of input connectors. The
    enumeration values are sorted by how lazy the behavior is, which they represent,
    so smaller/greater comparisons are possible. Do not rely on the exact integer
    value though, since they are not guaranteed to have the same value in any version
    of this package.

    1. ON_REQUEST
        the setter is called, when its execution is requested by a method further
        down the processing chain.
    2. ON_NOTIFY
        the setter is called, when the connected getter has computed the input
        value, even if the execution of this setter has not been requested.
    3. ON_ANNOUNCE
        the setter is requests its input value immediately and is executed as soon
        as that is available. But connecting the setter, does not cause a request
        of the input value.
    4. ON_CONNECT
        same as ON_ANNOUNCE, but the value is also requested, when a new connection
        is established, which influences the input value of this connector. This
        connection is does not necessarily have to be with this connector, but it
        can also be further upstream in the processing chain.
    """
    ON_REQUEST = 1
    ON_NOTIFY = 2
    ON_ANNOUNCE = 3
    ON_CONNECT = 4

    @staticmethod
    def default():
        """returns the default laziness setting for input connectors.

        :returns: a constant from this enumeration
        """
        return Laziness.ON_REQUEST


@enum.unique
class Parallelization(enum.Enum):
    """An enumeration type for the parallelization parameter of an executor's
    :meth:`~connectors._common._executors.Executor.run_method` method:

    * SEQUENTIAL
        the method can only be executed sequentially.
    * THREAD
        the method should be executed in a separate thread, sequential execution
        is possible as a fallback.
    * PROCESS
        the method should be executed in a separate process, threaded execution
        or sequential execution can be used as a fallback.
    """
    SEQUENTIAL = enum.auto()
    THREAD = enum.auto()
    PROCESS = enum.auto()

    @staticmethod
    def default_output_parallelization():
        """returns the default parallelization setting for output connectors.

        :returns: a constant from this enumeration
        """
        return Parallelization.THREAD

    @staticmethod
    def default_multioutput_parallelization():
        """returns the default parallelization setting for multi-output connectors.

        :returns: a constant from this enumeration
        """
        return Parallelization.THREAD

    @staticmethod
    def default_input_parallelization():
        """returns the default parallelization setting for input connectors.

        :returns: a constant from this enumeration
        """
        return Parallelization.SEQUENTIAL

    @staticmethod
    def default_multiinput_parallelization():
        """returns the default parallelization setting for multi-input connectors.

        :returns: a constant from this enumeration
        """
        return Parallelization.SEQUENTIAL
