################################################################################
#                             music-metadata-tools                             #
#  A collection of tools for manipulating and interacting with music metadata  #
#                               (C) 2019 Mischif                               #
#       Released under version 3.0 of the Non-Profit Open Source License       #
################################################################################

.PHONY: test ci-test build

clean:
	rm -rf .coverage coverage.xml .eggs/ .hypothesis/ .pytest_cache/ *egg-info/ dist/ build/
	find . -name __pycache__ -exec rm -rf {} +
	find . -name *.pyc -exec rm -rf {} +

test:
	python -B setup.py test --addopts "--cov-report term-missing:skip-covered --cov-config setup.cfg"

ci-test:
	python setup.py test --addopts "--cov-report term-missing  --cov-report xml --cov-config setup.cfg"

build:
	python setup.py build sdist bdist_wheel
