Information: Implementation details
===================================

:mod:`asyncio`
--------------

The *Connectors* package uses :mod:`asyncio` to model the dependencies between the connectors and schedule their execution.
The event loop is started by the connector, which triggers the computations and ends, when that connector's computation has finished.


Connector proxies - avoiding circular references
------------------------------------------------

.. note::
   
   Circular references occur, when objects have references to each other, so that their reference count never reaches zero, even when there is no reference to the objects in the active code.
   In such a case, the objects are not automatically deleted by Python's reference counting mechanism.

   Python uses *bound methods* and *unbound methods* to avoid circular references, in which an object has references to its methods, while the methods have a reference to the object.
   Unbound methods are basically functions, which require the object to be passed as the first parameter, which is commonly called *self*.
   An object has a reference to its class, which has references to its unbound methods, but the unbound methods have no reference to the object.
   When a method is accessed, Python automatically creates a bound method by predefining the first parameter with the object.
   Obviously, this causes bound methods to have a reference to the object, but since the object does not store references to bound methods, circular references do not occur.

Unbound methods are attributes of a class, which cannot store information about individual objects.
Connectors on the other hand must be able to store such information, like established connections or configurations about their behavior.
This requires the connectors to be persistent, unlike bound methods, which are created freshly, whenever they are required.
Also, in order to execute the method, which they have replaced, connectors have a reference to the object, to which they belong, which leads to circular references.

In the *Connectors* package, this problem is addressed by using weak references for the connector's reference to their object.
This alone is not sufficient though, since this would break the functionality to call a connector immediately after instantiating an object::

   result = ExampleClass().connector()

In the above example, an object of :class:`ExampleClass` is created and and its connector :meth:`connector` is accessed.
Since no reference of the object is stored, except for the weak reference of the connector, the object will be garbage collected after accessing the connector, but before executing it.
So the connector cannot be executed.

To prevent objects from being garbage collected prematurely, the *Connectors* package uses a mechanism similar to the bound and unbound methods from Python.
As long as no individual information has to be stored in the connector, the method is not replaced by a connector object.
Instead a :class:`~connectors.proxies.ConnectorProxy` object is created each time, when the connector is accessed.
Similar to bound methods, the connector proxy has a reference to the object, but not vice versa.
Only when establishing a connection or when changing the configuration, the method is replaced by a connector.
