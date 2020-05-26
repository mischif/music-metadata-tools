# encoding: utf-8

################################################################################
#                                 id3autosort                                  #
#  A collection of tools for manipulating and interacting with music metadata  #
#                               (C) 2019 Mischif                               #
#       Released under version 3.0 of the Non-Profit Open Source License       #
################################################################################

from __future__ import unicode_literals

from argparse import Namespace
from os import sep
from os.path import abspath, dirname, join

import pytest

from mock import Mock, patch

from id3autosort.cli import main, parse_args


TEST_AUDIO = abspath(join(dirname(__file__), "audio"))


@pytest.mark.parametrize("source_dir", [TEST_AUDIO, join(TEST_AUDIO, "test_mp3.mp3"), "/proc/noexist"],
						 ids=["valid-source", "source-file", "source-inaccessible"])
@pytest.mark.parametrize("windows_safe, verbose, dry_run, structure", [
						 [True, False, False, False],
						 [False, True, False, False],
						 [False, False, True, False],
						 [False, False, False, True]],
						 ids=["windows-safe", "verbose", "dry-run", "custom-structure"])
def test_parse_args(tmpdir, windows_safe, verbose, dry_run, structure, source_dir):
	args_list = []
	output_structure = sep.join(["{artist}", "{album}"])

	if verbose:
		args_list.append("-v")

	if dry_run:
		args_list.append("-n")

	if structure:
		output_structure = sep.join(["{artist}", "{album} ({date})"])
		args_list.extend(["-s", sep.join(["r", "l (d)"])])

	if not windows_safe:
		args_list.append("-u")

	args_list.extend([source_dir, str(tmpdir)])

	if source_dir != TEST_AUDIO:
		with pytest.raises(SystemExit):
			parse_args(argv=args_list)
	else:
		args = parse_args(argv=args_list)

		assert args.verbose == verbose
		assert args.dry_run == dry_run
		assert args.windows_safe == windows_safe
		assert args.structure == output_structure
		assert args.src_paths == [TEST_AUDIO]
		assert args.dest_path == str(tmpdir)


@patch("id3autosort.cli.sort")
@patch("id3autosort.cli.parse_args")
@patch("id3autosort.cli.logger")
def test_main(mock_logger, mock_parse_args, mock_sort):
	args_dict = {
		"dest_path": "/tmp",
		"dry_run": False,
		"src_paths": [TEST_AUDIO],
		"structure": "{artist}/{album}",
		"verbose": False,
		"windows_safe": True,
		}

	mock_parse_args.return_value = Namespace(**args_dict)
	main()

	mock_sort.assert_called_once_with(mock_logger,
									  args_dict["src_paths"][0],
									  args_dict["dest_path"],
									  args_dict["structure"],
									  args_dict["windows_safe"],
									  args_dict["dry_run"])
