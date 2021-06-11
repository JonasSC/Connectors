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

"""Tests for garbage collection related issues"""

import gc
from . import helper
from . import testclasses


def test_end_of_lifetime():
    """Tests if processing classes are garbage collected, when they are no longer accessible"""
    # collect garbage from imports and other tests
    gc.collect()
    assert gc.collect() == 0
    gc.collect()

    # test an orphaned processing chain, where a getter at the end has been called
    def closure1():     # pylint: disable=missing-docstring
        t1 = testclasses.Simple()
        t2 = testclasses.MultipleOutputs().set_value.connect(t1.get_value)
        t2.get_value()

    closure1()
    assert gc.collect() == 0    # this should work, as long as all setters to which a value was announced are called, even when not all getters have been called

    # test an orphaned processing chain, where all connected setters have been called
    def closure2():     # pylint: disable=missing-docstring
        t1 = testclasses.Simple()
        t2 = testclasses.MultipleOutputs().set_value.connect(t1.get_value)
        t2.set_value("go away")

    closure2()
    assert gc.collect() == 0    # setting the value manually should have removed the announcement

    # test an orphaned processing chain, that has been disconnected
    def closure3():     # pylint: disable=missing-docstring
        t1 = testclasses.Simple()
        t2 = testclasses.MultipleOutputs().set_value.connect(t1.get_value)
        t2.set_value.disconnect(t1.get_value)

    closure3()
    assert gc.collect() == 0    # breaking the connection should have propagated the last value and therefore removed the announcement

    # test the same things with MultiInputs
    def closure4():     # pylint: disable=missing-docstring
        t1 = testclasses.Simple()
        t2 = testclasses.ReplacingMultiInput().add_value.connect(t1.get_value)
        t3 = testclasses.NonReplacingMultiInput().add_value.connect(t1.get_value)
        t2.get_values()
        t3.add_value.disconnect(t1.get_value)

    closure4()
    assert gc.collect() == 0

    # test connecting and setting a value (without retrieving the result) with a non lazy input
    def closure5():     # pylint: disable=missing-docstring
        t1 = testclasses.Simple()
        testclasses.NonLazyInputs().set_value.connect(t1.get_value)
        t1.set_value(1.0)

    closure5()
    assert gc.collect() == 0    # this should work, because the non lazy setter gets called automatically after changing the value, thus removing the announcement


def test_direct_method_calls():
    """Tests that calling a connector directly after instantiating a processing class is allowed"""
    # collect garbage from imports and other tests
    gc.collect()
    assert gc.collect() == 0
    # test calling a getter directly
    assert testclasses.Simple().get_value() is None
    assert gc.collect() == 0
    # test calling a setter directly
    testclasses.MultipleInputs().set_value1(1.0)
    assert gc.collect() == 0
    # test calling multiple setters directly
    testclasses.MultipleInputs().set_value1(2.0).set_value2(3.0)
    assert gc.collect() == 0
    # test calling a setter twice directly
    testclasses.MultipleInputs().set_value1(4.0).set_value1(5.0)
    assert gc.collect() == 0
    # test calling a setter and a getter directly
    assert testclasses.Simple().set_value(6.0).get_value() == 6.0
    assert gc.collect() == 0


def test_method_calls_in_constructor():
    """Tests that processing classes, which are calling connectors in their constructor
    are garbage collected through reference counting."""
    # collect garbage from imports and other tests
    gc.collect()
    assert gc.collect() == 0
    # test with a direct method call
    call_logger = helper.CallLogger()
    assert testclasses.ConstructorMethodCall(call_logger).get_values() == [None]
    assert call_logger.get_number_of_calls() == 6
    assert gc.collect() == 0
    call_logger.clear()

    # test with connections
    def closure():  # pylint: disable=missing-docstring
        t1 = testclasses.MultipleOutputs(call_logger)
        t2 = testclasses.ConstructorMethodCall(call_logger).set_first_value.connect(t1.get_value).add_value.connect(t1.get_bool)         # pylint: disable=line-too-long; this ugly concatenation works too
        t3 = testclasses.Simple(call_logger).set_value.connect(t2.get_values)
        t1.set_value(12.0)
        assert t3.get_value() == [12.0, True]
        assert call_logger.get_number_of_calls() == 13

    closure()
    assert gc.collect() == 0
