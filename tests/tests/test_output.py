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

"""Tests for functionalities specific for output connectors"""

from . import helper
from . import testclasses


def test_wrapping():
    """Tests if the output connectors and the output connector proxies copy the
    docstring from the original method."""
    t = testclasses.Simple()
    proxy_doc = t.get_value.__doc__
    testclasses.Simple().set_value.connect(t.get_value)
    connector_doc = t.get_value.__doc__
    method_doc = t.get_value._method.__doc__    # pylint: disable=protected-access
    assert proxy_doc == method_doc
    assert connector_doc == method_doc


def test_caching():
    """Tests the caching of an output connector's return value"""
    call_logger = helper.CallLogger()
    # set up a small processing chain
    t1 = testclasses.Simple(call_logger)
    t1.get_value.set_caching(False)
    t2 = testclasses.Simple(call_logger).set_value.connect(t1.get_value)
    t3 = testclasses.Simple(call_logger).set_value.connect(t1.get_value)
    # change a value and check if it is propagated correctly
    t1.set_value(1.0)
    assert t2.get_value() == 1.0
    assert t3.get_value() == 1.0
    # check the call log (t1.get_value should only be called once)
    call_logger.compare([(t1, "set_value", 1.0), (t1, "get_value", 1.0),
                         (t2, "set_value", 1.0), (t2, "get_value", 1.0),
                         (t3, "set_value", 1.0), (t3, "get_value", 1.0)])
    # call the getter of t2 again (since there has been no announcement, t1.get_value should not be called again)
    call_logger.clear()
    assert t2.get_value() == 1.0
    call_logger.compare([])     # t2.get_value should not have been called either, because it has cached its value
    # call the getter of t1 manually (t1.get_value should be called again, because it does not cache its value)
    assert t1.get_value() == 1.0
    call_logger.compare([(t1, "get_value", 1.0)])
    # repeat the first tests with MultiInput setters
    t4 = testclasses.ReplacingMultiInput(call_logger).add_value.connect(t1.get_value)
    t5 = testclasses.NonReplacingMultiInput(call_logger).add_value.connect(t1.get_value)
    t1.set_value(2.0)
    assert t4.get_values() == [2.0]
    assert t5.get_values() == [2.0]
