Reference: The core functionalities
===================================

This API reference for the core functionalities of the *Connectors* package, which is the decorators for enhancing methods with the functionalities of a connector and the connectors themselves.

Decorating methods
------------------

The following classes can be used to decorate methods, so they become connectors.

.. autoclass:: connectors.Output
   :members:
   :inherited-members:

.. autoclass:: connectors.Input
   :members:
   :inherited-members:

.. autoclass:: connectors.MultiInput
   :members:
   :inherited-members:


Configuring connectors
----------------------

Instances of the following classes replace the decorated methods, so they are enhanced with the functionality of a connector.

.. autoclass:: connectors.connectors.OutputConnector
   :members:
   :inherited-members:

.. autoclass:: connectors.connectors.SingleInputConnector
   :members:
   :inherited-members:

.. autoclass:: connectors.connectors.MultiInputConnector
   :members:
   :inherited-members:


Automated parallelization
-------------------------

The following functionalities are for configuring the automated parallelization of the connector's computations.

.. autoclass:: connectors.Parallelization

.. autofunction:: connectors.executor


Configuring the laziness
------------------------

Flags of the following enumeration can be passed to an input connectors :meth:`set_laziness` method.

.. autoclass:: connectors.Laziness
