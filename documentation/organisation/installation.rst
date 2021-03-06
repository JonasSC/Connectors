Installation
============

pip
---

The easiest way to install the *Connectors* package is probably through ``pip``.

::

   pip3 install connectors

If the package shall only be installed for the current user, rather than system wide, run the following command:

::

   pip3 install --user connectors


Installation from source
------------------------

To retrieve the sources, the ``git``-repository of the *Connectors* package has to be cloned.

::

   git clone https://github.com/JonasSC/Connectors.git Connectors

The ``Connectors`` at the end of this command specifies the directory, in which the local copy of the repository shall be created.
After cloning, move to that directory.

::

   cd Connectors

Now the *Connectors* package can be installed system wide with the following command:

::

   python3 setup.py install

Alternatively, the package can be installed only for the current user.

::

   python3 setup.py install --user
