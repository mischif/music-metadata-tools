# encoding: utf-8

################################################################################
#                             music-metadata-tools                             #
#  A collection of tools for manipulating and interacting with music metadata  #
#                      (C) 2009-10, 2015-16, 2019 Mischif                      #
#       Released under version 3.0 of the Non-Profit Open Source License       #
################################################################################

from io import open
from os import path
from setuptools import setup

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, "README.md"), encoding="utf-8") as desc:
	long_description = desc.read()


setup(
	name="music-metadata-tools",

	version="0.3.0",

	packages=["id3autosort", "apic_tool"],

	license="NPOSL-3.0",

	url="https://github.com/mischif/music-metadata-tools",

	description="A collection of tools for manipulating and interacting with music metadata.",

	long_description=long_description,
	long_description_content_type="text/markdown",

	author="Jeremy Brown",
	author_email="mischif@users.noreply.github.com",

	python_requires=">=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, !=3.4.*, !=3.5.*, <4",

	install_requires=["mutagen"],

	setup_requires=["pytest-runner"],

	tests_require=["hypothesis", "hypothesis-pytest", "mock", "pytest", "pytest-cov"],

	extras_require={
		"test": ["codecov"],
		},

	entry_points={
		"console_scripts": ["id3autosort=id3autosort.cli:main"],
		},

	classifiers=[
		"Development Status :: 4 - Beta",

		"Operating System :: OS Independent",

		"License :: OSI Approved :: Open Software License 3.0 (OSL-3.0)",

		"Programming Language :: Python :: 2",
		"Programming Language :: Python :: 2.7",
		],

	keywords="ID3",
	)
