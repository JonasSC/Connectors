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

"""Contains test classes for the condition functions of (multi) input connectors"""

import connectors
from ._baseclass import BaseTestClass

__all__ = ("ConditionalInputAnnouncement", "ConditionalInputNotification",
           "ConditionalMultiInputAnnouncement", "ConditionalMultiInputNotification")


class ConditionalInputAnnouncement(BaseTestClass):
    """Features an input connector with a condition for the announcement of value changes"""

    def _initialize(self):                      # pylint: disable=missing-docstring
        self.__value = None
        self.condition = True

    @connectors.Input("get_value")
    def set_value(self, value):                 # pylint: disable=missing-docstring
        self._register_call(method_name="set_value", parameters=[value], return_value=self)
        self.__value = value
        return self

    @connectors.Output()
    def get_value(self):                        # pylint: disable=missing-docstring
        self._register_call(method_name="get_value", parameters=[], return_value=self.__value)
        return self.__value

    @set_value.announce_condition
    def __condition(self):                      # pylint: disable=missing-docstring
        return self.condition


class ConditionalInputNotification(BaseTestClass):
    """Features an input connector with a condition for the notification about value changes"""

    def _initialize(self):                      # pylint: disable=missing-docstring
        self.__value = None
        self.condition = True

    @connectors.Input("get_value")
    def set_value(self, value):                 # pylint: disable=missing-docstring
        self._register_call(method_name="set_value", parameters=[value], return_value=self)
        self.__value = value
        return self

    @connectors.Output()
    def get_value(self):                        # pylint: disable=missing-docstring
        self._register_call(method_name="get_value", parameters=[], return_value=self.__value)
        return self.__value

    @set_value.notify_condition
    def __condition(self, value):               # pylint: disable=missing-docstring,unused-argument
        return self.condition


class ConditionalMultiInputAnnouncement(BaseTestClass):
    """Features a multi-input connector with a condition for the announcement of value changes"""

    def _initialize(self):                      # pylint: disable=missing-docstring
        self.__data = connectors.MultiInputData()
        self.condition = True

    @connectors.MultiInput("get_values")
    def add_value(self, value):                 # pylint: disable=missing-docstring
        data_id = self.__data.add(value)
        self._register_call(method_name="add_value", parameters=[value], return_value=data_id)
        return data_id

    @add_value.remove
    def remove_value(self, data_id):            # pylint: disable=missing-docstring
        self._register_call(method_name="remove_value", parameters=[data_id], return_value=self)
        del self.__data[data_id]
        return self

    @add_value.replace
    def replace_value(self, data_id, value):    # pylint: disable=missing-docstring
        self._register_call(method_name="replace_value", parameters=[data_id, value], return_value=data_id)
        self.__data[data_id] = value
        return data_id

    @add_value.announce_condition
    def __condition(self, data_id):             # pylint: disable=missing-docstring,unused-argument
        return self.condition

    @connectors.Output()
    def get_values(self):                       # pylint: disable=missing-docstring
        result = tuple(self.__data.values())
        self._register_call(method_name="get_values", parameters=[], return_value=result)
        return result


class ConditionalMultiInputNotification(BaseTestClass):
    """Features a multi-input connector with a condition for the notification about value changes"""

    def _initialize(self):                      # pylint: disable=missing-docstring
        self.__data = connectors.MultiInputData()
        self.condition = True

    @connectors.Input("get_values")
    def set_condition(self, condition):         # pylint: disable=missing-docstring
        self._register_call(method_name="set_condition", parameters=[condition], return_value=self)
        self.condition = condition
        return self

    @connectors.MultiInput("get_values")
    def add_value(self, value):                 # pylint: disable=missing-docstring
        data_id = self.__data.add(value)
        self._register_call(method_name="add_value", parameters=[value], return_value=data_id)
        return data_id

    @add_value.remove
    def remove_value(self, data_id):            # pylint: disable=missing-docstring
        self._register_call(method_name="remove_value", parameters=[data_id], return_value=self)
        del self.__data[data_id]
        return self

    @add_value.replace
    def replace_value(self, data_id, value):    # pylint: disable=missing-docstring
        self._register_call(method_name="replace_value", parameters=[data_id, value], return_value=data_id)
        self.__data[data_id] = value
        return data_id

    @add_value.notify_condition
    def __condition(self, data_id, value):      # pylint: disable=missing-docstring,unused-argument
        return self.condition

    @connectors.Output()
    def get_values(self):                       # pylint: disable=missing-docstring
        result = tuple(self.__data.values())
        self._register_call(method_name="get_values", parameters=[], return_value=result)
        return result
