.. _connectorsReference:

Connectors
==========

This section documents the capabilities of the connector objects, with which the decorated methods are replaced.
Instances of the following classes replace the decorated methods, so they are enhanced with the functionality of a connector.
These classes are not instantiated by code outside the *Connectors* package.


Connectors for setter methods
-----------------------------

.. autoclass:: connectors.connectors.SingleInputConnector
   :members:
   :inherited-members:

.. autoclass:: connectors.connectors.MultiInputConnector
   :members:
   :inherited-members:

   .. automethod:: __getitem__


Connectors for getter methods
-----------------------------

.. autoclass:: connectors.connectors.OutputConnector
   :members:
   :inherited-members:


.. autoclass:: connectors.connectors.MultiOutputConnector
   :members:
   :inherited-members:

   .. automethod:: __getitem__
