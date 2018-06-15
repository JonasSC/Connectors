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

"""Tests for the helper functionalities"""

import gc
import weakref
import connectors
from . import testclasses


def test_multiinput_data():
    """Tests the :class:`MultiInputData` container"""
    data = connectors.MultiInputData([1, 2, 3, 4])
    assert list(data.values()) == [1, 2, 3, 4]
    data_id = data.add(5)
    assert list(data.values()) == [1, 2, 3, 4, 5]
    data[data_id] = 5.1
    assert list(data.values()) == [1, 2, 3, 4, 5.1]
    del data[data_id]
    assert list(data.values()) == [1, 2, 3, 4]
    data.clear()
    assert list(data.values()) == []


def test_weakref_proxy_generator_functionality():
    """Tests the basic functionality of the :class:`WeakrefProxyGenerator` class"""
    # collect garbage from imports and other tests
    gc.collect()
    assert gc.collect() == 0
    # create a processing chain for testing
    t1 = connectors.WeakrefProxyGenerator()
    t2 = testclasses.Simple().set_value.connect(t1.get_weakref_proxy)
    t1.delete_reference.connect(t2.get_value)
    # create a data object and a weak reference as a handle to check if the data object has been garbage collected
    data = testclasses.NonLazyInputs()  # just have any object, for which a weak reference can be created
    data_ref = weakref.ref(data)
    # pass the data into the processing chain
    t1.set_data(data)
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
    """Tests the :class:`WeakrefProxyGenerator` class with different types of input data"""
    t = connectors.WeakrefProxyGenerator()
    for data in (1, 2.0, (3, 4.0), [5, 6.0], None):
        t.set_data(data)
        assert t.get_weakref_proxy() == data
