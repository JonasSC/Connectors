.. _lazy_execution:

Lazy execution
==============

By default, the connectors are executed lazily, which means, that input values are not propagated through a processing network, unless an output value, which depends on them, is requested.
This is an important design decision, not only, because it saves potentially unnecessary computations, but also, because the correct input data might not be available at the time of setting up the processing network.
In this case, the processing objects still have their default values, which might lead to incompatible results and subsequently errors, when executing computations in a processing network without correct input.

An example script
-----------------

The following example shows, what happens, when a processing chain is set up, when a value is changed and when a value is retrieved.
It consists of two trivial processors, that simply pass their input value to their output.

>>> import connectors
>>> p1 = connectors.blocks.Passthrough()
>>> p2 = connectors.blocks.Passthrough().input.connect(p1.output)  # (Connect)
>>> _ = p1.input("data")                                           # (Set)
>>> p2.output()                                                    # (Get)
'data'

The following graph illustrates the communication between the input and output connectors of ``p1`` and ``p2``.
The columns in this graph correspond to the connectors, while the rows are in the order, in which the depicted events occur.
The yellow ellipses stand for the commands, from the example script above.
The symbols, that represent the connectors, are either green, after the respective method has been executed, or red, if there are pending value changes, that require an execution of the method, in order to compute the current output value.

.. graphviz::

   digraph LazyExecutionExample{
      rankdir = LR;

      p1_input_label [label="p1.input", shape=plain, fontsize=32];
      p1_input_set [label="", shape=parallelogram, style=filled, fillcolor=red];
      p1_input_notify [label="", shape=parallelogram, style=filled, fillcolor=green];

      p1_output_label [label="p1.output", shape=plain, fontsize=32];
      p1_output_connect [label="", shape=trapezium, style=filled, fillcolor=red];
      p1_output_set [label="", shape=trapezium, style=filled, fillcolor=red];
      p1_output_notify [label="", shape=trapezium, style=filled, fillcolor=red];
      p1_output_request [label="", shape=trapezium, style=filled, fillcolor=red];
      p1_output_execute [label="", shape=trapezium, style=filled, fillcolor=green];

      p2_input_label [label="p2.input", shape=plain, fontsize=32];
      p2_input_connect [label="", shape=parallelogram, style=filled, fillcolor=red];
      p2_input_set [label="", shape=parallelogram, style=filled, fillcolor=red];
      p2_input_notify [label="", shape=none];
      p2_input_request [label="", shape=parallelogram, style=filled, fillcolor=red];
      p2_input_execute [label="", shape=parallelogram, style=filled, fillcolor=green];

      p2_output_label [label="p2.output", shape=plain, fontsize=32];
      p2_output_connect [label="", shape=trapezium, style=filled, fillcolor=red];
      p2_output_set [label="", shape=trapezium, style=filled, fillcolor=red];
      p2_output_notify [label="", shape=none];
      p2_output_request [label="", shape=trapezium, style=filled, fillcolor=red];
      p2_output_execute [label="", shape=trapezium, style=filled, fillcolor=green];

      connect [label="Connect", style=filled, fillcolor=yellow];
      set [label="Set", style=filled, fillcolor=yellow];
      get [label="Get", style=filled, fillcolor=yellow];
      return [label="Return", style=filled, fillcolor=yellow];

      {rank="same"; connect; set}
      {rank="same"; get; return}
      {rank="same"; p1_input_label; p1_input_set; p1_input_notify}
      {rank="same"; p1_output_label; p1_output_connect; p1_output_set; p1_output_notify; p1_output_request; p1_output_execute}
      {rank="same"; p2_input_label; p2_input_connect; p2_input_set; p2_input_notify; p2_input_request; p2_input_execute}
      {rank="same"; p2_output_label; p2_output_connect; p2_output_set; p2_output_notify; p2_output_request; p2_output_execute}

      p1_output_label -> p1_output_connect -> p1_output_set-> p1_output_notify -> p1_output_request -> p1_output_execute [style="invis"];
      p2_input_label -> p2_input_connect -> p2_input_set -> p2_input_notify -> p2_input_request -> p2_input_execute [style="invis"];
      p2_output_label -> p2_output_connect -> p2_output_set -> p2_output_notify -> p2_output_request -> p2_output_execute [style="invis"];

      p1_input_label -> p1_output_label -> p2_input_label -> p2_output_label [style="invis"];
      p1_output_execute -> p1_output_execute [style="invis"];

      connect -> p1_output_connect;
      p1_output_connect -> p2_input_connect [label="announce"];
      p2_input_connect -> p2_output_connect [label="announce"];
      set -> p1_input_set;
      p1_input_set -> p1_output_set [label="announce"];
      p1_output_set -> p2_input_set [label="announce"];
      p2_input_set -> p2_output_set [label="announce"];
      p1_input_set -> p1_input_notify [label="execute"];
      p1_input_notify -> p1_output_notify [label="notify"];
      p2_output_request -> get [dir="back"];
      p2_input_request -> p2_output_request [label="request", dir="back"];
      p1_output_request -> p2_input_request [label="request", dir="back"];
      p1_output_request -> p1_output_execute [label="execute"];
      p1_output_execute -> p2_input_execute [label="notify"];
      p2_input_execute -> p2_input_execute [label="execute"];
      p2_input_execute -> p2_output_execute [label="notify"];
      p2_output_execute -> p2_output_execute [label="execute"];
      p2_output_execute -> return;
   }

This graph shows the behavior of the lazily executed connectors:

* When establishing a connection, the value change is announced to all connectors down the processing chain.
* When calling an input connector, the value change is announced, too.
  Additionally, the corresponding setter method is executed and the observing output connectors (which belong to the same object) are notified, that the setter has been executed.
  This means, that the output connectors do not have to request the setters execution, when they themselves receive a request to be executed.
* When an output connector is called, it requests the upstream connectors to be executed and waits for the corresponding notifications, before it executes its own getter method and returns the result.
  It happens only in this step, that the methods of the connectors are executed.


Disabling lazy execution
------------------------

Input connectors can be configured to automatically request the data of connected outputs by passing a flag from the :class:`connectors.Laziness` enum to its :meth:`~connectors.connectors.SingleInputConnector.set_laziness` method.

An example for the necessity of eager execution would be a plot, which shall automatically update, whenever new data can be computed.
In order to avoid the aforementioned problem of propagating default values, it is recommended to implement such classes with lazy execution enabled and disable the lazy execution as soon as the processing network has been intitialized with correct data.
