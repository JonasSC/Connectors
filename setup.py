from setuptools import setup, find_packages

with open("README.rst") as f:
    long_description = f.read()

setup(name="connectors",
      version="4.1",
      description="A package for connecting objects to form a processing chain",
      long_description=long_description,
      url="https://github.com/JonasSC/Connectors",
      author="Jonas Schulte-Coerne",
      license="GNU Lesser General Public License v3 or later (LGPLv3+)",
      classifiers=["Development Status :: 5 - Production/Stable",
                   "License :: OSI Approved :: GNU Lesser General Public License v3 or later (LGPLv3+)",
                   "Programming Language :: Python :: 3.6",
                   "Programming Language :: Python :: 3.7",
                   "Intended Audience :: Developers",
                   "Intended Audience :: Science/Research",
                   "Topic :: Software Development :: Libraries :: Application Frameworks"],
      keywords="parallel observer pipes-and-filters",
      packages=find_packages(exclude=["documentation", "tests", "docs"]),
      install_requires=[],
      extras_require={"dev": ["pytest-cov", "pylint", "flake8"],
                      "test": ["pytest", "numpy"],
                      "doc": ["sphinx_rtd_theme"]},
      project_urls={"Documentation": "https://connectors.readthedocs.io/en/latest/",
                    "Bug Reports": "https://github.com/JonasSC/Connectors/issues",
                    "Source": "https://github.com/JonasSC/Connectors"})
