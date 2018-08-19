Macro connectors for encapsulating processing networks in a class
=================================================================

Classes, which encapsulate networks of objects, that are connected with the functionalities of the *Connectors* package, are called *macros* or *macro classes* in the scope of this package.
The connectors, that are used to export connectors from the internal network as connectors of the macro, are called macro connectors.
This is the API reference for the functionalities, that are related to macro connectors.


Decorating methods
------------------

The following classes can be used to decorate methods, so they become macro connectors.

.. autoclass:: connectors.MacroOutput
   :members:
   :inherited-members:
   
.. autoclass:: connectors.MacroInput
   :members:
   :inherited-members:


Configuring macro connectors
----------------------------

Instances of the following classes replace the decorated methods, so they are enhanced with the functionality of a macro connector.

.. autoclass:: connectors.connectors.MacroOutputConnector
   :members:
   :inherited-members:

.. autoclass:: connectors.connectors.MacroInputConnector
   :members:
   :inherited-members:
   