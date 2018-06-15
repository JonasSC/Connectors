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

"""Tests for infrastructure tasks such as licensing, packaging etc."""

import os
import connectors
import tests


def test_license():
    """Tests if all source files have the correct license header"""
    header = ("# This file is a part of the \"Connectors\" package\n",
              "# Copyright (C) 2017-2018 Jonas Schulte-Coerne\n",
              "#\n",
              "# This program is free software: you can redistribute it and/or modify it under\n",
              "# the terms of the GNU Lesser General Public License as published by the Free\n",
              "# Software Foundation, either version 3 of the License, or (at your option) any\n",
              "# later version.\n",
              "#\n",
              "# This program is distributed in the hope that it will be useful, but WITHOUT\n",
              "# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS\n",
              "# FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public License for more\n",
              "# details.\n",
              "#\n",
              "# You should have received a copy of the GNU Lesser General Public License along\n",
              "# with this program. If not, see <http://www.gnu.org/licenses/>.\n")
    for directory in (os.path.split(connectors.__file__)[0],
                      os.path.split(tests.__file__)[0]):
        for dirpath, _, filenames in os.walk(directory):
            for filename in filenames:
                if filename.lower().endswith(".py"):
                    with open(os.path.join(directory, dirpath, filename)) as f:
                        line = f.readline()
                        if line == "":
                            break   # an empty file does not need a license header
                        else:
                            for h in header:
                                assert line == h
                                line = f.readline()
