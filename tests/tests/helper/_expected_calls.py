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

"""Contains classes and functions for comparing an expected sequence of method
calls with one, that was recorded by a CallLogger instance.
"""

import collections
import functools

__all__ = ("ExpectedCallList",)


class ExpectedCall:
    """Models an expected call, so that it can be processed by a ExpectedCallList instance"""

    def __init__(self, call):
        """
        @param call: a tuple (INSTANCE, METHOD, VALUE), where INSTANCE is the object,
                     of which a method call is expected, METHOD is the string method
                     name and VALUE is optional and can be the argument, that is
                     expected to be passed to the method.
        """
        self.__call = call
        self.__found = False

    def check(self, call):
        """Checks if the given call is the expected one of this instance."""
        if call.class_ != self.__call[0].__class__.__name__:
            return False
        if call.method != self.__call[1]:
            return False
        if call.identifier != self.__call[0].get_identifier():
            return False
        if len(self.__call) > 3:
            if call.value != self.__call[3]:
                return False
        self.__found = True
        return True

    def found(self):
        """Returns True, if the expected call of this instance has already been passed to the check method."""
        return self.__found

    def expected(self):
        """Returns a list of still expected calls. This is useful when generating error messages."""
        if self.__found:
            return []
        else:
            return [self.__call]


class ExpectedCallList:
    """Manages lists of expected calls and allows to check if a given recorded
    call is expected."""

    def __init__(self, call_list):
        """
        @param call_list: a list of expected calls as tuples (INSTANCE, METHOD, VALUE),
                          where INSTANCE is the object, of which a method call is
                          expected, METHOD is the string method name and VALUE is
                          optional and can be the argument, that is expected to
                          be passed to the method.
        """
        self.__call_list = list(call_list)
        self.__expected = None
        self.__found = False
        self.__next()

    def check(self, call):
        """Checks if the given call is expected now."""
        if isinstance(self.__expected, collections.abc.Iterable):
            result = False
            for e in self.__expected:
                result = result or e.check(call)
                if result:
                    break
            self.__expected = [e for e in self.__expected if not e.found()]
            if self.__expected == []:
                self.__next()
        else:
            result = self.__expected.check(call)
            if self.__expected.found():
                self.__next()
        return result

    def found(self):
        """Returns True, if all expected calls in the list have already been passed to the check method."""
        return self.__found

    def expected(self):
        """Returns a list of still expected calls. This is useful when generating error messages."""
        if isinstance(self.__expected, collections.abc.Iterable):
            return functools.reduce(lambda a, b: a + b, [e.expected() for e in self.__expected])
        else:
            return self.__expected.expected()

    def __next(self):
        if self.__call_list:
            item = self.__call_list.pop(0)
            if isinstance(item, (set, frozenset)):  # sets indicate parallel streams of execution, so that any of the call lists in it might expect the recorded call
                self.__expected = [ExpectedCallList(i) for i in item]
            else:
                self.__expected = ExpectedCall(item)
        else:
            self.__found = True
