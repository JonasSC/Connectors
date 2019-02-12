Executors
=========

Executors control, if a connector is executed sequentially, in a parallel thread or even a separate process.
Use the :func:`connectors.executor` function to instantiate an executor.


Base class
----------

.. autoclass:: connectors._common._executors.Executor
   :members:
   :inherited-members:


Executor classes
----------------

.. autoclass:: connectors._common._executors.SequentialExecutor
   :members:
   :inherited-members:


.. autoclass:: connectors._common._executors.ThreadingExecutor
   :members:
   :inherited-members:


.. autoclass:: connectors._common._executors.MultiprocessingExecutor
   :members:
   :inherited-members:


.. autoclass:: connectors._common._executors.ThreadingMultiprocessingExecutor
   :members:
   :inherited-members:
