Tutorial: Measuring a transfer function (demonstrates the core functionalities)
===============================================================================

This tutorial walks through a simple example of determining a transfer function with processing objects, that are connected with the functionalities of the *Connectors* package.

What's a transfer function
--------------------------

A transfer function describes, how a linear, time-invariant system amplifies and delays the frequency components of its input signal.
Examples of such systems are equalizers of HiFi systems, which allow to tweak the system's sound by boosting or attenuating certain frequency regions.
Or radio tuners, which supress all frequencies except for the one of the channel, that shall be received.
The reflections and reverberations of a concert hall, which a listener experiences when attending an event there, can also be described by a transfer function.

The transfer function of a system can be measured by sending a known input signal into the system and recording its response.
After that, the spectrum of this response has to be divided by the spectrum of the input signal.
Think of this as of compensating for a bias of the input signal, which might excite certain frequencies at a higher level than others.
If this is the case, the recorded response will also have an exaggerated amount of these frequency components, which is not due them being boosted by the system, but due to a biased excitation.
The divison normalizes the response by attenuating the frequency components, that had been exaggerated in the excitation signal.

Of course, the exctiation signal has to excite all frequencies, at which the system shall be modeled.
Otherwise, the division will divide by zero and the resulting transfer function will be invalid at the non-excited frequencies.

For more background on transfer functions, you can read the following Wikipedia articles (sorted in increasing order of theoretical complexity):
   - `Frequency response <https://en.wikipedia.org/wiki/Frequency_response>`_
   - `Transfer function <https://en.wikipedia.org/wiki/Transfer_function>`_
   - `Linear time-invariant theory <https://en.wikipedia.org/wiki/Linear_time-invariant_theory>`_

The following block diagram shows the computation steps for determining the transfer function of a system:

.. graphviz::

   digraph Measurement{
      rankdir=LR;
      generator -> system -> fft1 -> division -> plot;
      generator -> fft2 -> division;
      generator [label="Signal generator", shape=hexagon];
      system [label="{|System|}", shape=record, color=red];
      fft1 [label="FFT 1", shape=box, color=blue];
      division [label="÷", shape=box, color=blue];
      fft2 [label="FFT 2", shape=box, color=blue];
      plot [label="Plot", shape=parallelogram];
      {rank=same; fft1, fft2};
   }

First, the excitation signal is created in *Signal generator*.
In this tutorial, a linear sweep is used, which is a sine wave, which continuously increases its frequency over time, thus exciting all the frequencies at which the system shall be modeled.
The sweep is used, because it is mathematically well defined, easy to implement and for demonstrating what will happen, if the frequency range of the excitation signal is limited.
For the purpose of measuring a transfer function, other signals such as noise or maximum length sequences are also suitable.

The generated excitation signal is fed into the *System*.
The spectrum of the system's response is computed by transforming the response to the frequency domain with the help of the fast fourier transform in block *FFT 1*.
Meanwhile, the spectrum of the excitation signal is computed by the block *FFT 2*.
The resulting transfer function is computed by the division *÷* and displayed by the *Plot*.


Define a system, of which the tranfer function shall be measured
----------------------------------------------------------------

For reducing the lines of code for this tutorial, the system, that shall be analyzed by measuring its transfer function, is modeled with its impulse response.
The impulse response is mathematically connected to the transfer function by the (inverse) fourier transform.

.. graphviz::

   digraph ImpulseResponse{
      rankdir=LR;
      ir -> fft -> tf -> ifft -> ir;
      ir [label="impulse response", shape=hexagon];
      fft [label="Fourier transform", shape=box];
      tf [label="transfer function", shape=hexagon];
      ifft [label="inverse Fourier transform", shape=box];
      {rank=same; fft, ifft};
   }

The following code implements a class for defining a linear time-invariant system.
It requires an impulse response as constructor parameter, in order to define the system's behavior.
Furthermore it has a setter and a getter method for passing the excitation signal and retrieving the response.

.. literalinclude:: ressources/transfer_function.py
   :language: python
   :pyobject: LinearSystem

