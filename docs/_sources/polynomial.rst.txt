Tutorial: Implementing a polynomial (demonstrates macros and memory saving techniques)
======================================================================================

This tutorial shall demonstrate the use of macros and the use of the :class:`connectors.WeakrefProxyGenerator` class in order to avoid the caching intermediate results in the setters.
For this, the computation of polynomial is implemented as a processing network, that is encapsulated in a macro class.


The block diagram representation of a polynomial
------------------------------------------------

A polynomial is a weighted sum of powers of its input variable:

.. math::

   y = a + b x + c x^2 + d x^3 + ...

This can be organized in a block diagram:

.. graphviz::

   digraph Polynomial{
      rankdir=LR;
      x -> x0 -> a -> sum -> y;
      x -> x1 -> b -> sum;
      x -> x2 -> c -> sum;
      x -> x3 -> d -> sum;
      x -> xn -> n -> sum;
      x [label="x", shape=parallelogram];
      x0 [label="1", shape=box];
      a [label="a", shape=box];
      x1 [label="(·)", shape=box];
      b [label="·b", shape=box];
      x2 [label="(·)²", shape=box];
      c [label="·c", shape=box];
      x3 [label="(·)³", shape=box];
      d [label="·d", shape=box];
      xn [label="...", shape=box];
      n [label="...", shape=box];
      sum [label="+"];
      y [label="y", shape=parallelogram];
      {rank=same; x0, x1, x2, x3, xn};
      {rank=same; a, b, c, d, n};
   }


Implementing the basic building blocks: power, multiplication and summation
---------------------------------------------------------------------------

As seen in the block diagram, the basic building blocks can be implemented with three processing classes:
   - one that computes a specified power of its input value
   - one that multiplies its input value with a given factor
   - one that sums up all its input values

For this task, it would be sufficient, if the exponent of the power and the weighting factor of the multiplication, were constants, that are specified through the constructor of the class.
But assuming, that a project, in which polynomials are computed, would also benefit from processing classes, that compute arbitrary powers and products, the following, more general implementations are used in this tutorial.

>>> import numpy
>>> import connectors

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


Avoiding the caching of intermediate results
--------------------------------------------

The :class:`Power` and :class:`Multiply` classes store references to their input parameters.
Also, because these classes are meant to be useful outside the scope of the polynomial computation, the caching of their result value is not disabled.
This leads to all intermediate results of the polynomial to remain in memory, even after the computation of the final result has finished.
Due to the caching of the final result, the intermediate results are no longer needed, once the computation has finished.

The :class:`FourierTransform` class in the *transfer function* tutorial has solved the issue of storing its input value, by deleting it in the getter method.
This solution is only applicable to classes with not more than one input and one output connector, which is not the case with the :class:`Power` and :class:`Multiply` classes.

To solve this problem for use cases like this, the *Connectors* package provides the :class:`~connectors.WeakrefProxyGenerator` class, that stores a strong reference to its input value, propagates a weak reference to it through its output connector and provides an input connector, that deletes the strong reference, once the result of the following processing step has been computed.
In combination with disabling the caching of the output connector, that produced the input value for the :class:`~connectors.WeakrefProxyGenerator` instance, this causes the input value to be garbage collected.

The block diagram of a polynomial implementation, that uses :class:`~connectors.WeakrefProxyGenerator`\s, is shown below.
The :class:`~connectors.WeakrefProxyGenerator`\s are highlighted in red.
Note the backwards dependencies of the :class:`~connectors.WeakrefProxyGenerator`\s on the output of processing classes, by which they are followed.
This is a feedback loop to tell the :class:`~connectors.WeakrefProxyGenerator`\s, that they can delete the strong reference to their input values.

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

The following class implements the computation of a polynomial, by encapsulating the required processing chain and exporting the input and output connectors via macro connectors.
It accepts a sequence of weighting factors (:math:`a`, :math:`b`, :math:`c`, :math:`d`, ... in the block diagram) and instantiates the required processing classes in the ``for``-loop.

>>> class Polynomial:
...     def __init__(self, coefficients):
...         self.__powers = []
...         self.__sum = Sum()
...         for e, c in enumerate(coefficients):
...             power = Power(exponent=e)
...             self.__powers.append(power)
...             power.get_result.set_caching(False)
...             power_weakref = connectors.WeakrefProxyGenerator().set_data.connect(power.get_result)
...             weighting = Multiply(factor2=c).set_factor1.connect(power_weakref.get_weakref_proxy)
...             weighting.get_result.set_caching(False)
...             weighting.get_result.connect(power_weakref.delete_reference)
...             weighting_weakref = connectors.WeakrefProxyGenerator().set_data.connect(weighting.get_result)
...             weighting_weakref.get_weakref_proxy.connect(self.__sum.add_summand)
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

Note that the methods, that are decorated to become macro connectors merely return the connectors of the internal processing chain.
These methods will be replaced by macro connectors, that behave like setter or getter methods, so the behavior of macro connectors differs significantly from that of the methods, which they replace.


Using the implementation of the polynomial
------------------------------------------

The :class:`Polynomial` class can now be instantiated and used for computations.

>>> polynomial = Polynomial(coefficients=(5.0, -3.0, 2.0))  # y = 2*x**2 - 3*x + 5
>>> polynomial.set_variable(4.0).get_result()               # compute the polynomial for a scalar
25.0
>>> polynomial.set_variable([-2, -1, 0, 1, 2]).get_result() # compute the polynomial for elements of an array
array([ 19.,  10.,   5.,   4.,   7.])

Note how the :meth:`set_variable` and :meth:`get_result` methods work as actual setter and getter methods, rather than returning connectors and not accepting any parameters.
The :meth:`get_result` input connector of the polynomial basically mimics the :meth:`get_result` connector of the summation.
Since the macro input connector represents multiple connectors, all operations on it will be performed with each of these connectors:

* setting a value of a macro input connector, passes that value to all represented connectors.
* changing the behavior of a macro input connector applies the same changes to all represented connectors.
* connecting an output connector to a macro input connector connects that output to all represented connectors.

Also note, that macro input connectors return the instance of the processing class to which they belong, so that setting a parameter and retrieving the updated result can be programmed in one line.
