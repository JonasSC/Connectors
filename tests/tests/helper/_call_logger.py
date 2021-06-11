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

"""Contains a class for logging calls and comparing that log to a given call sequence"""

import collections
from . import _expected_calls as expected_calls

__all__ = ("CallLogger",)

Call = collections.namedtuple(typename="Call", field_names=("class_", "method", "identifier", "value"))


def format_call(call, mapping):
    """formats a call as a human readable string, so it can be used for debug prints
    and error messages

    :param call: either a logged call (a Call instance) or an expected call, which
                 is a tuple (INSTANCE, METHOD, VALUE), where INSTANCE is the object,
                 of which a method call is expected, METHOD is the string method
                 name and VALUE is optional and can be the argument, that is
                 expected to be passed to the method
    :param mapping: an optional mapping from an instance's identifier to the name
                    of the variable, in which it is stored
    :returns: a string
    """
    if isinstance(call, Call):
        identifier = call.identifier
        class_ = call.class_
        method = call.method
        value = call.value
    else:
        identifier = call[0].get_identifier()
        class_ = call[0].__class__.__name__
        method = call[1]
        value = call[2] if len(call) >= 3 else ""
    if identifier in mapping:
        instance = mapping[identifier]
        return f"{instance}.{method}({value})"
    else:
        return f"{identifier}-{class_}.{method}({value})"


class CallLogger:
    """Logs calls, so that the logs can be compared to expected call sequences.
    Many classes in the :mod:`testclasses` module allow to pass a call logger as a
    constructor parameter.
    """

    def __init__(self):
        self.__calls = []
        self.__mapping = {}

    def register_call(self, instance, methodname, value):
        """Is called by methods, when a call shall be logged"""
        self.__calls.append(Call(class_=instance.__class__.__name__,
                                 method=methodname,
                                 identifier=instance.get_identifier(),
                                 value=value))

    def set_instance_mapping(self, mapping):
        """Specifies a mapping from string variable names to BaseTestClass instances,
        which allows for more readable debug prints and error messages.
        """
        for k, v in mapping.items():
            self.__mapping[v.get_identifier()] = k
        return self

    def clear(self):
        """Clears the current call log"""
        self.__calls = []
        return self

    def compare(self, call_list):
        """Compares the recorded call log to an expected call sequence.

        Calls in the call sequence are described by tuples (INSTANCE, METHOD_NAME, PARAMETER).

        If the order of parts of the call sequence is not known, these parts can
        be put in a set inside the call sequence.

        :param call_list: the call sequence as a list. This list is modified by this call.
        """
        expected = expected_calls.ExpectedCallList(call_list)
        for call in self.__calls:
            if expected.found():
                c = format_call(call, self.__mapping)
                raise AssertionError(f"the call of {c} was not expected")
            else:
                if not expected.check(call):
                    e = "{" + ", ".join([format_call(c, self.__mapping) for c in expected.expected()]) + "}"
                    c = format_call(call, self.__mapping)
                    raise AssertionError(f"expected one of the following calls:\n    {e}\nbut found {c}.")
        if not expected.found():
            e = "{" + ", ".join([format_call(c, self.__mapping) for c in expected.expected()]) + "}"
            raise AssertionError(f"expected one of the following calls:\n    {e}\nbut no calls were registered.")
        return self

    def get_number_of_calls(self):
        """Returns the number of recorded calls"""
        return len(self.__calls)

    def print_log(self):
        """Prints the call log"""
        for i, c in enumerate(self.__calls):
            print(f"{i+1}.", format_call(c, self.__mapping))
        return self
