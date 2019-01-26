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

"""Test for multi-input connectors"""

import connectors
from . import testclasses
from . import helper


def test_wrapping():
    """Tests if the multi-input connectors and the multi-input connector proxies
     copy the docstring from the original method."""
    t = testclasses.ReplacingMultiInput()
    add_proxy_doc = t.add_value.__doc__
    remove_proxy_doc = t.remove_value.__doc__
    replace_proxy_doc = t.replace_value.__doc__
    testclasses.Simple().get_value.connect(t.add_value)
    add_connector_doc = t.add_value.__doc__
    add_method_doc = t.add_value._method.__doc__                                    # pylint: disable=protected-access
    remove_method_doc = t.remove_value._MultiInputAssociateProxy__method.__doc__    # pylint: disable=protected-access
    replace_method_doc = t.replace_value._MultiInputAssociateProxy__method.__doc__  # pylint: disable=protected-access
    assert add_proxy_doc == add_method_doc
    assert add_connector_doc == add_method_doc
    assert remove_proxy_doc == remove_method_doc
    assert replace_proxy_doc == replace_method_doc


def test_manual_method_calls():
    """Tests the behavior, when multi-input connectors are called manually like
    methods, rather than through connections"""
    # non replacing MultiInput
    t1 = testclasses.Simple()
    t2 = testclasses.Simple()
    t2.set_value.set_laziness(connectors.Laziness.ON_ANNOUNCE)
    not_connected = testclasses.NonReplacingMultiInput()
    not_connected.add_value(None)
    connected = testclasses.NonReplacingMultiInput().add_value.connect(t1.get_value)
    t2.set_value.connect(connected.get_values)
    for instance in (not_connected, connected):
        assert instance.get_values() == [None]
        id1 = instance.add_value(1.0)
        assert instance.get_values() == [None, 1.0]
        instance.add_value(2.0)
        assert instance.get_values() == [None, 1.0, 2.0]
        instance.remove_value(id1)
        assert instance.get_values() == [None, 2.0]
    # replacing MultiInput
    t1 = testclasses.Simple()
    t2 = testclasses.Simple()
    t2.set_value.set_laziness(connectors.Laziness.ON_ANNOUNCE)
    not_connected = testclasses.ReplacingMultiInput()
    not_connected.add_value(None)
    connected = testclasses.ReplacingMultiInput().add_value.connect(t1.get_value)
    t2.set_value.connect(connected.get_values)
    for instance in (not_connected, connected):
        assert instance.get_values() == [None]
        id1 = instance.add_value(10)
        assert instance.get_values() == [None, 10]
        instance.add_value(20)
        assert instance.get_values() == [None, 10, 20]
        instance.replace_value(id1, 30)
        assert instance.get_values() == [None, 30, 20]
        instance.remove_value(id1)
        assert instance.get_values() == [None, 20]


def test_non_replacing_multiinput():
    """Tests the behavior of a multi-input connector without a replace method"""
    call_logger = helper.CallLogger()
    # test without connections
    instance = testclasses.NonReplacingMultiInput(call_logger)
    assert instance.get_values() == []
    id1 = instance.add_value(1)
    assert instance.get_values() == [1]
    instance.add_value(2)
    assert instance.get_values() == [1, 2]
    instance.remove_value(id1)
    assert instance.get_values() == [2]
    # test with connections
    t1 = testclasses.Simple(call_logger)
    t1.set_value(11)
    instance.add_value.connect(t1.get_value)
    t2 = testclasses.Simple(call_logger)
    t2.set_value(12)
    instance.add_value.connect(t2.get_value)
    assert instance.get_values() == [2, 11, 12]
    t1.set_value(13)
    assert instance.get_values() == [2, 12, 13]


def test_replacing_multiinput():
    """Tests the behavior of a multi-input connector with a replace method"""
    call_logger = helper.CallLogger()
    # test without connections
    instance = testclasses.ReplacingMultiInput(call_logger)
    assert instance.get_values() == []
    id1 = instance.add_value(1)
    assert instance.get_values() == [1]
    instance.add_value(2)
    assert instance.get_values() == [1, 2]
    instance.replace_value(id1, 3)
    assert instance.get_values() == [3, 2]
    instance.remove_value(id1)
    assert instance.get_values() == [2]
    # test with connections
    t1 = testclasses.Simple(call_logger)
    t1.set_value(11)
    instance.add_value.connect(t1.get_value)
    t2 = testclasses.Simple(call_logger)
    t2.set_value(12)
    instance.add_value.connect(t2.get_value)
    assert instance.get_values() == [2, 11, 12]
    t1.set_value(13)
    assert instance.get_values() == [2, 13, 12]


