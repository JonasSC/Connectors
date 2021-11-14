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

"""Tests for the automatic parallelization"""

import time
import connectors
from . import testclasses


def test_parallelization_and_executors():
    """Tests the correctness of the computation with different parallelization configurations"""
    t1 = testclasses.Simple()
    t2 = testclasses.ReplacingMultiInput().add_value.connect(t1.get_value)
    t3 = testclasses.Simple().set_value.connect(t2.get_values)
    input_value = 0
    for executor in (connectors.executor(threads=t, processes=p) for p in (0, 2) for t in(0, 2)):
        for output_parallelization in (connectors.Parallelization.SEQUENTIAL,
                                       connectors.Parallelization.THREAD,
                                       connectors.Parallelization.PROCESS):
            for input_parallelization in (connectors.Parallelization.SEQUENTIAL,            # putting setter in a separate process
                                          connectors.Parallelization.THREAD):               # will not work, since the changes will
                for multiinput_parallelization in (connectors.Parallelization.SEQUENTIAL,   # not be applied to the objects in the
                                                   connectors.Parallelization.THREAD):      # main process.
                    t1.get_value.set_parallelization(output_parallelization)
                    t2.add_value.set_parallelization(multiinput_parallelization)
                    t3.set_value.set_parallelization(input_parallelization)
                    t3.get_value.set_executor(executor)
                    t1.set_value(input_value)
                    assert t3.get_value() == (input_value,)
                    input_value += 1


def test_concurrency():
    """Tests if parallelized tasks actually run concurrently"""
    t1 = testclasses.MultipleOutputs()
    t2 = testclasses.SleepInMultiInput().add_value.connect(t1.get_value)
    t3 = testclasses.SleepInInput().set_value.connect(t1.get_bool)
    t4 = testclasses.SleepInOutput().set_value.connect(t1.get_value)
    t5 = testclasses.MultipleInputs()
    t5.set_value1.connect(t2.get_values)
    t5.set_value2.connect(t3.get_value)
    t6 = testclasses.ReplacingMultiInput()
    t6.add_value.connect(t5.get_values)
    t6.add_value.connect(t4.get_value)
    t1.set_value(1.0)
    t6.get_values.set_executor(connectors.executor(threads=4))
    start_time = time.time()
    assert t6.get_values() == (((1.0,), True), 1.0)
    run_duration = time.time() - start_time
    assert run_duration > 1.0   # the longest running path has a sleep time of 1s
    assert run_duration < 2.0   # since both paths can be executed in parallel, their sleep times must not be added


def test_multioutput_parallelization():
    """tests if the getter method is executed concurrently with the different parameters."""
    t1 = testclasses.SleepInMultiOutput()
    t2 = testclasses.Simple().set_value.connect(t1.get_value[1])
    t3 = testclasses.Simple().set_value.connect(t1.get_value[1])
    t4 = testclasses.Simple().set_value.connect(t1.get_value[4])
    t5 = testclasses.ReplacingMultiInput() \
        .add_value.connect(t2.get_value) \
        .add_value.connect(t3.get_value) \
        .add_value.connect(t4.get_value)
    t1.set_value(3)
    start_time = time.time()
    assert t5.get_values() == (3, 3, 12)
    run_duration = time.time() - start_time
    assert run_duration > 1.0                   # the longest running path has a sleep time of 1s
    assert run_duration < 2.0                   # since the getter can be executed in parallel, its sleep times must not be added
