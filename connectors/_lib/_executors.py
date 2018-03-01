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

"""Contains the :class:`Executor` classes, that implement the parallelization of
computations in separate threads or processes.
Only the factory function for creating :class:`Executor` instances is exported.
"""

# pylint: disable=wrong-spelling-in-comment,wrong-spelling-in-docstring;    for some reason the spell checker does not recognize the word "CPU"

import asyncio
import concurrent.futures
import os
from connectors.connectors import Connector
from ._flags import Parallelization

__all__ = ("executor",)


def executor(threads=None, processes=0):
    """A factory function for creating :class:`Executor` objects.
    Executors define how the computations of a processing chain are parallelized
    by executing them in separate threads or processes. This function creates an
    executor and configures it to use at maximum the given number of threads or
    processes.

    :param threads: an integer number of threads or None to determine the number
                    automatically. 0 disables the thread based parallelization.
    :param processes: an integer number of processes or None to determine the number
                      automatically (in this case, the number of CPU cores will
                      be taken). 0 disables the process based parallelization.
    """
    if threads == 0:
        if processes == 0:
            return SequentialExecutor()
        else:
            return MultiprocessingExecutor(number_of_processes=processes)
    else:
        if processes == 0:
            return ThreadingExecutor(number_of_threads=threads)
        else:
            return ThreadingMultiprocessingExecutor(number_of_threads=threads, number_of_processes=processes)


def _redeployed_method(method_name, reduced_instance, *args, **kwargs):
    """A helper function, that is passed to the separate processes for executing
    the given method.
    This function is necessary, because objects with connectors cannot be pickled,
    so that their methods cannot be passed to a process directly. Instead only the
    relevant data is serialized and passed to the process, where this function
    unwraps this data and executes the method.
    :param method_name: the string name of the method that shall be executed
    :param reduced_instance: a tuple with the class, in which the method is defined
                             and the ``__dict__`` of the instance of which the
                             method shall be executed
    :param *args, **kwargs: arguments for the method
    """
    class_, state = reduced_instance
    instance = class_.__new__(class_)
    instance.__dict__.update(state)
    method = getattr(instance, method_name)
    return method(*args, **kwargs)


class Executor:
    """a base class for managing the event loop and the execution in threads or processes."""
    def __init__(self):
        self._loop = None   # will be initialized in run_until_complete

    async def run_method(self, parallelization, method, instance, *args, **kwargs):
        """Abstract method, whose overrides shall execute the given method.
        The parallelization shall be implemented in this method.
        :param parallelization: a flag of :class:`connectors.Parallelization`, that
                                specifies how the given method can be parallelized
        :param method: the unbound method, that shall be executed
        :param instance: the instance of which the method shall be executed
        :param *args, **kwargs: arguments for the method
        """
        raise NotImplementedError("this method should have been overridden in a derived class")

    def run_until_complete(self, future):
        """a wrapper for the event loop's :meth:`run_until_complete` from :mod:`asyncio`.
        Executes the given future in an :mod:`asyncio` event loop.
        :param future: e.g. a coroutine or a sequence of tasks
        """
        self._loop = asyncio.get_event_loop()
        return self._loop.run_until_complete(future)

    def create_task(self, coro):
        """a wrapper for the event loop's :meth:`create_task` from :mod:`asyncio`.
        Creates a task, that will be executed in the event loop.
        :param coro: a coroutine
        """
        return self._loop.create_task(coro)


class SequentialExecutor(Executor):
    """An executor class, that executes everything sequentially."""
    async def run_method(self, parallelization, method, instance, *args, **kwargs):
        """Executes the given method sequentially.
        :param parallelization: a flag of :class:`connectors.Parallelization`, that
                                specifies how the given method can be parallelized
        :param method: the unbound method, that shall be executed
        :param instance: the instance of which the method shall be executed
        :param *args, **kwargs: arguments for the method
        """
        return method(instance, *args, **kwargs)


class ThreadingExecutor(Executor):
    """An executor class, that can parallelize computations with threads."""
    def __init__(self, number_of_threads):
        """
        :param number_of_threads: the maximum number of threads, that shall be
                                  created, or None to determine this number
                                  automatically.
        """
        Executor.__init__(self)
        self.__number_of_threads = number_of_threads
        self.__executor = None  # will be initialized in run_until_complete

    async def run_method(self, parallelization, method, instance, *args, **kwargs):
        """Executes the given method in a thread if possible and falls back to
        sequential execution if not.
        :param parallelization: a flag of :class:`connectors.Parallelization`, that
                                specifies how the given method can be parallelized
        :param method: the unbound method, that shall be executed
        :param instance: the instance of which the method shall be executed
        :param *args, **kwargs: arguments for the method
        """
        if parallelization == Parallelization.SEQUENTIAL:
            return method(instance, *args, **kwargs)
        else:
            return await self._loop.run_in_executor(self.__executor, method, instance, *args, **kwargs)

    def run_until_complete(self, future):
        """a wrapper for the event loop's :meth:`run_until_complete` from :mod:`asyncio`.
        Executes the given future in an :mod:`asyncio` event loop.
        :param future: e.g. a coroutine or a sequence of tasks
        """
        if self.__number_of_threads is None:            # the default number of workers for the ThreadPoolExecutor is 5x the CPU count, which is meant for I/O bound tasks.
            self.__number_of_threads = os.cpu_count()   # This class is meant for CPU work, so the number of threads should be lower to reduce context switching overhead.
        self.__executor = concurrent.futures.ThreadPoolExecutor(max_workers=self.__number_of_threads)
        result = Executor.run_until_complete(self, future)
        self.__executor.shutdown()
        return result


