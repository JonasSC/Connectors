.. _connectorsReference:

Connectors
==========

This section shows the capabilities and configuration options of the connector objects, with which the decorated methods are replaced.

Connector classes
-----------------

Instances of the following classes replace the decorated methods, so they are enhanced with the functionality of a connector.
These classes are not instantiated by code outside the *Connectors* package.

.. autoclass:: connectors.connectors.OutputConnector
   :members:
   :inherited-members:

.. autoclass:: connectors.connectors.SingleInputConnector
   :members:
   :inherited-members:

.. autoclass:: connectors.connectors.MultiInputConnector
   :members:
   :inherited-members:

   .. automethod:: __getitem__


Automated parallelization
-------------------------

The following functionalities are for configuring the automated parallelization of the connector's computations.

.. autoclass:: connectors.Parallelization

.. autofunction:: connectors.executor


Configuring the laziness
------------------------

Flags of the following enumeration can be passed to an input connectors :meth:`~connectors._connectors._baseclasses.InputConnector.set_laziness` method.

.. autoclass:: connectors.Laziness
