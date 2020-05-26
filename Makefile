################################################################################
#                             music-metadata-tools                             #
#  A collection of tools for manipulating and interacting with music metadata  #
#                               (C) 2019 Mischif                               #
#       Released under version 3.0 of the Non-Profit Open Source License       #
################################################################################

.POSIX:

CI_OPTIONS="--cov-report xml"

.PHONY: test ci-test build

clean:
	rm -rf .coverage coverage.xml .eggs/ .pytest_cache/ *egg-info/ dist/ build/
	find . -name __pycache__ -exec rm -rf {} +
	find . -name *.pyc -exec rm -rf {} +

test:
	python -B setup.py test

ci-test:
	python setup.py test --addopts ${CI_OPTIONS}

build:
	python -m pep517.build -sb .