class MultiprocessingExecutor(Executor):
    """An executor class, that can parallelize computations with processes."""
    def __init__(self, number_of_processes):
        """
        :param number_of_processes: the maximum number of processes, that shall be
                                    created, or None to determine this number
                                    automatically (in this case, the number of CPU
                                    cores will be taken).
        """
        Executor.__init__(self)
        self.__number_of_processes = number_of_processes
        self.__executor = None  # will be initialized in run_until_complete

    async def run_method(self, parallelization, method, instance, *args, **kwargs):
        """Executes the given method in a process if possible and falls back to
        sequential execution if not.
        :param parallelization: a flag of :class:`connectors.Parallelization`, that
                                specifies how the given method can be parallelized
        :param method: the unbound method, that shall be executed
        :param instance: the instance of which the method shall be executed
        :param *args, **kwargs: arguments for the method
        """
        if parallelization == Parallelization.PROCESS:
            class_ = instance.__class__
            state = instance.__dict__.copy()
            to_remove = []
            for a in state:
                if isinstance(state[a], Connector):
                    to_remove.append(a)
            for a in to_remove:
                del state[a]
            reduced_instance = (class_, state)
            return await self._loop.run_in_executor(self.__executor,
                                                    _redeployed_method,
                                                    method.__name__,
                                                    reduced_instance,
                                                    *args, **kwargs)
        else:
            return method(instance, *args, **kwargs)

    def run_until_complete(self, future):
        """a wrapper for the event loop's :meth:`run_until_complete` from :mod:`asyncio`.
        Executes the given future in an :mod:`asyncio` event loop.
        :param future: e.g. a coroutine or a sequence of tasks
        """
        self.__executor = concurrent.futures.ProcessPoolExecutor(max_workers=self.__number_of_processes)
        result = Executor.run_until_complete(self, future)
        self.__executor.shutdown()
        return result


class ThreadingMultiprocessingExecutor(Executor):
    """An executor class, that can parallelize computations with both threads and processes."""
    def __init__(self, number_of_threads, number_of_processes):
        """
        :param number_of_threads: the maximum number of threads, that shall be
                                  created, or None to determine this number
                                  automatically.
        :param number_of_processes: the maximum number of processes, that shall be
                                    created, or None to determine this number
                                    automatically (in this case, the number of CPU
                                    cores will be taken).
        """
        Executor.__init__(self)
        self.__number_of_threads = number_of_threads
        self.__number_of_processes = number_of_processes
        self.__thread_executor = None   # will be initialized in run_until_complete
        self.__process_executor = None  # will be initialized in run_until_complete

    async def run_method(self, parallelization, method, instance, *args, **kwargs):
        """Executes the given method in a process if possible and falls back to
        threaded and then sequential execution if not.
        :param parallelization: a flag of :class:`connectors.Parallelization`, that
                                specifies how the given method can be parallelized
        :param method: the unbound method, that shall be executed
        :param instance: the instance of which the method shall be executed
        :param *args, **kwargs: arguments for the method
        """
        if parallelization == Parallelization.SEQUENTIAL:
            return method(instance, *args, **kwargs)
        elif parallelization == Parallelization.THREAD:
            return await self._loop.run_in_executor(self.__thread_executor, method, instance, *args, **kwargs)
        else:
            class_ = instance.__class__
            state = instance.__dict__.copy()
            to_remove = []
            for a in state:
                if isinstance(state[a], Connector):
                    to_remove.append(a)
            for a in to_remove:
                del state[a]
            reduced_instance = (class_, state)
            return await self._loop.run_in_executor(self.__process_executor,
                                                    _redeployed_method,
                                                    method.__name__,
                                                    reduced_instance,
                                                    *args, **kwargs)

    def run_until_complete(self, future):
        """a wrapper for the event loop's :meth:`run_until_complete` from :mod:`asyncio`.
        Executes the given future in an :mod:`asyncio` event loop.
        :param future: e.g. a coroutine or a sequence of tasks
        """
        if self.__number_of_threads is None:            # the default number of workers for the ThreadPoolExecutor is 5x the CPU count, which is meant for I/O bound tasks.
            self.__number_of_threads = os.cpu_count()   # This class is meant for CPU work, so the number of threads should be lower to reduce context switching overhead.
        self.__thread_executor = concurrent.futures.ThreadPoolExecutor(max_workers=self.__number_of_threads)
        self.__process_executor = concurrent.futures.ProcessPoolExecutor(max_workers=self.__number_of_processes)
        result = Executor.run_until_complete(self, future)
        self.__thread_executor.shutdown()
        self.__process_executor.shutdown()
        return result
