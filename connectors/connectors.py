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

"""A sub-module, that makes the Connector classes accessible.
Usually it should not be necessary to instantiate any of these classes, as they
are created by decorating methods.
"""

from ._connectors import *                          # pylint: disable=wildcard-import,unused-wildcard-import

from ._macro._input import MacroInputConnector      # pylint: disable=unused-import
from ._macro._output import MacroOutputConnector    # pylint: disable=unused-import

from ._proxies import *
from ._common import MultiInputAssociateProxy
