.. _polynomial2:

Improving the polynomial implementation *(demonstrates memory saving techniques)*
=================================================================================

This tutorial shows how to reduce the memory consumption of the polynomial implementation from the :ref:`previous tutorial<polynomial1>` by disabling :ref:`caching<caching>` and using the :class:`~connectors.blocks.WeakrefProxyGenerator` class.

The problem of caching intermediate values
------------------------------------------

The :class:`Power` and :class:`Multiply` classes store references to their input parameters.
Also, because these classes are meant to be useful outside the scope of the polynomial computation, the caching of their result value is not disabled.
This leads to all intermediate results of the polynomial to remain in memory, even after the computation of the final result has finished.
Due to the caching of the final result, the intermediate results are no longer needed, once the computation has finished.

Avoiding the caching of intermediate results
--------------------------------------------

The :class:`FourierTransform` class in the *transfer function* tutorial has solved the issue of storing its input value, by deleting it in the getter method.
For classes like this, it would be sufficient to disable the :ref:`caching<caching>` of the output value, to avoid that intermediate results are stored.
But this solution is only applicable to classes with no more than one input and one output connector, which is not the case with the :class:`Power` and :class:`Multiply` classes.

To solve this problem in use cases like this, the *Connectors* package provides the :class:`~connectors.blocks.WeakrefProxyGenerator` class, that stores a strong reference to its input value, propagates a weak reference to it through its output connector.
In order to delete the strong reference, once it is no longer needed, this class also provides an input connector, that deletes the strong reference, once the result of the following processing step has been computed.
In combination with disabling the :ref:`caching<caching>` of the output connector, that produced the input value for the :class:`~connectors.blocks.WeakrefProxyGenerator` instance, this causes the input value to be garbage collected.

Block diagram of the improved polynomial implementation
-------------------------------------------------------

The block diagram of a polynomial implementation, that uses :class:`~connectors.blocks.WeakrefProxyGenerator`\s, is shown below.
The :class:`~connectors.blocks.WeakrefProxyGenerator`\s are highlighted in red.
Note the backwards dependencies of the :class:`~connectors.blocks.WeakrefProxyGenerator`\s on the output of processing classes, by which they are followed.
This is a feedback loop to tell the :class:`~connectors.blocks.WeakrefProxyGenerator`\s, that they can delete the strong reference to their input values.

.. graphviz::

   digraph Polynomial{
      rankdir=LR;
      x -> x0 -> wp0 -> a -> wm0 -> sum -> y;
      a -> wp0;
      sum -> wm0;
      x -> x1 -> wp1 -> b -> wm1 -> sum;
      b -> wp1;
      sum -> wm1;
      x -> x2 -> wp2 -> c -> wm2 -> sum;
      c -> wp2;
      sum -> wm2;
      x -> x3 -> wp3 -> d -> wm3 -> sum;
      d -> wp3;
      sum -> wm3;
      x -> xn -> wpn -> n -> wmn -> sum;
      n -> wpn;
      sum -> wmn;
      x [label="x", shape=parallelogram];
      x0 [label="1", shape=box];
      wp0 [label="wr", shape=box, color=red];
      a [label="a", shape=box];
      wm0 [label="wr", shape=box, color=red];
      x1 [label="(·)", shape=box];
      wp1 [label="wr", shape=box, color=red];
      b [label="·b", shape=box];
      wm1 [label="wr", shape=box, color=red];
      x2 [label="(·)²", shape=box];
      wp2 [label="wr", shape=box, color=red];
      c [label="·c", shape=box];
      wm2 [label="wr", shape=box, color=red];
      x3 [label="(·)³", shape=box];
      wp3 [label="wr", shape=box, color=red];
      d [label="·d", shape=box];
      wm3 [label="wr", shape=box, color=red];
      xn [label="...", shape=box];
      wpn [label="...", shape=box, color=red];
      n [label="...", shape=box];
      wmn [label="...", shape=box, color=red];
      sum [label="+"];
      y [label="y", shape=parallelogram];
      {rank=same; x0, x1, x2, x3, xn};
      {rank=same; wp0, wp1, wp2, wp3, wpn};
      {rank=same; a, b, c, d, n};
      {rank=same; wm0, wm1, wm2, wm3, wmn};
   }


