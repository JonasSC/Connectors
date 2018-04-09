test:
	python3 -m pytest --doctest-glob="*.rst"

test_coverage:
	python3 -m pytest --doctest-glob="*.rst" --cov="connectors" --cov-report term:skip-covered

lint:
	pylint3 --rcfile=tests/pylintrc_connectors connectors
	pylint3 --rcfile=tests/pylintrc_tests tests/helper
	pylint3 --rcfile=tests/pylintrc_tests tests/testclasses
	pylint3 --rcfile=tests/pylintrc_tests tests/tests

doc:
	sphinx-build -b html documentation docs
