Dependencies
============

Python version
--------------

The *Connectors* package is currently developed and tested with Python 3.7.
Python 3.6 is very likely to work as well.
Earlier versions are not compatible with the *Connectors* package.


Other packages and tools
------------------------

The *Connectors* package itself does not depend on other packages.
Nevertheless, the setup, the tests and the documentation rely on third party packages and tools.

* the setup is done with :mod:`setuptools`.
* the tests are run with :mod:`pytest`.
   - the test coverage is assessed with :mod:`pytest-cov`.
   - the code is analyzed with *Pylint* and :mod:`flake8`.
   - spell-checking is done with *pyenchant*.
* the documentation is built with :mod:`sphinx`.
   - the documentation uses the :mod:`sphinx_rtd_theme`.
   - graphs are drawn with :mod:`sphinx.ext.graphviz`.
   - some examples rely on :mod:`numpy` and :mod:`matplotlib`.
