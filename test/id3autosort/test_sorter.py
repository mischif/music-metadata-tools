# encoding: utf-8

################################################################################
#                                 id3autosort                                  #
#  A collection of tools for manipulating and interacting with music metadata  #
#                               (C) 2019 Mischif                               #
#       Released under version 3.0 of the Non-Profit Open Source License       #
################################################################################

from __future__ import unicode_literals

from errno import EACCES
from os import sep
from os.path import abspath, dirname, join

import pytest

from mock import Mock, patch
from mutagen import File

from id3autosort.sorter import (
	get_music_files,
	get_new_path,
	normalize_tags,
	sort
	)


TEST_AUDIO = abspath(join(dirname(__file__), "audio"))


@pytest.mark.parametrize("audio_path", [
	join(TEST_AUDIO, "test_aac.m4a"),
	join(TEST_AUDIO, "test_aiff.aiff"),
	join(TEST_AUDIO, "test_wma.wma")
	], ids=["easy-tags", "aiff-tags", "wma-tags"])
@pytest.mark.parametrize("windows_safe", [True, False], ids=["windows-safe", "non-windows-safe"])
def test_parse_normalize_tags(audio_path, windows_safe):
	mock_logger = Mock()
	data = File(audio_path, easy=True)

	if "audio/aiff" in data.mime:
		result = {
			"album": "_id3autosort_testing_",
			"date": "2019",
			"genre": "Testing",
			"title": "Test AIFF",
			"tracknumber": "7",
			}

		if windows_safe:
			result.update({"artist": "TestAIFF"})
		else:
			result.update({"artist": ">Test?A\u012cFF<", "album": "_id3autosort:_testing_"})

	elif "audio/x-wma" in data.mime:
		result = {
			"album": "_id3autosort_testing_",
			"genre": "Testing",
			"title": "Test WMA",
			"tracknumber": "4",
			}

		if windows_safe:
			result.update({"artist": "TestWMA"})
		else:
			result.update({"artist": "?Test<>\u0174MA:", "album": "_id3autosort:_testing_"})

	else:
		result = {
			"album": "_id3autosort_testing_",
			"date": "0",
			"genre": "Testing",
			"title": "Test AAC",
			"tracknumber": "3",
			}

		if windows_safe:
			result.update({"artist": "TestAAC"})
		else:
			result.update({"artist": "|Test<>AA\xc7.", "album": "_id3autosort:_testing_"})


	assert result == normalize_tags(mock_logger, data, windows_safe)


@patch("id3autosort.sorter.File")
def test_get_music_files(mock_file):
	mock_logger = Mock()

	def _middle(path, easy):
		if path.endswith(".mp3"):
			raise OSError(EACCES, "Permission Denied")
		else:
			return File(path, easy=easy)

	mock_file.side_effect = _middle

	result = get_music_files(mock_logger, TEST_AUDIO)
	assert len(result) == 5


@patch("id3autosort.sorter.normalize_tags")
def test_get_new_path(mock_normalize, tmpdir):
	mock_logger = Mock()
	tags = {"artist": "Track Artist", "album": "Track Album", "date": "1017"}
	valid_structure = sep.join(["{artist}", "{album} ({date})"])
	invalid_structure = sep.join(["{genre}", "{artist}", "{album}"])

	mock_normalize.return_value = tags

	assert join(str(tmpdir),
				"Track Artist",
				"Track Album (1017)") == get_new_path(mock_logger,
													  str(tmpdir),
													  valid_structure,
													  None,
													  True)
	assert None == get_new_path(mock_logger, str(tmpdir), invalid_structure, None, True)


@patch("id3autosort.sorter.isdir")
@patch("id3autosort.sorter.makedirs")
@patch("id3autosort.sorter.move")
def test_sort(mock_move, mock_makedirs, mock_isdir, tmpdir):
	mock_logger = Mock()

	def _makedirs_middle(path, permissions):
		if path.contains("AIFF"):
			raise OSError(EACCES, "Permission Denied")

	def _move_middle(from_path, to_path):
		if from_path.contains(".mp3"):
			raise OSError(EACCES, "Permission Denied")

	mock_isdir.side_effect = lambda path: False if path.find("AIFF") != -1 else True
	mock_makedirs.side_effect = _makedirs_middle
	mock_move.side_effect = _move_middle

	sort(mock_logger, TEST_AUDIO, "/tmp", "{artist}/{album} ({date})", True, False)
	sort(mock_logger, str(tmpdir), "/tmp", "{artist}/{album} ({date})", True, False)

	assert mock_makedirs.call_count == 3
	assert mock_move.call_count == 2
