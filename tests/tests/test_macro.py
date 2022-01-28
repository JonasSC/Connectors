# This file is a part of the "Connectors" package
# Copyright (C) 2017-2022 Jonas Schulte-Coerne
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

"""Tests for the macro connectors"""

import connectors
from . import testclasses


def test_wrapping():
    """Tests if the macro connectors and the input connector proxies copy the
    docstring from the original method."""
    t = testclasses.Macro()
    input_macro_doc = t.set_input1.__doc__
    input_method_doc = t.set_input1._MacroInputConnector__method.__doc__        # pylint: disable=protected-access
    output_macro_doc = t.get_output1.__doc__
    output_method_doc = t.get_output1._MacroOutputConnector__method.__doc__     # pylint: disable=protected-access
    assert input_macro_doc == input_method_doc
    assert output_macro_doc == output_method_doc


def test_macro():
    """Tests the basic functionality of macro connectors"""
    macro = testclasses.Macro()
    t1 = testclasses.Simple().get_value.connect(macro.set_input1)
    t2 = testclasses.Simple().get_value.connect(macro.set_input2and3)
    t3 = testclasses.Simple().set_value.connect(macro.get_output1)
    t4 = testclasses.Simple().set_value.connect(macro.get_output2)
    # test the initial values and changing them through the connectors
    assert t3.get_value() == ((None, None), None)
    assert t4.get_value()
    t1.set_value(1.0)
    assert t3.get_value() == ((1.0, None), None)
    t2.set_value(2.0)
    assert t3.get_value() == ((1.0, 2.0), 2.0)
    # test disconnecting the inputs
    t1.get_value.disconnect(macro.set_input1)
    macro.set_input2and3.disconnect(t2.get_value)
    assert t3.get_value() == ((1.0, 2.0), 2.0)
    # test changing values through the macro inputs
    macro.set_input1(3.0)
    assert t3.get_value() == ((3.0, 2.0), 2.0)
    # test disconnecting the outputs
    t3.set_value.disconnect(macro.get_output1)
    macro.get_output2.disconnect(t4.set_value)
    macro.set_input2and3(4.0)
    assert macro.get_output1() == ((3.0, 4.0), 4.0)
    assert t3.get_value() == ((3.0, 2.0), 2.0)


def test_macro_in_macro():
    """Tests if the internal processing chain of a macro can also contain macro connectors"""
    macro = testclasses.MacroInMacro()
    # test without connectors
    assert macro.get_output() == ((None, None), None)   # pylint: disable=comparison-with-callable; Pylint got confused by the MacroOutput decorator
    macro.set_input(1.0)
    assert macro.get_output() == ((1.0, 1.0), 1.0)      # pylint: disable=comparison-with-callable; Pylint got confused by the MacroOutput decorator
    # test with connectors
    t1 = testclasses.Simple().get_value.connect(macro.set_input)
    t2 = testclasses.Simple().set_value.connect(macro.get_output)
    assert t2.get_value() == ((None, None), None)
    t1.set_value(2.0)
    assert t2.get_value() == ((2.0, 2.0), 2.0)


def test_macro_preferences():
    """Tests if the configuration of the macro connectors is passed on the the
    exported connectors.
    """
    t1 = testclasses.MacroPreferences()
    executor = connectors.executor()
    # input
    t1.set_input.set_laziness(connectors.Laziness.ON_NOTIFY)
    assert t1.input1.laziness == connectors.Laziness.ON_NOTIFY
    assert t1.input2.laziness == connectors.Laziness.ON_NOTIFY
    t1.set_input.set_parallelization(connectors.Parallelization.PROCESS)
    assert t1.input1.parallelization == connectors.Parallelization.PROCESS
    assert t1.input2.parallelization == connectors.Parallelization.PROCESS
    t1.set_input.set_executor(executor)
    assert t1.input1.executor is executor
    assert t1.input2.executor is executor
    # output
    t1.get_output.set_caching(False)
    assert not t1.output.caching
    t1.get_output.set_parallelization(connectors.Parallelization.PROCESS)
    assert t1.output.parallelization == connectors.Parallelization.PROCESS
    t1.get_output.set_executor(executor)
    assert t1.output.executor is executor


def test_macro_input_output_cascade():
    """Tests if the macro input connectors return the instance, so that cascading
    the calls of inputs and one output connector is possible.
    """
    # test the basic idea
    t = testclasses.Macro()
    assert t.set_input1(2.3) is t
    # test a cascade of calling two inputs and an output at the end
    assert testclasses.Macro().set_input1(2.3).set_input2and3(4.9).get_output1() == ((2.3, 4.9), 4.9)
