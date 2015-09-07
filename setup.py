# encoding: utf-8

################################################################################
#                             music-metadata-tools                             #
#  A collection of tools for manipulating and interacting with music metadata  #
#                       (C) 2009-2010, 2015 Jeremy Brown                       #
################################################################################

from setuptools import setup

setup(
	name="music-metadata-tools",

	version="0.2.0",

	packages=["id3autosort", "apic_tool"],

	license="NPOSL-3.0",

	install_requires=["hsaudiotag", "mutagen"],

	classifiers=[
		"Development Status :: 4 - Beta",

		"Operating System :: OS Independent",

		"License :: OSI Approved :: Open Software License 3.0 (OSL-3.0)",

		"Programming Language :: Python :: 2",
		"Programming Language :: Python :: 2.7",
		],

	keywords="ID3",
	)