The setter method :meth:`set_input` is decorated to become an input connector, so that the output of the generator of the excitation signal can be connected to it.
Note that the name of the getter method :meth:`get_output` is passed as a parameter to the input decorator.
This models the dependency of the getter's return value on whether the setter has been called.
So whenever a new value is passed to the setter, the getter is notified, that it can produce a new result.

The getter method :meth:`get_output` is decorated to become an output connector.
Note that this is the method, that actually does the expensive computation, while the setter only stores the received parameter.
This is a recommended practice when using the *Connectors* package, since the lazy execution and the caching capability of the output connectors can avoid, that these computations are performed unnecessarily.


Generate a measurement signal
-----------------------------

Using the *Connectors* package with the generator class for the linear sweep is straight forward.
In production code, all parameters, that can be passed to the constructor, should have a setter method, that is decorated to become an input connector.
This has been omitted in this tutorial to keep the code short.

.. literalinclude:: ressources/transfer_function.py
   :language: python
   :pyobject: SweepGenerator


Compute the fourier transform
-----------------------------

Decorating the methods of the class for the fourier transform works just like in the previous classes.
But the deletion of the input signal in the getter method :meth:`get_spectrum` is noteworthy.

.. literalinclude:: ressources/transfer_function.py
   :language: python
   :pyobject: FourierTransform

Since the input signal is the only parameter for the fourier transform, the reference to it can be deleted after computing the output spectrum, as long as the caching of the output spectrum is enabled.
The only situation, in which the cached spectrum becomes invalid and the output spectrum has to be recomputed, is when a new input signal is provided.
So the old input signal is no longer needed after the computation.

In this example, the input signals for the two fourier transform classes would not be garbage collected, because they are cached in the outputs of the signal generator and the system under test.
The memory requirements for running the script of this tutorial are moderate, so that the code has not been optimized for minimal memory consumption by deactivating caching and other measures.
In some practical situations, these optimizations can reduce the memory consumption significantly.


Compute the transfer function
-----------------------------

The class, that computes the transfer function by dividing the response spectrum by the excitation spectrum is again straight forward.
The only difference, that has not been shown in previous classes is, that an output connector depends on the parameters of multiple input connectors.
Each of these receives the name of the dependent output connector as a parameter for the :class:`~connectors.Input` decorator.

.. literalinclude:: ressources/transfer_function.py
   :language: python
   :pyobject: TransferFunction


Plot the transfer function
--------------------------

For the sake of simplicity, the plotting class in this tutorial only plots the magnitude of the transfer function.
Plotting the phase aswell, requires some additional functionalities of :mod:`matplotlib`, which is not in the scope of this tutorial.

The plotting class demonstrates the use of a multi-input connector for plotting multiple spectrums in one plot.

.. literalinclude:: ressources/transfer_function.py
   :language: python
   :pyobject: MagnitudePlot

Decorating the :meth:`add_spectrum` method to become a multi-input connector is similar to the regular input connectors.
It also gets the name of the dependent output connectors passed as a parameter.
It is improtant though, that the method of multi-input returns an ID, with which the added dataset can be identified, when it shall be deleted or replaced.

Specifying a remove-method for a multi-input connector is mandatory.
This method is called whenever a dataset is removed, for example by disconnecting an output connector from the multi-input.
Notice that the remove-method :meth:`remove_spectrum` is decorated with a method of the multi-input connector instead of an object from the *Connectors* package.

The replace-method :meth:`replace_spectrum` of the multi-input connector is called, whenever an added spectrum shall be replaced by an updated version.
If none is specified, the replacement will be done by removing the old dataset and adding a new one, which does not preserve the order, in which the datasets have been added.

The spectrums, that are added through the :meth:`add_spectrum` method are managed by a :class:`~connectors.MultiInputData` container.
This is basically an :class:`~collections.OrderedDict`, that has been extended with an :meth:`~connectors.MultiInputData.add` method, which adds the given dataset to the dictionary and returns a unique ID, under which the dataset has been stored.

The :meth:`show` method is decorated to become an output connector, despite the fact that it does not return any result value.
Nevertheless, this allows to model, that showing the plot depends on the input data for the plot.

