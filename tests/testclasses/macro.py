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

"""Contains test classes for the macro connectors"""

import connectors
import testclasses

__all__ = ("Macro", "MacroInMacro", "MacroPreferences")


class Macro:
    """A test class with an internal processing network and macro connectors"""
    def __init__(self):
        self.__input1 = testclasses.Simple()
        self.__input2 = testclasses.Simple()
        self.__input3 = testclasses.Simple()
        hidden1 = testclasses.MultipleInputs()
        hidden1.set_value1.connect(self.__input1.get_value)
        hidden1.set_value2.connect(self.__input2.get_value)
        hidden2 = testclasses.MultipleInputs()
        hidden2.set_value1.connect(hidden1.get_values)
        hidden2.set_value2.connect(self.__input3.get_value)
        self.__output = testclasses.MultipleOutputs().set_value.connect(hidden2.get_values)

    @connectors.MacroInput()
    def set_input1(self, *_):
        """sets the first input value"""
        yield self.__input1.set_value

    @connectors.MacroInput()
    def set_input2and3(self, *_):
        """sets the second and third input value"""
        yield self.__input2.set_value
        yield self.__input3.set_value

    @connectors.MacroOutput()
    def get_output1(self):
        """returns the output value"""
        return self.__output.get_value

    @connectors.MacroOutput()
    def get_output2(self):
        """returns the output boolean"""
        return self.__output.get_bool


class MacroInMacro:
    """A test class whose internal processing network contains a class with macro connectors"""
    def __init__(self):
        self.__internal = Macro()

    @connectors.MacroInput()
    def set_input(self, *_):        # pylint: disable=missing-docstring
        yield self.__internal.set_input1
        yield self.__internal.set_input2and3

    @connectors.MacroOutput()
    def get_output(self):           # pylint: disable=missing-docstring
        return self.__internal.get_output1


class ConnectorPreferences:
    """A test class that can be configured like a connector"""
    def __init__(self):
        self.caching = True
        self.laziness = connectors.Laziness.ON_REQUEST
        self.parallelization = connectors.Parallelization.SEQUENTIAL
        self.executor = None

    def set_caching(self, caching):
        """Emulates a connector's set_caching method"""
        self.caching = caching

    def set_laziness(self, laziness):
        """Emulates a connector's set_laziness method"""
        self.laziness = laziness

    def set_parallelization(self, parallelization):
        """Emulates a connector's set_parallelization method"""
        self.parallelization = parallelization

    def set_executor(self, executor):
        """Emulates a connector's set_executor method"""
        self.executor = executor


class MacroPreferences:
    """This class exports :class:`ConnectorPreferences` instances through its macro
    connectors, so it can be tested how macro connectors pass on the configuration
    to the exported connectors.
    """
    def __init__(self):
        self.input1 = ConnectorPreferences()
        self.input2 = ConnectorPreferences()
        self.output = ConnectorPreferences()

    @connectors.MacroInput()
    def set_input(self, *_):    # pylint: disable=missing-docstring
        yield self.input1
        yield self.input2

    @connectors.MacroOutput()
    def get_output(self):       # pylint: disable=missing-docstring
        return self.output
