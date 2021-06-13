.PHONY: test test_coverage lint docs

test:
	python3 -m pytest --doctest-glob="*.rst" --doctest-modules $(filter-out $@,$(MAKECMDGOALS))

test_coverage:
	python3 -m pytest --doctest-glob="*.rst" --doctest-modules --cov="connectors" --cov-report term:skip-covered $(filter-out $@,$(MAKECMDGOALS))

lint:
	python3 -m flake8 --config=tests/flake8 connectors
	pylint3 --rcfile=tests/pylintrc_connectors connectors
	python3 -m flake8 --config=tests/flake8 tests/tests
	pylint3 --rcfile=tests/pylintrc_tests tests/tests

docs:
	sphinx-build -a -b html documentation docs
