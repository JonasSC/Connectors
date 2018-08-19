.. _caching:

Caching
=======

By default, output connectors cache the return values of their wrapped getter methods.
This shall avoid unnecessary recomputations, when the output connectors are called multiple times.

The caching can only work well, when all setters, that affect the return value of an output connector, are decorated as input connectors, which are observed by that output connector.

If this is not the case, the caching can be disabled by passing ``False`` to an output connector's :meth:`~connectors.connectors.OutputConnector.set_caching` method.
Alternatively, the default setting for caching the result of a particular method can be changed by passing ``caching=False`` to the :class:`~connectors.Output` decorator of the method.
