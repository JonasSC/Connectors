# This file is a part of the "Connectors" package
# Copyright (C) 2017-2019 Jonas Schulte-Coerne
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

"""Tests for multi-output connectors"""

import pytest
from . import helper
from . import testclasses


def test_wrapping():
    """Tests if the multi-output connectors and the multi-output connector proxies
     copy the docstring from the original method."""
    t = testclasses.MultiOutputWithKeys()
    get_proxy_doc = t.get_value.__doc__
    keys_proxy_doc = t.keys.__doc__
    testclasses.Simple().set_value.connect(t.get_value[3])
    get_connector_doc = t.get_value.__doc__
    keys_connector_doc = t.keys.__doc__
    get_method_doc = t.get_value._method.__doc__    # pylint: disable=protected-access
    keys_method_doc = """Returns a couple of example keys for the get_value method"""
    assert get_proxy_doc == get_method_doc
    assert keys_proxy_doc == keys_method_doc
    assert get_connector_doc == get_method_doc
    assert keys_connector_doc == keys_method_doc


def test_manual_method_calls():
    """Tests the behavior, when multi-output connectors are called manually like
    methods, rather than through connections"""
    t = testclasses.MultiOutputWithKeys()
    assert t.get_value(1) == 0
    assert t.get_value(4) == 0
    assert t.keys() == {2, 3, 5}
    t.set_value(7)
    assert t.get_value(1) == 7
    assert t.get_value(4) == 28
    # check that the the connector does not alter the fact, that the method requires an argument
    with pytest.raises(TypeError):
        t.get_value()   # pylint: disable=no-value-for-parameter; calling without argument is exactly, what shall be tested here


def test_manual_item_calls():
    """Tests the behavior, when multi-output connector's virtual single outputs
    are called manually like methods, rather than through connections"""
    t = testclasses.MultiOutputWithKeys()
    assert t.get_value[3]() == 0
    assert t.get_value[9]() == 0
    t.set_value(4)
    assert t.get_value[6]() == 24
    assert t.get_value[8]() == 32
    # check that the the connector does not alter the fact, that the method takes only one argument
    with pytest.raises(TypeError):
        t.get_value[12](4)


def test_caching():
    """tests if the caching works as expected"""
    # make a connection, because otherwise the output is not replaced with a connector
    call_logger = helper.CallLogger()
    t1 = testclasses.Simple(call_logger).set_value(1)
    t2 = testclasses.MultiOutputWithKeys(call_logger).set_value.connect(t1.get_value)
    # test with caching enabled
    assert t2.get_value(2) == 2
    call_logger.compare([(t1, "set_value", 1), (t1, "get_value", 2),
                         (t2, "set_value", 1), (t2, "get_value", 2)]).clear()
    assert t2.get_value(2) == 2     # this should come from the cache
    assert t2.get_value[2]() == 2   # this should come from the cache
    assert call_logger.get_number_of_calls() == 0
    assert t2.get_value[9]() == 9
    call_logger.compare([(t2, "get_value", 9)]).clear()
    assert t2.get_value(9) == 9     # this should come from the cache
    assert t2.get_value[9]() == 9   # this should come from the cache
    assert call_logger.get_number_of_calls() == 0
    # test with caching disabled
    t2.get_value.set_caching(False)
    assert t2.get_value(2) == 2
    assert t2.get_value(4) == 4
    assert t2.get_value[9]() == 9
    call_logger.compare([(t2, "get_value", 2), (t2, "get_value", 4), (t2, "get_value", 9)]).clear()


def test_caching_in_parallelization():
    """tests if the caching also works, when the getter method is executed concurrently."""
    # pylint: disable=line-too-long; the expected calls can be specified in a more readable fashion, if there are more liberties with the line length
    call_logger = helper.CallLogger()
    t1 = testclasses.MultiOutputWithoutKeys(call_logger)
    t2 = testclasses.Simple(call_logger).set_value.connect(t1.get_value[1])
    t3 = testclasses.Simple(call_logger).set_value.connect(t1.get_value[1])
    t4 = testclasses.Simple(call_logger).set_value.connect(t1.get_value[4])
    t5 = testclasses.ReplacingMultiInput(call_logger) \
        .add_value.connect(t2.get_value) \
        .add_value.connect(t3.get_value) \
        .add_value.connect(t4.get_value)
    call_logger.set_instance_mapping({"t1": t1, "t2": t2, "t3": t3, "t4": t4, "t5": t5})
    t1.set_value(3)
    assert t5.get_values() == [3, 3, 12]
    call_logger.compare([(t1, "set_value", 3),  # test that the getter is only executed once for the parameter 1
                         {((t1, "get_value", 3), frozenset({((t2, "set_value", 3), (t2, "get_value", 3), (t5, "add_value", 3)),
                                                            ((t3, "set_value", 3), (t3, "get_value", 3), (t5, "add_value", 3))})),
                          ((t1, "get_value", 12), (t4, "set_value", 12), (t4, "get_value", 12), (t5, "add_value", 12))},
                         (t5, "get_values", [3, 3, 12])])


