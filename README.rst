Connectors
==========

The *Connectors* package facilitates the writing of block-diagram-like processing networks.
For this it provides decorators for the methods of processing classes, so they can be connected to each other.
When a parameter in such a processing network is changed, the result values will also be updated automatically.
This is similar to a pipes and filters architecture, the observer pattern or streams.

This short example demonstrates the core functionality of the *Connectors* package by implementing a processing network of two sequential blocks, which double their input value:

>>> import connectors
>>>
>>> class TimesTwo:
...     def __init__(self, value=0):
...         self.__value = value
...
...     @connectors.Input("get_double")
...     def set_value(self, value):
...         self.__value = value
...
...     @connectors.Output()
...     def get_double(self):
...          return 2 * self.__value
>>>
>>> d1 = TimesTwo()                                     # create an instance that doubles its input value
>>> d2 = TimesTwo().set_value.connect(d1.get_double)    # create a second instance and connect it to the first
>>> d2.get_double()
0
>>> d1.set_value(2)
>>> d2.get_double()                                     # causes the new input value 2 to be processed by d1 and d2
8


Installation
------------

The *Connectors* package requires Python version 3.6 or later.
Python 3.5 might work, but this is not tested.

::

   pip3 install connectors

Documentation
-------------

The documentation for the *Connectors* librariy can be found on `Read the Docs <https://connectors.readthedocs.io/en/latest/>`_.


License
-------

The *Connectors* package is published under the terms and conditions of the GNU lesser general public license version 3 or later (LGPLv3+).
