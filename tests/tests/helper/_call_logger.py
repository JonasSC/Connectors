# This file is a part of the "Connectors" package
# Copyright (C) 2017-2022 Jonas Schulte-Coerne
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

import functools

__all__ = ("CallLogger", "ignore")


class Ignore:
    """A class for the singleton `ignore` value, that is used to indicate, that the parameters or
    the return value of a method call shall not be checked by the call logger."""
    def __eq__(self, other):
        return True

    def __ne__(self, other):
        return False


ignore = Ignore()


class Call:
    """A class for representing a single method call in the call log"""

    def __init__(self, instance, method_name, parameters=ignore, return_value=ignore, name_mapping=None):
        self.instance = instance
        self.method_name = method_name
        if parameters is ignore or parameters is None:
            self.parameters = ignore
        else:
            self.parameters = tuple(parameters)
        self.return_value = return_value
        self.__instance_name = self.__lookup_name(name_mapping if name_mapping else {})

    def __str__(self):
        if self.__instance_name:
            instance_name = self.__instance_name
        else:
            instance_name = f"{self.instance.__class__.__name__}({id(self.instance)})"
        parameters = "" if self.parameters is ignore else ", ".join(str(p) for p in self.parameters)
        if self.return_value is ignore:
            return f"{instance_name}.{self.method_name}({parameters})"
        else:
            return_value = self.__instance_name if self.return_value is self.instance else self.return_value
            return f"{instance_name}.{self.method_name}({parameters}) -> {return_value}"

    def __eq__(self, other):
        return (self.instance is other.instance
                and self.method_name == other.method_name
                and (self.parameters == other.parameters or other.parameters == self.parameters)           # checking the == in both directions checks, whether the parameters are ignored by one call (see. __eq__ method of Ignore)
                and (self.return_value == other.return_value or other.return_value == self.return_value))  # checking the == in both directions checks, whether the return value is ignored by one call (see. __eq__ method of Ignore)

    def __ne__(self, other):
        return not self == other

    def set_name_mapping(self, **kwargs):
        """Specifies a mapping from string variable names to instances,
        which allows for more readable debug prints and error messages.

        :param kwargs: keyword arguments: NAME=INSTANCE
        """
        new_name = self.__lookup_name(kwargs)
        if new_name:
            self.__instance_name = new_name
        return self

    def __lookup_name(self, name_mapping):
        """looks up the name of this call's instance in the given name mapping"""
        for name, instance in name_mapping.items():
            if instance is self.instance:
                return name
        return None


class CallList:
    """Manages lists of expected calls and allows to check if a given recorded
    call is expected."""

    def __init__(self, call_list, name_mapping=None):
        """
        @param call_list: a list of expected calls as tuples (INSTANCE, METHOD, VALUE),
                          where INSTANCE is the object, of which a method call is
                          expected, METHOD is the string method name and VALUE is
                          optional and can be the argument, that is expected to
                          be passed to the method.
        """
        self.__name_mapping = name_mapping
        self.__call_list = self.__parse_list(call_list)

    def __parse_list(self, call_list):
        result = []
        for item in call_list:
            if isinstance(item, (set, frozenset)):
                result.append([CallList(l, self.__name_mapping) for l in item])
            else:
                if len(item) == 2:
                    instance, method_name = item
                    parameters = ignore
                    return_value = ignore
                elif len(item) == 3:
                    instance, method_name, parameters = item
                    return_value = ignore
                elif len(item) == 4:
                    instance, method_name, parameters, return_value = item
                result.append(Call(instance=instance,
                                   method_name=method_name,
                                   parameters=parameters,
                                   return_value=return_value,
                                   name_mapping=self.__name_mapping))
        return result

    def __str__(self):
        items = []
        for item in self.__call_list:
            if isinstance(item, list):
                items.append(f"{{{', '.join(str(i) for i in item)}}}")
            else:
                items.append(str(item))
        return f"[{', '.join(items)}]"

    def check(self, call):
        """Checks if the given call is expected now."""
        if isinstance(self.__call_list[0], Call):
            result = call == self.__call_list[0]
            if result:
                self.__call_list.pop(0)
            return result
        else:
            for i, call_list in enumerate(self.__call_list[0]):
                if call_list.check(call):
                    if call_list.found():
                        del self.__call_list[0][i]
                        if not self.__call_list[0]:
                            self.__call_list.pop(0)
                    return True
        return False

    def found(self):
        """Returns True, if all expected calls in the list have already been passed to the check method."""
        return not self.__call_list

    def expected(self):
        """Returns a list of still expected calls. This is useful when generating error messages."""
        if isinstance(self.__call_list[0], Call):
            return [self.__call_list[0]]
        else:
            return functools.reduce(lambda a, b: a + b, (call_list.expected() for call_list in self.__call_list[0]))


class CallLogger:
    """Logs calls, so that the logs can be compared to expected call sequences.
    Many classes in the :mod:`testclasses` module allow to pass a call logger as a
    constructor parameter.
    """

    def __init__(self):
        self.__calls = []
        self.__name_mapping = {}

    def register_call(self, instance, method_name, parameters=ignore, return_value=ignore):
        """Is called by methods, when a call shall be logged"""
        self.__calls.append(Call(instance=instance,
                                 method_name=method_name,
                                 parameters=parameters,
                                 return_value=return_value,
                                 name_mapping=self.__name_mapping))

    def set_name_mapping(self, **kwargs):
        """Specifies a mapping from string variable names to instances,
        which allows for more readable debug prints and error messages.

        :param kwargs: keyword arguments: NAME=INSTANCE
        """
        self.__name_mapping.update(kwargs)
        for call in self.__calls:
            call.set_name_mapping(**self.__name_mapping)
        return self

    def clear(self):
        """Clears the current call log"""
        self.__calls = []
        return self

    def compare(self, call_list):
        """Compares the recorded call log to an expected call sequence.

        Calls in the call sequence are described by tuples (INSTANCE, METHOD_NAME, PARAMETERS, RETURN_VALUE).

        If the order of parts of the call sequence is not known, these parts can
        be put in a set inside the call sequence.

        :param call_list: the call sequence as a list. This list is modified by this call.
        """
        expected = CallList(call_list, name_mapping=self.__name_mapping)
        for i, call in enumerate(self.__calls, start=1):
            if expected.found():  # this means, that all calls in the expected list have been found, but there are still calls in self.__calls, that were not in the list
                raise AssertionError(f"the call of {call} was not expected")
            if not expected.check(call):
                raise AssertionError(f"expected one of the following calls:\n"
                                     f"    {[str(c) for c in expected.expected()]}\n"
                                     f"but found {call}.")
        if not expected.found():
            raise AssertionError(f"expected one of the following calls:\n"
                                 f"    {[str(c) for c in expected.expected()]}\n"
                                 f"but no calls were registered.")
        return self

    def get_number_of_calls(self):
        """Returns the number of recorded calls"""
        return len(self.__calls)

    def print_log(self):
        """Prints the call log"""
        for i, call in enumerate(self.__calls, start=1):
            print(f"{i}. {call}")
        return self
