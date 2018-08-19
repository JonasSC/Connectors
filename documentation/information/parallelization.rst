Automated parallelization
=========================

If a processing network is branched, so that different operations can be executed in parallel, the *Connectors* package has the functionality to do so.
This document provides some background information on this topic, since the distinction between a connector's *parallelization* parameter and its executor might be counter-intuitive.


The default settings
--------------------

By default, the execution of output connectors are parallelized in different threads, while input connectors are executed sequentially.
This choice has been made, because the complex computations are usually done in the getter methods, while the setters often only store parameters, which is such a short operation, that it would be slowed down by the overhead of a parallelization.

Preferring threads over processes in the default setting is justified by the lower overhead of threads and fewer constraints (e.g. pickle-ability of objects, that are passed between processes).
Also, many libraries such as :mod:`numpy` release the GIL in many of their functions, so that they do run concurrently, when using threads.


The *parallelization* parameter
-------------------------------

The *parallelization* parameter defines, which methods of parallelization are allowed for the given connector.

The *parallelization* parameter is meant to be configured in the decorator, when implementing processing classes, but connectors also provide a :meth:`set_parallelization` method to configure the parallelization of individual instances.
It must be set to a flag of the :class:`connectors.Parallelization` enum.

* Enforcing a sequential execution is useful for reducing the overhead, when doing short operations.
  Sometimes it is even necessary to disable the parallelization, like for example in GUI applications, where the drawing operations must be executed in the same thread.
* As explained above, threaded parallelization is often a good compromise.
* Using processes for the parallelization requires both the processing class and the data, that is passed through its connectors, to be pickle-able.
  Also, the overhead of starting an operation in a separate process and retrieving its result is much higher than with using threads, so process-based parallelization is only worth the effort for long running computations.
  Nevertheless, it is often recommended to allow the use of processes with the *parallelization* parameter, when implementing a processing class, if the constraints on pickle-ability are met.
  The actual parallelization method can later be chosen after setting up a processing network for a specific application, by specifying the executor of the connector, that triggers the computations.
  At this stage, the lengths of the computations can often be estimated better, than during the implementation of the classes.


Executors
---------

If an operation actually is parallelized as allowed by its *parallelization* parameter, is decided by the executor of the connector, that triggers the computations.

Executors are created with the factory function :func:`connectors.executor`, which takes the maximum number of threads and processes for the parallelization as parameters.
Think of executors as wrappers around the :class:`concurrent.futures.ThreadPoolExecutor` and :class:`concurrent.futures.ProcessPoolExecutor` classes.
They check, how a connector is allowed to be parallelized and then execute it accordingly:

* If a connector is allowed to be parallelized in a more complex way than the executor is capable of, the next simpler method for parallelization, that is available is used.
  The complexity hierarchy for this decision in descending order is process-based parallelization, separate threads and as last resort sequential execution.
* If a connector can be executed in a separate thread/process and the executor provides this functionality, the connector will never be executed in the main thread/process.

Only one executor is used for all computations, that are required for a requested result.
This is usually the executor of the output connector, through which the result is retrieved.
With non-lazy connectors, that request results immediately, when a parameter is set, the executor of the input connector for that parameter is used.
So changing the executors of connectors in the middle of a processing chain usually has no effect.