def test_multiple_outputs():
    """Tests the behavior of a multi-input connector upon which two output connectors depend."""
    call_logger = helper.CallLogger()
    # set the processing chain
    t1 = testclasses.Simple(call_logger)
    t2 = testclasses.MultiInputMultipleOutputs(call_logger).add_value.connect(t1.get_value)
    t3 = testclasses.MultipleInputs(call_logger)
    t3.set_value1.connect(t2.get_values)
    t3.set_value2.connect(t2.get_bools)
    call_logger.compare([])
    # check the executed methods
    t1.set_value(25.4)
    assert t3.get_values() == ([25.4], [True])
    call_logger.compare([(t1, "set_value", 25.4), (t1, "get_value", 25.4), (t2, "add_value", 25.4),
                         set((((t2, "get_values", (25.4)), (t3, "set_value1", (25.4))),
                              ((t2, "get_bools", (True)), (t3, "set_value2", (True))))),
                         (t3, "get_values", ([25.4], [True]))])


def test_disconnect():
    """Tests the behavior when disconnecting a multi-input connector"""
    t1 = testclasses.Simple()
    t2 = testclasses.Simple()
    t3 = testclasses.ReplacingMultiInput()
    t3.add_value.connect(t1.get_value)
    t3.add_value.connect(t2.get_value)
    t1.set_value(1.0)
    t2.set_value(2.0)
    assert t3.get_values() == [1.0, 2.0]
    t3.add_value.disconnect(t2.get_value)
    assert t3.get_values() == [1.0]


def test_laziness_on_connect():
    """Tests the behavior of a non-lazy multi-input connector, that requests new
    data as soon as it becomes available and also when connecting an output connector
    to the multi-input connector"""
    call_logger = helper.CallLogger()
    # set up a small processing chain
    t1 = testclasses.NonReplacingMultiInput(call_logger)
    t2 = testclasses.NonLazyInputs(call_logger)
    t2.add_value.set_laziness(connectors.Laziness.ON_CONNECT)
    t2.add_value.connect(t1.get_values)
    call_logger.compare([(t1, "get_values", None), (t2, "add_value", None)])
    # change a value and check that the setter is called
    call_logger.clear()
    t1.add_value(1.0)
    call_logger.compare([(t1, "add_value", 1.0), (t1, "get_values", 1.0), (t2, "replace_value")])
    # change the input's laziness and check again
    call_logger.clear()
    t2.add_value.set_laziness(connectors.Laziness.ON_REQUEST)
    t1.add_value(2.0)
    call_logger.compare([(t1, "add_value", 2.0)])


def test_laziness_on_announce():
    """Tests the behavior of a non-lazy multi-input connector, that requests new
    data as soon as it becomes available"""
    call_logger = helper.CallLogger()
    # set up a small processing chain
    t1 = testclasses.NonReplacingMultiInput(call_logger)
    t2 = testclasses.NonLazyInputs(call_logger).add_value.connect(t1.get_values)
    call_logger.compare([])
    # change a value and check that the setter is called
    t1.add_value(1.0)
    call_logger.compare([(t1, "add_value", 1.0), (t1, "get_values", 1.0), (t2, "add_value", 1.0)])
    # change the input's laziness and check again
    call_logger.clear()
    t2.add_value.set_laziness(connectors.Laziness.ON_REQUEST)
    t1.add_value(2.0)
    call_logger.compare([(t1, "add_value", 2.0)])
    # check that the set_laziness method is also available in the proxies
    call_logger.clear()
    t3 = testclasses.ReplacingMultiInput(call_logger)
    t3.add_value.set_laziness(connectors.Laziness.ON_ANNOUNCE)
    t3.add_value.connect(t1.get_values)
    call_logger.compare([])
    t1.add_value(3.0)
    call_logger.compare([(t1, "add_value", 3.0), (t1, "get_values", 3.0), (t3, "add_value", 3.0)])


