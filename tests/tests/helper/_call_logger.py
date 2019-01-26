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

"""Contains a class for logging calls and comparing that log to a given call sequence"""

import collections

__all__ = ("CallLogger",)

Call = collections.namedtuple(typename="Call", field_names=("class_", "method", "identifier", "value"))


class CallLogger:
    """Logs calls, so that the logs can be compared to expected call sequences.
    Many classes in the :mod:`testclasses` module allow to pass a call logger as a
    constructor parameter.
    """

    def __init__(self):
        self.__calls = []

    def register_call(self, instance, methodname, value):
        """Is called by methods, when a call shall be logged"""
        self.__calls.append(Call(class_=instance.__class__.__name__,
                                 method=methodname,
                                 identifier=instance.get_identifier(),
                                 value=value))

    def clear(self):
        """Clears the current call log"""
        self.__calls = []

    def compare(self, call_list):
        """Compares the recorded call log to an expected call sequence.

        Calls in the call sequence are described by tuples (INSTANCE, METHOD_NAME, PARAMETER).

        If the order of parts of the call sequence is not known, these parts can
        be put in a set inside the call sequence.

        :param call_list: the call sequence as a list. This list is modified by this call.
        """
        index = 0
        while call_list:
            assert index < len(self.__calls)
            call_description = call_list.pop(0)
            if isinstance(call_description, set):
                old_set = call_description
                new_set = set()
                found = False
                while old_set:
                    call_sublist = old_set.pop()
                    if isinstance(call_sublist[0], set):
                        raise NotImplementedError("modelling concurrency inside a concurrent branch is not supported")
                    if self.__check_call(call=self.__calls[index], call_description=call_sublist[0]):
                        found = True
                        index += 1
                        if len(call_sublist) > 1:
                            new_set.add(call_sublist[1:])
                    else:
                        new_set.add(call_sublist)
                if new_set:
                    call_list.insert(0, new_set)    # keep the set at the beginning of the call list as long as it is not empty
                assert found
            else:
                assert self.__check_call(self.__calls[index], call_description)
                index += 1
        assert index == len(self.__calls)

    def get_number_of_calls(self):
        """Returns the number of recorded calls"""
        return len(self.__calls)

    def print_log(self):
        """Prints the call log"""
        for i, c in enumerate(self.__calls):
            print(f"{i}.", c.class_, c.method, c.identifier, c.value)

    def __check_call(self, call, call_description):  # pylint: disable=no-self-use; pylint shall not complain, that this is a private method rather than a function
        """Is used internally to compare an element from the call log to an element
        from the call sequence.
        """
        if call.class_ != call_description[0].__class__.__name__:
            return False
        if isinstance(call[1], str):
            if call.method != call_description[1]:
                return False
        else:
            if call.method != call_description[1].__name__:
                return False
        if call.identifier != call_description[0].get_identifier():
            return False
        if len(call_description) > 3:
            if call.value != call_description[3]:
                return False
        return True
