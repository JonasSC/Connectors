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

"""Contains tests that fail, because the current implementation of the *Connectors*
package does not show the desired behavior.
"""

import gc
import pytest
from . import testclasses


def test_orphaned_connection():
    """Shows, that a processing chain with pending computations is not garbage
    collected by Python's reference counting.
    """
    # collect garbage from imports and other tests
    gc.collect()
    assert gc.collect() == 0

    # test garbage collection of connected instances, that are no longer reachable
    def closure():  # pylint: disable=missing-docstring
        t1 = testclasses.Simple()
        testclasses.Simple().set_value.connect(t1.get_value)

    closure()
    with pytest.raises(AssertionError):
        assert gc.collect() == 0    # this cannot be zero, as the value of t2 has been announced (by making the connection) but not retrieved


def test_laziness_change_in_constructor():
    """Shows that changing parameters of connectors in the constructor replaces
    the methods too early, which prevents accessing the connectors directly after
    instantiating the processing class.
    """
    # storing the instance and then calling the connector works
    t = testclasses.ConstructorLazinessChange()
    assert t.set_value(0) is t
    # since changing the laziness replaces the method with the connector, which
    # only has a weak reference to the instance, the instance is garbage collected
    # before the setter is called directly
    with pytest.raises(AttributeError):
        testclasses.ConstructorLazinessChange().set_value(0)


def test_caching_change_in_constructor():
    """Shows that changing parameters of connectors in the constructor replaces
    the methods too early, which prevents accessing the connectors directly after
    instantiating the processing class.
    """
    # storing the instance and then calling the connector works
    t = testclasses.ConstructorCachingChange()
    assert t.get_value() is None
    # since changing the caching behavior replaces the method with the connector,
    # which only has a weak reference to the instance, the instance is garbage
    # collected before the setter is called directly
    with pytest.raises(AttributeError):
        testclasses.ConstructorCachingChange().get_value()


def test_parallelization_change_in_constructor():
    """Shows that changing parameters of connectors in the constructor replaces
    the methods too early, which prevents accessing the connectors directly after
    instantiating the processing class.
    """
    # storing the instance and then calling the connector works
    t = testclasses.ConstructorParallelizationChange()
    assert t.get_value() is None
    # since changing the parallelization flag replaces the method with the connector,
    # which only has a weak reference to the instance, the instance is garbage
    # collected before the setter is called directly
    with pytest.raises(AttributeError):
        testclasses.ConstructorParallelizationChange().get_value()


def test_executor_change_in_constructor():
    """Shows that changing parameters of connectors in the constructor replaces
    the methods too early, which prevents accessing the connectors directly after
    instantiating the processing class.
    """
    # storing the instance and then calling the connector works
    t = testclasses.ConstructorExecutorChange()
    assert t.get_value() is None
    # since changing the executor replaces the method with the connector, which
    # only has a weak reference to the instance, the instance is garbage collected
    # before the setter is called directly
    with pytest.raises(AttributeError):
        testclasses.ConstructorExecutorChange().get_value()
