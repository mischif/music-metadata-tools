# encoding: utf-8

################################################################################
#                                  apic-tool                                   #
#       Insert cover images to and extract cover images from music files       #
#                           (C) 2015-16, 2019 Mischif                          #
#       Released under version 3.0 of the Non-Profit Open Source License       #
################################################################################

from argparse import ArgumentTypeError, Namespace
from mock import Mock, patch
from os.path import abspath, dirname, getsize, join

import pytest

from apic_tool.cli import main, parse_args


APIC_TOOL_DATA = abspath(join(dirname(__file__), "data"))
AUTOSORT_AUDIO = abspath(join(dirname(dirname(__file__)), "id3autosort", "audio"))


@pytest.mark.parametrize("action", ["insert", "extract"], ids=["insert-action", "extract-action"])
@pytest.mark.parametrize("dry_run", [True, False], ids=["dry-run", "no-dry-run"])
@pytest.mark.parametrize("verbose", [True, False], ids=["verbose", "no-verbose"])
@pytest.mark.parametrize("force", [True, False], ids=["forced", "not-forced"])
@pytest.mark.parametrize("extract_pic", [True, False], ids=["extract-location", "no-extract-location"])
@pytest.mark.parametrize("keep_pic", [True, False], ids=["keep-pic", "no-keep-pic"])
@pytest.mark.parametrize("insert_dirs, insert_files", [(True, False), (False, True)], ids=["insert-dirs", "insert-files"])
def test_parse_args(action, dry_run, verbose, force, extract_pic, keep_pic, insert_dirs, insert_files, tmpdir):
	extract_location = None
	args_list = []

	if dry_run:
		args_list.append("-n")

	if verbose:
		args_list.append("-v")

	if force:
		args_list.append("--force")

	args_list.append(action)

	if action == "extract":
		args_list.append(join(APIC_TOOL_DATA, "test_extract.mp3"))

		if extract_pic:
			extract_location = join(APIC_TOOL_DATA, "test_extract.png")
			args_list.append(extract_location)

	elif action == "insert":
		args_list.extend(["-p", join(APIC_TOOL_DATA, "test_cover.png")])

		if keep_pic:
			args_list.append("-k")

		if insert_files:
			args_list.extend(["-f", join(APIC_TOOL_DATA, "test_insert.mp3"),
							  "--file", join(APIC_TOOL_DATA, "test_extract.mp3")])

		if insert_dirs:
			args_list.extend(["-d", APIC_TOOL_DATA])

	args = parse_args(argv=args_list)

	assert args.dry_run == dry_run
	assert args.verbose == verbose
	assert args.force == force

	if action == "extract":
		assert args.extract_music == join(APIC_TOOL_DATA, "test_extract.mp3")
		assert args.extract_pic == extract_location

	if action == "insert":
		assert args.keep_pic == keep_pic

		if insert_files:
			assert args.insert_files == [join(APIC_TOOL_DATA, "test_insert.mp3"),
										 join(APIC_TOOL_DATA, "test_extract.mp3")]

		if insert_dirs:
			assert args.insert_dirs == [APIC_TOOL_DATA]


def test_action_unhappy_paths(tmpdir):
	with pytest.raises(ArgumentTypeError):
		parse_args(argv=["extract", str(tmpdir)])

	with pytest.raises(ArgumentTypeError):
		parse_args(argv=["extract", join(AUTOSORT_AUDIO, "test_wav.wav")])

	with pytest.raises(ArgumentTypeError):
		parse_args(argv=["insert", "-d", join(AUTOSORT_AUDIO, "test_wav.wav", "-p", join(APIC_TOOL_DATA, "test_cover.png"))])

	with pytest.raises(ArgumentTypeError):
		parse_args(argv=["insert", "-f", join(APIC_TOOL_DATA, "test_insert.mp3"), "-p", join(APIC_TOOL_DATA, "test_unsupported_cover.bmp")])


@pytest.mark.parametrize("action", ["insert", "extract"], ids=["insert-action", "extract-action"])
@patch("apic_tool.cli.insert_image")
@patch("apic_tool.cli.extract_image")
@patch("apic_tool.cli.parse_args")
@patch("apic_tool.cli.logger")
def test_main(mock_logger, mock_parse_args, mock_extract, mock_insert, action):
	args_dict = {
		"action": action,
		"dry_run": False,
		"extract_music": join(APIC_TOOL_DATA, "test_extract.mp3"),
		"extract_pic": None,
		"force": False,
		"insert_files": [join(APIC_TOOL_DATA, "test_extract.mp3")],
		"insert_dirs": None,
		"insert_pic": join(APIC_TOOL_DATA, "test_cover.png"),
		"keep_pic": True,
		"verbose": False,
		}

	mock_parse_args.return_value = Namespace(**args_dict)
	main()

	if action == "extract":
		mock_extract.assert_called_once_with(mock_logger,
											 args_dict["extract_music"],
											 args_dict["extract_pic"],
											 args_dict["dry_run"],
											 args_dict["force"])
	else:
		mock_insert.assert_called_once_with(mock_logger,
											args_dict["insert_pic"],
											args_dict["insert_dirs"],
											args_dict["insert_files"],
											args_dict["keep_pic"],
											args_dict["dry_run"],
											args_dict["force"])
