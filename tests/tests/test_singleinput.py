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

"""Basic functionality tests with input connectors and output connectors"""

import connectors
import helper
import testclasses


def test_wrapping():
    """Tests if the input connectors and the input connector proxies copy the
    docstring from the original method."""
    t = testclasses.Simple()
    proxy_doc = t.set_value.__doc__
    testclasses.Simple().get_value.connect(t.set_value)
    connector_doc = t.set_value.__doc__
    method_doc = t.set_value._method.__doc__
    assert proxy_doc == method_doc
    assert connector_doc == method_doc


def test_simple_input_output_chain():
    """Tests of a simple chain of two processing objects, that pass through their input value"""
    call_logger = helper.CallLogger()
    # set up a small processing chain
    t1 = testclasses.Simple(call_logger)
    t2 = testclasses.Simple(call_logger).set_value.connect(t1.get_value)
    call_logger.compare([])
    # retrieve a value and check the executed methods
    assert t2.get_value() is None
    call_logger.compare([(t1, "get_value", None), (t2, "set_value", None), (t2, "get_value", None)])
    call_logger.clear()
    # modify a value and check the executed methods
    t1.set_value(1.0)
    call_logger.compare([(t1, "set_value", 1.0)])
    assert t2.get_value() == 1.0
    call_logger.compare([(t1, "set_value", 1.0), (t1, "get_value", 1.0),
                         (t2, "set_value", 1.0), (t2, "get_value", 1.0)])


def test_multiple_inputs():
    """Tests the behavior of a processing class with multiple inputs, that affect the same output"""
    call_logger = helper.CallLogger()
    # set up a small processing chain
    t1 = testclasses.Simple(call_logger)
    t2 = testclasses.MultipleInputs(call_logger).set_value1.connect(t1.get_value)
    call_logger.compare([])
    # retrieve a value and check the executed methods
    assert t2.get_values() == (None, None)
    call_logger.compare([(t1, "get_value", None), (t2, "set_value1", None), (t2, "get_values", (None, None))])
    call_logger.clear()
    # set one value and check that the methods for the others have not been executed
    t2.set_value2(94.7)
    assert t2.get_values() == (None, 94.7)
    call_logger.compare([(t2, "set_value2", None), (t2, "get_values", (None, 94.7))])
    call_logger.clear()
    # modify a value at the very beginning of the chain and check the executed methods
    t1.set_value(1.0)
    call_logger.compare([(t1, "set_value", 1.0)])
    assert t2.get_values() == (1.0, 94.7)
    call_logger.compare([(t1, "set_value", 1.0), (t1, "get_value", 1.0),
                         (t2, "set_value1", 1.0), (t2, "get_values", (1.0, 1.0))])
    call_logger.clear()
    # connect both inputs of the second instance to the output of the first
    t2.set_value2.connect(t1.get_value,)
    assert t2.get_values() == (1.0, 1.0)
    call_logger.clear()
    t1.set_value(2)
    assert t2.get_values() == (2, 2)
    call_logger.compare([(t1, "set_value", 2), (t1, "get_value", 2),
                         set((((t2, "set_value1", 2),), ((t2, "set_value2", 2),))), (t2, "get_values", (2, 2))])


def test_multiple_outputs():
    """Tests the behavior of a processing class with multiple outputs, that depend on the same input"""
    call_logger = helper.CallLogger()
    # set up a small processing chain
    t1 = testclasses.Simple(call_logger)
    t2 = testclasses.MultipleOutputs(call_logger).set_value.connect(t1.get_value)
    call_logger.compare([])
    # retrieve one value and check the executed methods
    assert t2.get_value() is None
    call_logger.compare([(t1, "get_value", None), (t2, "set_value", None), (t2, "get_value", None)])
    call_logger.clear()
    # retrieve the other value and check the executed methods
    assert t2.get_bool() == bool(None)
    call_logger.compare([(t2, "get_bool", bool(None))])
    call_logger.clear()
    # make the processing chain a bit more complex and check the executed methods
    t3 = testclasses.MultipleInputs(call_logger)
    t3.set_value1.connect(t2.get_value)
    t3.set_value2.connect(t2.get_bool)
    t1.set_value(25.4)
    assert t3.get_values() == (25.4, True)
    call_logger.compare([(t1, "set_value", 25.4), (t1, "get_value", 25.4), (t2, "set_value", 25.4),
                         set((((t2, "get_value", 25.4), (t3, "set_value1", 25.4)),
                              ((t2, "get_bool", True), (t3, "set_value2", True)))),
                         (t3, "get_values", (25.4, True))])


