Proxy classes
=============

This section contains the documentation of the connector proxy classes.
The proxies emulate the behavior of the connectors and are used to avoid :ref:`circular references<avoidingCircularReferences>`.
See the :ref:`decorators<decoratorsReference>` on how to create connectors and the :ref:`connectors<connectorsReference>` themselves on how to use and configure them.

Base class
----------

.. autoclass:: connectors._proxies._baseclasses.ConnectorProxy
   :members:


Proxy classes
-------------

.. autoclass:: connectors._proxies.OutputProxy
   :members:
   :inherited-members:

.. autoclass:: connectors._proxies.SingleInputProxy
   :members:
   :inherited-members:

.. autoclass:: connectors._proxies.MultiInputProxy
   :members:
   :inherited-members:
