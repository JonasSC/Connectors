.. _multiplexer2:

Improving the multiplexer *(demonstrates avoiding unneccessary computations with conditional input connectors)*
===============================================================================================================

The multiplexer from the :ref:`previous tutorial<multiplexer1>` can cause unnecessary computations in certain constellations.
This tutorial shows how to avoid these computations by specifying conditions for the propagation of value changes of the input connector.

Situations, in which unneccessary computations occur
----------------------------------------------------

If any input of the simple multiplexer from the :ref:`previous tutorial<multiplexer1>` receives value update, this update will be propagated down the processing chain.
In case, the updated input is not currently selected, the output of the multiplexer will produce the same value as before the value update, which causes an unnecessary recomputation of the processing chain.

In order to avoid these unnecessary computations, a means to interrupt the processing of the chain is required.
The (multi) input connectors have a feature to specify conditions on the propagation of value changes, which can be used for this purpose.

Conditions for the input connectors
-----------------------------------

Inputs and multi-inputs have two decorators for methods, which specify the conditional propagation of value changes.
For a more detailed explanation of the *announcement* and *notification* phases of the propagation of value changes, it is recommended read the section about :ref:`lazy execution<lazy_execution>`.

* The method decorated with :obj:`~connectors.Input.announce_condition` is evaluated to check if the announcement of a value change shall be propagated.
  If the condition evaluates to ``False``, processors further down the processing chain will not be informed about the pending value change, which means, that they will not request this value change to be performed.
  In case all endpoints, which request this value update, (such as manually called output connectors or non-lazy inputs) are behind the conditional input in the processing chain, this means, that also the connectors, which are before the conditional input, are not executed.
* The method decorated with :obj:`~connectors.Input.notify_condition` is evaluated after executing the input connector to check if the observing output connectors shall be notified about the changed value.
  If this evaluation yields ``False``, the pending announcements are canceled, so that downstream connectors do not request an updated value.

Implementing a conditional multi-input connector for the multiplexer
--------------------------------------------------------------------

Choosing condition for the multiplexer's input is trivial.
It should simply check, if the changed input is the one, that is currently selected.
The harder choice is to decide whether to use an :obj:`~connectors.Input.announce_condition` or a :obj:`~connectors.Input.notify_condition`.

At first glance, the :obj:`~connectors.Input.announce_condition` is tempting, because it also avoids the computations, that produce the input value, which is not selected by the multiplexer.
Sadly, these computations cannot generally be avoided, because it is always possible, that the changed value is selected by the multiplexer at a later point in time.
In this case, the output connector of the multiplexer must have been informed about the pending value change, in order to request that value to be updated.
And this announcement has not been sent, if the :obj:`~connectors.Input.announce_condition` evaluated to ``False``.

Therefore, the multiplexer's input must specify a :obj:`~connectors.Input.notify_condition`.

An improved implementation of the multiplexer
---------------------------------------------

>>> import connectors

The following implementation of the improved multiplexer is almost identical to the ``SimpleMultiplexer`` from the :ref:`previous tutorial<multiplexer1>`.
It is only enhanced by the :meth:`~Multiplexer.__input_condition` method, which is decorated to become the :meth:`~Multiplexer.input` method's :obj:`~connectors.Input.notify_condition`.

>>> class Multiplexer:
...     def __init__(self, selector=None):
...         self.__selector = selector
...         self.__data = connectors.MultiInputData()
...
...     @connectors.Output()
...     def output(self):
...         if self.__selector in self.__data:
...             return self.__data[self.__selector]
...         else:
...             return None
...
...     @connectors.Input("output")
...     def select(self, selector):
...         self.__selector = selector
...
...     @connectors.MultiInput("output")
...     def input(self, data):
...         return self.__data.add(data)
...
...     @input.remove
...     def remove(self, data_id):
...         del self.__data[data_id]
...
...     @input.replace
...     def replace(self, data_id, data):
...         self.__data[data_id] = data
...
...     @input.notify_condition
...     def __input_condition(self, data_id, value):
...        return data_id == self.__selector

In order to test and demonstrate the avoidance of unnecessary computations, the following test class is implemented:

>>> class Tester:
...     @connectors.Input(laziness=connectors.Laziness.ON_ANNOUNCE)
...     def input(self, value):
...         print("Tester received value:", repr(value))

It has a non-lazy input, which requests the updated value as soon as an update is announced.
And whenever it receives a new value, it prints a message.

In the following test set up, two :class:`~connectors.blocks.Passthrough` instances are connected to the inputs of a multiplexer, while a :class:`Tester` instance is connected to its output.
It is now expected, that the tester prints a message, whenever the selected input of the multiplexer changes its value, while it remains silent, when there is a value change in a not-selected input.

>>> source1 = connectors.blocks.Passthrough("value 1")
>>> source2 = connectors.blocks.Passthrough("value 2")
>>> multiplexer = Multiplexer()
>>> tester = Tester()
>>>
>>> _ = source1.output.connect(multiplexer.input[1])
>>> _ = source2.output.connect(multiplexer.input[2])
>>> _ = multiplexer.output.connect(tester.input)

Of course, selecting an input causes the output to be updated, so a message from the tester is expected.

>>> multiplexer.select(1)
Tester received value: 'value 1'

When input `1` is selected, a change of that input's value shall also trigger a message from the tester.

>>> _ = source1.input("new value 1")
Tester received value: 'new value 1'

But since input `2` is not selected, the tester is not invoked when the value of that input is updated.

>>> _ = source2.input("new value 2")