Implementation of the improved polynomial
-----------------------------------------

First, the building blocks of the polynomial have to be defined.
They are identical to the ones from the :ref:`previous tutorial<polynomial1>` (and they are only shown here, so the implementation of the improved polynomial can be tested with :mod:`doctest`).

>>> import numpy
>>> import connectors
>>>
>>> class Power:
...     def __init__(self, base=0, exponent=1):
...         self.__base = base
...         self.__exponent = exponent
...
...     @connectors.Output()
...     def get_result(self):
...         return numpy.power(self.__base, self.__exponent)
...
...     @connectors.Input("get_result")
...     def set_base(self, base):
...         self.__base = base
...
...     @connectors.Input("get_result")
...     def set_exponent(self, exponent):
...         self.__exponent = exponent
>>>
>>> class Multiply:
...     def __init__(self, factor1=0, factor2=0):
...         self.__factor1 = factor1
...         self.__factor2 = factor2
...
...     @connectors.Output()
...     def get_result(self):
...         return numpy.multiply(self.__factor1, self.__factor2)
...
...     @connectors.Input("get_result")
...     def set_factor1(self, factor):
...         self.__factor1 = factor
...
...     @connectors.Input("get_result")
...     def set_factor2(self, factor):
...         self.__factor2 = factor
>>>
>>> class Sum:
...     def __init__(self):
...         self.__summands = connectors.MultiInputData()
...
...     @connectors.Output()
...     def get_result(self):
...         return sum(tuple(self.__summands.values()))
...
...     @connectors.MultiInput("get_result")
...     def add_summand(self, summand):
...         return self.__summands.add(summand)
...
...     @add_summand.remove
...     def remove_summand(self, data_id):
...         del self.__summands[data_id]

The implementation of the :class:`Polynomial` class is conceptually similar to that from the :ref:`previous tutorial<polynomial1>`.
But it contains extra lines of code for disabling the :ref:`caching<caching>` of the output connectors and for inserting the :class:`~connectors.blocks.WeakrefProxyGenerator` instances in the processing chain.

>>> class Polynomial:
...     def __init__(self, coefficients):
...         self.__powers = []
...         self.__sum = Sum()
...         for e, c in enumerate(coefficients):
...             power = Power(exponent=e)
...             self.__powers.append(power)
...             power.get_result.set_caching(False)
...             power_weakref = connectors.blocks.WeakrefProxyGenerator().input.connect(power.get_result)
...             weighting = Multiply(factor2=c).set_factor1.connect(power_weakref.output)
...             weighting.get_result.set_caching(False)
...             weighting.get_result.connect(power_weakref.delete_reference)
...             weighting_weakref = connectors.blocks.WeakrefProxyGenerator().input.connect(weighting.get_result)
...             weighting_weakref.output.connect(self.__sum.add_summand)
...             self.__sum.get_result.connect(weighting_weakref.delete_reference)
...
...     @connectors.MacroInput()
...     def set_variable(self):
...         for p in self.__powers:
...             yield p.set_base
...
...     @connectors.MacroOutput()
...     def get_result(self):
...         return self.__sum.get_result


Using the implementation of the polynomial
------------------------------------------

The usage of the :class:`Polynomial` is identical to that from the :ref:`previous tutorial<polynomial1>`.

>>> polynomial = Polynomial(coefficients=(5.0, -3.0, 2.0))  # y = 2*x**2 - 3*x + 5
>>> polynomial.set_variable(4.0).get_result()               # compute the polynomial for a scalar
25.0
>>> polynomial.set_variable([-2, -1, 0, 1, 2]).get_result() # compute the polynomial for elements of an array
array([19., 10.,  5.,  4.,  7.])
