# encoding: utf-8

################################################################################
#                                  apic-tool                                   #
#       Insert cover images to and extract cover images from music files       #
#                           (C) 2015-16, 2019 Mischif                          #
#       Released under version 3.0 of the Non-Profit Open Source License       #
################################################################################

from mock import call, Mock
from os.path import abspath, dirname, getsize, join
from shutil import copy

import pytest

from apic_tool.insertion import get_music_files, insert_image


APIC_TOOL_DATA = abspath(join(dirname(__file__), "data"))
AUTOSORT_AUDIO = abspath(join(dirname(dirname(__file__)), "id3autosort", "audio"))


def test_get_music_files():
	mock_logger = Mock()
	file_list = [join(APIC_TOOL_DATA, "test_insert.mp3")]
	dir_list = [AUTOSORT_AUDIO]
	result = sorted([join(AUTOSORT_AUDIO, "test_mp3.mp3"), join(APIC_TOOL_DATA, "test_insert.mp3")])

	assert sorted(get_music_files(mock_logger, file_list, dir_list, True)) == result
	mock_logger.debug.assert_has_calls([
		call("File %s is not a supported music file, skipping", join(AUTOSORT_AUDIO, "test_aac.m4a")),
		call("File %s is not a supported music file, skipping", join(AUTOSORT_AUDIO, "test_aiff.aiff")),
		call("File %s is not a supported music file, skipping", join(AUTOSORT_AUDIO, "test_flac.flac")),
		call("File %s is not a supported music file, skipping", join(AUTOSORT_AUDIO, "test_ogg.ogg")),
		call("File %s is not a supported music file, skipping", join(AUTOSORT_AUDIO, "test_wav.wav")),
		call("File %s is not a supported music file, skipping", join(AUTOSORT_AUDIO, "test_wma.wma")),
		], any_order=True)


def test_insert_image(tmpdir):
	mock_logger = Mock()
	music_path = join(str(tmpdir), "test_insert.mp3")
	cover_path = join(str(tmpdir), "test_cover.png")

	copy(join(APIC_TOOL_DATA, "test_insert.mp3"), music_path)
	copy(join(APIC_TOOL_DATA, "test_cover.png"), cover_path)
	orig_size = getsize(music_path)
	cover_size = getsize(cover_path)
	assert len(tmpdir.listdir()) == 2

	insert_image(mock_logger, cover_path, None, [music_path], False, False, False)
	assert len(tmpdir.listdir()) == 1
	assert getsize(music_path) >= orig_size + cover_size
	mock_logger.debug.assert_any_call("Writing image %s to file %s", cover_path, music_path)
	mock_logger.info.assert_has_calls([
		call("Deleting image file %s", cover_path)
		], any_order=True)
