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

"""Tests for the helper functionalities"""

import gc
import weakref
import connectors
from . import helper
from . import testclasses


def test_multiplexer_functionality():
    """Tests the functionality of the :class:`Multiplexer` class."""
    mux = connectors.blocks.Multiplexer(selector=3)
    assert mux.input[1]("one") is mux
    assert mux.input[2]("two") is mux
    assert mux.output() is None
    assert mux.input[3]("three") is mux
    assert mux.output() == "three"
    assert mux.select(2) is mux
    assert mux.output() == "two"
    assert mux.replace(2, "Two") == 2
    assert mux.output() == "Two"
    assert mux.input[2]("TWO") is mux
    assert mux.output() == "TWO"
    assert mux.remove(2) is mux
    assert mux.output() is None


def test_multiplexer_connectors():
    """Tests the connectors of the :class:`Multiplexer` class."""
    call_logger = helper.CallLogger()
    mux = connectors.blocks.Multiplexer()
    t1 = testclasses.Simple(call_logger).set_value("one").get_value.connect(mux.input[1])
    t2 = testclasses.Simple(call_logger).set_value("two").get_value.connect(mux.input[2])
    to = testclasses.Simple(call_logger).set_value.connect(mux.output)
    call_logger.set_name_mapping(t1=t1, t2=t2, to=to)
    assert call_logger.get_number_of_calls() == 2   # the three set_value calls of the Simple instances
    # test when nothing is selected
    call_logger.clear()
    assert to.get_value() is None
    call_logger.compare([{((t1, "get_value", (), "one"),), ((t2, "get_value", (), "two"),)},
                         (to, "set_value", [None], to), (to, "get_value", (), None)])
    # test when a present value is selected
    call_logger.clear()
    ts = testclasses.Simple(call_logger).set_value(2).get_value.connect(mux.select)
    call_logger.set_name_mapping(ts=ts)
    assert to.get_value() == "two"
    call_logger.compare([(ts, "set_value", [2], ts), (ts, "get_value", [], 2),
                         (to, "set_value", ["two"], to), (to, "get_value", [], "two")])
    # test changing a selected input
    call_logger.clear()
    t2.set_value("Two")
    assert to.get_value() == "Two"
    call_logger.compare([(t2, "set_value", ["Two"], t2), (t2, "get_value", [], "Two"),
                         (to, "set_value", ["Two"], to), (to, "get_value", [], "Two")])
    # test changing a not selected input
    call_logger.clear()
    t1.set_value("One")
    assert to.get_value() == "Two"
    call_logger.compare([(t1, "set_value", ["One"], t1), (t1, "get_value", [], "One")])
    # test disconnecting a not selected input
    t1.get_value.disconnect(mux.input[1])
    call_logger.clear()
    assert to.get_value() == "Two"
    assert call_logger.get_number_of_calls() == 0
    # test selecting a value through a connection
    ts.set_value(1)
    mux.input[1].connect(t1.get_value)
    assert to.get_value() == "One"
    call_logger.compare([(ts, "set_value", [1], ts), (ts, "get_value", [], 1),
                         (to, "set_value", ["One"], to), (to, "get_value", [], "One")])
    # test disconnecting a selected input
    call_logger.clear()
    mux.input[1].disconnect(t1.get_value)
    assert to.get_value() is None
    call_logger.compare([(to, "set_value", [None], to), (to, "get_value", [], None)])


def test_passthrough():
    """Tests the functionality of the :class:`~connectors.blocks.PassThrough` class."""
    assert connectors.blocks.PassThrough().output() is None
    p = connectors.blocks.PassThrough(7.2)
    assert p.output() == 7.2
    p.input(5)
    assert p.output() == 5
    t1 = testclasses.Simple().get_value.connect(p.input)
    t2 = testclasses.Simple().set_value.connect(p.output)
    t1.set_value("foo")
    assert t2.get_value() == "foo"


def test_weakref_proxy_generator_functionality():
    """Tests the basic functionality of the :class:`WeakrefProxyGenerator` class."""
    # collect garbage from imports and other tests
    gc.collect()
    assert gc.collect() == 0
    # create a processing chain for testing
    t1 = connectors.blocks.WeakrefProxyGenerator()
    t2 = testclasses.Simple().set_value.connect(t1.output)
    t1.delete_reference.connect(t2.get_value)
    # create a data object and a weak reference as a handle to check if the data object has been garbage collected
    data = testclasses.NonLazyInputs()  # just have any object, for which a weak reference can be created
    data_ref = weakref.ref(data)
    # pass the data into the processing chain
    t1.input(data)
    del data                        # delete the local reference
    assert gc.collect() == 0        # make sure, the data object has been deleted by reference counting
    assert data_ref() is not None   # the data object has been deleted, since a reference to it has been stored by the setter
    data = data_ref()
    # retrieve the result of the processing chain
    assert t2.get_value() == data
    del data                    # delete the local reference
    assert gc.collect() == 0    # make sure, the data object has been deleted by reference counting
    assert data_ref() is None   # the data object has been deleted, because the loopback has told the X to delete the reference, that has been stored by the setter


def test_weakref_proxy_generator_data_types():
    """Tests the :class:`WeakrefProxyGenerator` class with different types of input data."""
    t = connectors.blocks.WeakrefProxyGenerator()
    for data in (1, 2.0, (3, 4.0), [5, 6.0], None):
        t.input(data)
        assert t.output() == data