Note that the automated parallelization is disabled for this method by passing the flag :const:`~connectors.Parallelization.SEQUENTIAL` as the *parallelization* parameter for the output decorator.
By default, the *Connectors* package parallelizes independent computations in separate threads.
Process-based parallelization is also available, but this requires the data, that is passed through the connections, to be pickle-able and the pickling introduces additional overhead.
GUI functionalities often require, that all updates of the GUI are done by the same thread, which is why this example script will raise errors if the parallelization of the :meth:`show` method is not disabled.


Instantiating the processing network
------------------------------------

Now that all the necessary processing classes are implemented, the network for measuring and computing the transfer function can be set up.

First the linear, time-invariant system is instantiated.
The impulse response is chosen to have a rolloff at both high and low frequencies.

.. literalinclude:: ressources/transfer_function.py
   :language: python
   :start-after: if __name__ == "__main__":
   :end-before: sweep =

After that, the sweep generator is created and connected to the system, that shall be measured.
The connection is established by calling the :meth:`~connectors.connectors.OutputConnector.connect` method of the output connector :meth:`get_sweep` with the input connector :meth:`set_input` from the system.
The :meth:`~connectors.connectors.OutputConnector.connect` method returns the instance, to which the connector belongs.
This way, the instantiation of a processing class and the connection of one of its connectors can be done in one line, like this example shows.

.. literalinclude:: ressources/transfer_function.py
   :language: python
   :start-after: system =
   :end-before: excitation_fft =

Instantiating the fourier transform classes is straight forward now.
Note, that this time, the :meth:`~connectors.connectors.SingleInputConnector.connect` method of the input connectors are called with an output connector as a parameter, while it is the other way around, during the instantiation of the sweep generator.
Both ways are possible.

.. literalinclude:: ressources/transfer_function.py
   :language: python
   :start-after: sweep =
   :end-before: transfer_function =

The class for dividing the two spectrums is created without connecting any of its connectors in the same line.
Since two of its connectors have to be connected, the connections are established in separate but similar lines, which improves the readability of the code.

.. literalinclude:: ressources/transfer_function.py
   :language: python
   :start-after: response_fft =
   :end-before: plot =

Finally, the plot is created and shown.
In addition to the measured transfer function, the plot also shows the spectrum of the system's impulse response, so it can be seen how the measured transfer function deviates from the expected spectrum.

.. graphviz::

   digraph Plot{
      rankdir=LR;
      ir -> system;
      ir -> fft0 -> plot;
      generator -> system -> fft1 -> division -> plot;
      generator -> fft2 -> division;
      ir [label="Impulse response", shape=octagon, color=green];
      fft0 [label="FFT", shape=box, color=green];
      generator [label="Signal generator", shape=hexagon];
      system [label="{|System|}", shape=record, color=red];
      fft1 [label="FFT", shape=box, color=blue];
      division [label="÷", shape=box, color=blue];
      fft2 [label="FFT", shape=box, color=blue];
      plot [label="Plot", shape=parallelogram];
      {rank=same; ir, system};
      {rank=same; fft0, fft1, fft2};
   }

Adding the measured transfer function is done through connections, just like the other connections, that have been established before.
It is noteworthy though, how the spectrum of the impulse response is added by simply calling the respective methods and without relying on the functionality of the *Connectors* package.
This shows, that the decorated methods can still be used as normal methods, even when they are extended with the functionality of a connector.

.. literalinclude:: ressources/transfer_function.py
   :language: python
   :start-after: transfer_function.set_response.connect
   :end-before: sweep.set_start_frequency

This results in the following plot.
The measured transfer function matches well with the spectrum of the original impulse response, but especially at low frequencies, there are slight deviations.
Above 20kHz, the two measured frequency response becomes highly inaccurate, which is because the sweep has not excited these frequencies, so the computation of the transfer function becomes a division by zero.

.. image:: ressources/transfer_function1.png

To demonstrate the automated updating of data in a processing network, the start frequency of the sweep is changed and the plot is shown again.

.. literalinclude:: ressources/transfer_function.py
   :language: python
   :start-after: magnitude_plot.show()

The following plot shows the effect of raising the start frequency of the sweep to a value in the plotted frequency range.
Since the low frequencies are no longer properly excited, the measurement of the tranfer function is invalid here aswell.

.. image:: ressources/transfer_function2.png


The complete script
-------------------

.. literalinclude:: ressources/transfer_function.py
   :language: python
