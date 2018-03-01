Information: Lazy execution
===========================

By default, the connectors are executed lazily, which means, that input values are not propagated through a processing network, unless an output value, which depends on them, is requested.
This is an important design decision, not only, because it saves potentially unnecessary computations, but also, because the correct input data might not be available at the time of setting up the processing network.
In this case, the processing objects still have their default values, which might lead to incompatible results and subsequently errors, when executing computations in a processing network without correct input.

Input connectors can be configured to automatically request the data of connected outputs by passing a flag from the :class:`connectors.Laziness` enum to its :meth:`~connectors.connectors.SingleInputConnector.set_laziness` method.

An example for the necessity of eager execution would be a plot, which shall automatically update, whenever new data can be computed.
In order to avoid the aforementioned problem of propagating default values, it is recommended to implement such classes with lazy execution enabled and disable the lazy execution as soon as the processing network has been intitialized with correct data.
