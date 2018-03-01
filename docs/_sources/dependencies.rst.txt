Infrastructure: Dependencies
============================

Python version
--------------

The *Connectors* package is developed and tested with Python 3.6.
Python 3.5 might work, but this is not tested.
The package uses the ``await`` statement, which has been introduced in Python version 3.5, so earlier versions of Python are not able to run the *Connectors* package.


Other packages and tools
------------------------

The *Connectors* package itself does not depend on other packages.
Nevertheless, the setup, the tests and the documentation rely on third party packages and tools.

* the setup is done with :mod:`setuptools`
* the tests are run with :mod:`pytest`
   - the test coverage is assessed with :mod:`pytest-cov`
   - the code is analyzed with :mod:`pylint`
   - spell-checking is done with :mod:`enchant`
* the documentation is built with :mod:`sphinx`
   - graphs are drawn with :mod:`sphinx.ext.graphviz`
   - some examples rely on :mod:`numpy` and :mod:`matplotlib`