def test_single_connections():
    """tests if connecting single-inputs to a multi-output connector works as expected."""
    t1 = testclasses.MultiOutputWithKeys()
    t2 = testclasses.Simple().set_value.connect(t1.get_value[1])
    t3 = testclasses.Simple()
    t1.get_value[1].connect(t3.set_value)
    t4 = testclasses.Simple().set_value.connect(t1.get_value[4])
    t5 = testclasses.ReplacingMultiInput().add_value.connect(t1.get_value[5])
    t1.get_value[6].connect(t5.add_value)
    # check if the connections worked
    assert t2.get_value() == 0
    assert t3.get_value() == 0
    assert t4.get_value() == 0
    assert t5.get_values() == [0, 0]
    # check if the value change is propagated correctly
    t1.set_value(5)
    assert t2.get_value() == 5
    assert t3.get_value() == 5
    assert t4.get_value() == 20
    assert t5.get_values() == [25, 30]
    # check if disconnecting works as expected
    t1.get_value[1].disconnect(t2.set_value)
    t4.set_value.disconnect(t1.get_value[4])
    t1.get_value[5].disconnect(t5.add_value)
    t5.add_value.disconnect(t1.get_value[6])
    t1.set_value(7)
    assert t2.get_value() == 5
    assert t3.get_value() == 7  # this should still be connected
    assert t4.get_value() == 20
    assert t5.get_values() == []


def test_connection_errors():
    """tests the errors, that are expected to be raised, when the multi-output
    is connected to single-inputs without having specified a parameter.
    """
    t = testclasses.MultiOutputWithKeys()
    with pytest.raises(TypeError):
        testclasses.Simple().set_value.connect(t.get_value)
    with pytest.raises(TypeError):
        t.get_value.connect(testclasses.Simple().set_value)
    with pytest.raises(TypeError):
        testclasses.ReplacingMultiInput().add_value[9].connect(t.get_value)
    with pytest.raises(TypeError):
        t.get_value.connect(testclasses.ReplacingMultiInput().add_value[9])


def test_multi_connections_with_keys():
    """tests if connecting the multi-output connector to a multi-input works as expected."""
    t1 = testclasses.MultiOutputWithKeys()
    t2 = testclasses.ReplacingMultiInput().add_value.connect(t1.get_value)
    assert t2.get_values() == [0, 0, 0]
    t1.set_value(7)
    assert set(t2.get_values()) == {14, 21, 35}
    # test changing keys
    t1.set_keys({3, 5, 7})
    assert set(t2.get_values()) == {21, 35, 49}
    # test disconnecting
    t1.get_value.disconnect(t2.add_value)
    assert t2.get_values() == []


def test_multi_connections_without_keys():
    """tests if connecting the multi-output connector to a multi-input works as expected."""
    t2 = testclasses.ReplacingMultiInput()
    t1 = testclasses.MultiOutputWithoutKeys().get_value.connect(t2.add_value)
    assert t2.get_values() == []
    t1.set_value(7)
    assert t2.get_values() == []
    # test disconnecting
    t2.add_value.disconnect(t1.get_value)
    assert t2.get_values() == []


def test_multi_connections_with_volatile_keys():
    """tests if connecting the multi-output connector to a multi-input works as expected."""
    t1 = testclasses.MultiOutputWithVolatileKeys()
    t2 = testclasses.ReplacingMultiInput().add_value.connect(t1.get_value)
    assert t2.get_values() == [0, 0, 0]
    t1.set_value(7)
    assert set(t2.get_values()) == {14, 21, 35}
    # test changing keys
    t1.set_keys({3, 5, 7})
    assert set(t2.get_values()) == {21, 35, 49}
    # test disconnecting
    t1.get_value.disconnect(t2.add_value)
    assert t2.get_values() == []


def test_multi_connections_with_dynamic_keys():
    """tests if connecting the multi-output connector to a multi-input works as expected."""
    t1 = testclasses.Simple().set_value({1, 2, 3})
    t2 = testclasses.MultiOutputWithKeys().set_keys.connect(t1.get_value)
    t3 = testclasses.ReplacingMultiInput().add_value.connect(t2.get_value)
    assert t3.get_values() == [0, 0, 0]
    t2.set_value(7)
    assert set(t3.get_values()) == {7, 14, 21}
    # test changing keys
    t1.set_value({3, 5, 7})
    assert set(t3.get_values()) == {21, 35, 49}
    # test disconnecting
    t1.get_value.disconnect(t2.set_keys)
    assert set(t3.get_values()) == {21, 35, 49}
    t2.get_value.disconnect(t3.add_value)
    assert t3.get_values() == []