def test_disconnect():
    """Tests the behavior when breaking a connection"""
    call_logger = helper.CallLogger()
    # set up a small processing chain
    t1 = testclasses.Simple(call_logger)
    t2 = testclasses.Simple(call_logger).set_value.connect(t1.get_value)
    call_logger.compare([])
    # change a value
    t1.set_value(1.0)
    call_logger.compare([(t1, "set_value", 1.0)])
    # break the connection and check, that the value change before the break is propagated
    t2.set_value.disconnect(t1.get_value)
    call_logger.compare([(t1, "set_value", 1.0), (t1, "get_value", 1.0), (t2, "set_value", 1.0)])
    # verify, that later value changes are not propagated
    call_logger.clear()
    t1.set_value(2.0)
    assert t2.get_value() == 1.0
    call_logger.compare([(t1, "set_value", 2.0), (t2, "get_value", 1.0)])


def test_laziness_on_connect():
    """Tests the behavior of a non-lazy input connector, that requests new data
    as soon as it becomes available and also when connecting an output connector
    to the input connector"""
    call_logger = helper.CallLogger()
    # test ON_REQUEST setting
    t1 = testclasses.Simple(call_logger)
    testclasses.Simple(call_logger).set_value.connect(t1.get_value)
    call_logger.compare([])
    # test ON_NOTIFY setting with a cached result
    t1 = testclasses.Simple(call_logger)
    t1.get_value()  # even if there is a cached value, the creation of the connection shall not cause a value propagation
    call_logger.clear()
    t2 = testclasses.Simple(call_logger)
    t2.set_value.set_laziness(connectors.Laziness.ON_NOTIFY)
    t2.set_value.connect(t1.get_value)
    call_logger.compare([])
    # test ON_ANNOUNCE setting
    t1 = testclasses.Simple(call_logger)
    t2 = testclasses.Simple(call_logger)
    t2.set_value.set_laziness(connectors.Laziness.ON_ANNOUNCE)
    t2.set_value.connect(t1.get_value)
    call_logger.compare([])
    # test ON_CONNECT setting
    t1 = testclasses.Simple(call_logger)
    t2 = testclasses.Simple(call_logger)
    t2.set_value.set_laziness(connectors.Laziness.ON_CONNECT)
    t2.set_value.connect(t1.get_value)
    call_logger.compare([(t1, "get_value", None), (t2, "set_value", None)])


def test_laziness_on_announce():
    """Tests the behavior of a non-lazy input connector, that requests new data
    as soon as it becomes available"""
    call_logger = helper.CallLogger()
    # set up a small processing chain
    t1 = testclasses.Simple(call_logger)
    t2 = testclasses.NonLazyInputs(call_logger).set_value.connect(t1.get_value)
    call_logger.compare([])
    # change a value and check that the setter is called
    t1.set_value(1.0)
    call_logger.compare([(t1, "set_value", 1.0), (t1, "get_value", 1.0), (t2, "set_value", 1.0)])
    # change the input's laziness and check again
    call_logger.clear()
    t2.set_value.set_laziness(connectors.Laziness.ON_REQUEST)
    t1.set_value(2.0)
    call_logger.compare([(t1, "set_value", 2.0)])
    # check that the set_laziness method is also available in the proxies
    call_logger.clear()
    t3 = testclasses.Simple(call_logger)
    t3.set_value.set_laziness(connectors.Laziness.ON_ANNOUNCE)
    t3.set_value.connect(t1.get_value)
    call_logger.compare([])
    t1.set_value(3.0)
    call_logger.compare([(t1, "set_value", 3.0), (t1, "get_value", 3.0), (t3, "set_value", 3.0)])


def test_laziness_on_notify():
    """Tests the behavior of a non-lazy input connector, that requests new data
    as soon as it has been computed"""
    call_logger = helper.CallLogger()
    # set up a small processing chain
    t1 = testclasses.Simple(call_logger)
    t2 = testclasses.Simple(call_logger)
    t3 = testclasses.Simple(call_logger)
    t3.set_value.set_laziness(connectors.Laziness.ON_NOTIFY)
    t2.set_value.connect(t1.get_value)
    t3.set_value.connect(t1.get_value)
    call_logger.compare([])
    # set the value
    t1.set_value(1.0)
    call_logger.compare([(t1, "set_value", 1.0)])
    call_logger.clear()
    # retrieve the value through t2 and check if t3 updates itself
    assert t2.get_value() == 1.0
    call_logger.compare([(t1, "get_value", 1.0),
                         set([((t2, "set_value", 1.0), (t2, "get_value", 1.0)),
                              ((t3, "set_value", 1.0),)])])
    call_logger.clear()
    assert t3.get_value() == 1.0
    call_logger.compare([(t3, "get_value", 1.0)])