def test_laziness_on_notify():
    """Tests the behavior of a non-lazy multi-input connector, that requests new
    data as soon as it has been computed"""
    call_logger = helper.CallLogger()
    # set up a small processing chain
    t1 = testclasses.Simple(call_logger)
    t2 = testclasses.Simple(call_logger).set_value.connect(t1.get_value)
    t3 = testclasses.NonReplacingMultiInput(call_logger).add_value.connect(t1.get_value)
    t3.add_value.set_laziness(connectors.Laziness.ON_NOTIFY)
    call_logger.compare([])
    # set the value
    t1.set_value(1.0)
    call_logger.compare([(t1, "set_value", 1.0)])
    call_logger.clear()
    # retrieve the value through t2 and check if t3 updates itself
    assert t2.get_value() == 1.0
    call_logger.compare([(t1, "get_value", 1.0),
                         set([((t2, "set_value", 1.0), (t2, "get_value", 1.0)),
                              ((t3, "add_value", 1.0),)])])
    call_logger.clear()
    assert t3.get_values() == [1.0]
    call_logger.compare([(t3, "get_values", (1.0,))])


def test_condition_on_announce():
    """Tests the conditional announcement of value changes"""
    call_logger = helper.CallLogger()
    t1 = testclasses.Simple(call_logger)
    t2 = testclasses.ConditionalMultiInputAnnouncement(call_logger).add_value.connect(t1.get_value)
    t3 = testclasses.Simple(call_logger).set_value.connect(t2.get_values)
    # test with condition == True
    call_logger.compare([])
    t1.set_value(1.0)
    assert t3.get_value() == [1.0]
    call_logger.compare([(t1, "set_value", 1.0), (t1, "get_value", 1.0),
                         (t2, "add_value", 1.0), (t2, "get_values", [1.0]),
                         (t3, "set_value", [1.0]), (t3, "get_value", [1.0])])
    # test with condition == False
    t2.condition = False
    call_logger.clear()
    t1.set_value(2.0)
    assert t3.get_value() == [1.0]
    call_logger.compare([(t1, "set_value", 2.0)])
    assert t2.get_values() == [1.0]
    # test calling the method directly
    t2.condition = False
    call_logger.clear()
    t2.add_value(3.0)
    assert t3.get_value() == [1.0, 3.0]
    call_logger.compare([(t2, "add_value", 3.0), (t2, "get_values", [1.0, 3.0]),
                         (t3, "set_value", [1.0, 3.0]), (t3, "get_value", [1.0, 3.0])])
    # test disconnecting
    t2.condition = False
    call_logger.clear()
    t1.get_value.disconnect(t2.add_value)
    assert t3.get_value() == [3.0]
    call_logger.compare([(t2, "remove_value"), (t2, "get_values", [3.0]),
                         (t3, "set_value", [3.0]), (t3, "get_value", [3.0])])


def test_condition_on_notify():
    """Tests the conditional notification of observing output connectors about value changes"""
    call_logger = helper.CallLogger()
    t1 = testclasses.Simple(call_logger)
    t2 = testclasses.ConditionalMultiInputNotification(call_logger).add_value.connect(t1.get_value)
    t3 = testclasses.Simple(call_logger).set_value.connect(t2.get_values)
    call_logger.compare([])
    # test with condition == True
    t1.set_value(1.0)
    assert t3.get_value() == [1.0]
    call_logger.compare([(t1, "set_value", 1.0), (t1, "get_value", 1.0),
                         (t2, "add_value", 1.0), (t2, "get_values", [1.0]),
                         (t3, "set_value", [1.0]), (t3, "get_value", [1.0])])
    # test with condition == False
    t2.condition = False
    call_logger.clear()
    t1.set_value(2.0)
    assert t3.get_value() == [1.0]
    call_logger.compare([(t1, "set_value", 2.0), (t1, "get_value", 2.0), (t2, "replace_value", 1.0)])
    assert t2.get_values() == [1.0]
    # test calling the method directly
    t2.condition = False
    call_logger.clear()
    t2.add_value(3.0)
    assert t3.get_value() == [1.0]
    call_logger.compare([(t2, "add_value", 3.0)])
    assert t2.get_values() == [1.0]
    # test for an implementation detail, that specifying the value as keyword argument takes a slightly more complex code path
    data_id = t2.add_value(value=4.0)
    t2.remove_value(data_id)
    # test disconnecting
    t2.condition = False
    call_logger.clear()
    t1.get_value.disconnect(t2.add_value)
    assert t3.get_value() == [1.0]
    call_logger.compare([(t2, "remove_value")])
    # test changing the condition
    call_logger.clear()
    t2.set_condition(True)
    assert t3.get_value() == [3.0]  # the value from calling the method directly
    call_logger.compare([(t2, "set_condition", True), (t2, "get_values", [3.0]),
                         (t3, "set_value", [3.0]), (t3, "get_value", [3.0])])
