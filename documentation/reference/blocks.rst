Processing blocks for common tasks
==================================

This is the API reference for processing blocks, that help with common tasks, when
constructing a processing network.


Routing data in a processing network
------------------------------------

.. autoclass:: connectors.blocks.PassThrough

   .. automethod:: output()
   .. automethod:: input(data)


.. autoclass:: connectors.blocks.Multiplexer

   .. automethod:: output()
   .. automethod:: input(data)
   .. automethod:: remove(data_id)
   .. automethod:: replace(data_id, data)



Reducing the memory consumption
-------------------------------

.. autoclass:: connectors.blocks.WeakrefProxyGenerator

   .. automethod:: output()
   .. automethod:: input(data)
   .. automethod:: delete_reference(*args, **kwargs)
