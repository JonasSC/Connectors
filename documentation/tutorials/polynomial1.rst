.. _polynomial1:

Implementing a polynomial *(demonstrates the encapsulation of a processing network in a single class with macro connectors)*
============================================================================================================================

This tutorial demonstrates the use of the :class:`~connectors.MacroInput` and :class:`~connectors.MacroOutput` decorators to encapsulate the processing network for computing a polynomial in a single class.

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
      y [label="y", shape=trapezium];
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


Implementing the polynomial
---------------------------

The following class implements the computation of a polynomial, by encapsulating the required processing chain and exporting the input and output connectors via macro connectors.
It accepts a sequence of weighting factors (:math:`a`, :math:`b`, :math:`c`, :math:`d`, ... in the block diagram) and instantiates the required processing classes in the ``for``-loop.

>>> class Polynomial:
...     def __init__(self, coefficients):
...         self.__powers = []
...         self.__sum = Sum()
...         for e, c in enumerate(coefficients):
...             power = Power(exponent=e)
...             weighting = Multiply(factor2=c).set_factor1.connect(power.get_result)
...             weighting.get_result.connect(self.__sum.add_summand)
...             self.__powers.append(power)
...
...     @connectors.MacroInput()
...     def set_variable(self):
...         for p in self.__powers:
...             yield p.set_base
...
...     @connectors.MacroOutput()
...     def get_result(self):
...         return self.__sum.get_result

Each iteration of the ``for``-loop in the constructor generates one of the parallel branches, that are shown in the block diagram.
The input of each branch, which is a :meth:`~Power.set_base` connector, is stored in the :attr:`~Polynomial.__powers` list.
These input connectors are exported to the interface of the :class:`Polynomial` class through the :meth:`~Polynomial.set_variable` macro input method.

Storing the output connector of each branch is not necessary, since they are all connected to the summation block.
The output of the summation is exported to the interface of the :class:`Polynomial` class through the :meth:`~Polynomial.get_result` macro output method.

Note that the methods, that are decorated to become macro connectors, merely return the connectors of the internal processing chain.
These methods will be replaced by macro connectors, that behave like setter or getter methods, so the behavior of macro connectors differs significantly from that of the methods, which they replace.


Using the implementation of the polynomial
------------------------------------------

The :class:`Polynomial` class can now be instantiated and used for computations.

>>> polynomial = Polynomial(coefficients=(5.0, -3.0, 2.0))  # y = 2*x**2 - 3*x + 5
>>> polynomial.set_variable(4.0).get_result()               # compute the polynomial for a scalar
25.0
>>> polynomial.set_variable([-2, -1, 0, 1, 2]).get_result() # compute the polynomial for elements of an array
array([19., 10.,  5.,  4.,  7.])

Note how the :meth:`set_variable` and :meth:`get_result` methods work as actual setter and getter methods, rather than returning connectors and not accepting any parameters.
The :meth:`get_result` output connector of the polynomial basically mimics the :meth:`get_result` connector of the summation.
Since the macro input connector represents multiple connectors, all operations on it will be performed with each of these connectors:

* setting a value of a macro input connector, passes that value to all represented connectors.
* changing the behavior of a macro input connector applies the same changes to all represented connectors.
* connecting an output connector to a macro input connector connects that output to all represented connectors.

Also note, that macro input connectors return the instance of the processing class to which they belong, so that setting a parameter and retrieving the updated result can be programmed in one line.
