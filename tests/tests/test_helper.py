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

import connectors


def test_multiinput_data():
    """Tests the :class:`MultiInputData` container."""
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
