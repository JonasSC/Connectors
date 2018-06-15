test:
	python3 -m pytest --doctest-glob="*.rst"

test_coverage:
	python3 -m pytest --doctest-glob="*.rst" --cov="connectors" --cov-report term:skip-covered

lint:
	python3 -m flake8 --config=tests/flake8 connectors
	pylint3 --rcfile=tests/pylintrc_connectors connectors
	python3 -m flake8 --config=tests/flake8 tests/tests
	pylint3 --rcfile=tests/pylintrc_tests tests/tests

doc:
	sphinx-build -b html documentation docs
