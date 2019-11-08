# encoding: utf-8

################################################################################
#                                  apic-tool                                   #
#       Insert cover images to and extract cover images from music files       #
#                           (C) 2015-16, 2019 Mischif                          #
#       Released under version 3.0 of the Non-Profit Open Source License       #
################################################################################

from errno import EACCES
from functools import partial
from os.path import abspath, dirname, join
from mock import call, Mock, patch

try:
	from importlib import reload
except ImportError:
	pass

import pytest

from mutagen import MutagenError
from mutagen.id3 import ID3, APIC
from mutagen.mp3 import MP3

from apic_tool.workers import mp3worker


APIC_TOOL_DATA = abspath(join(dirname(dirname(__file__)), "data"))
AUTOSORT_AUDIO = abspath(join(dirname(dirname(dirname(__file__))), "id3autosort", "audio"))


def test_supported_extensions():
	assert mp3worker.MP3Worker.supported_extensions() == ["mp3"]


@patch("apic_tool.workers.mp3worker.MP3")
@pytest.mark.parametrize("scenario", ["good", "eacces", "exception"],
						 ids=["happy-path", "permission-denied", "generic-exception"])
def test_load_file(mock_mp3, scenario):
	mock_logger = Mock()

	def _middle(path):
		raise MutagenError(IOError(EACCES, "Permission denied"))

	if scenario == "eacces":
		mock_mp3.side_effect = _middle
	else:
		mock_mp3.side_effect = MP3

	if scenario == "exception":
		path = join(AUTOSORT_AUDIO, "test_wav.wav")
	else:
		path = join(APIC_TOOL_DATA, "test_extract.mp3")

	if scenario == "good":
		assert isinstance(mp3worker.MP3Worker.load_file(mock_logger, path), MP3)
	elif scenario == "eacces":
		assert mp3worker.MP3Worker.load_file(mock_logger, path) is None
		mock_logger.info.assert_called_once_with("Permission denied attempting to access file %s", path)
	elif scenario == "exception":
		assert mp3worker.MP3Worker.load_file(mock_logger, path) is None
		mock_logger.info.assert_called_once_with("Error trying to load %s as MP3 file: %s", path, "can't sync to MPEG frame")


@pytest.mark.parametrize("scenario", ["good", "missing", "unclean", "tagless"],
						 ids=["happy-path", "missing-metadata", "sketchy-load", "tagless-file"])
def test_get_image_data(scenario):
	mp3worker.MP3Worker.load_file = mock_load = Mock()
	mock_logger = Mock()
	path = join(APIC_TOOL_DATA, "test_extract.mp3")

	with open(join(APIC_TOOL_DATA, "test_cover.png"), "rb") as f:
		expected_cover = f.read()

	if scenario == "good":
		reload(mp3worker)
	elif scenario == "missing":
		mock_load.return_value = None
	else:
		mock_load.return_value = mock_load

	if scenario == "unclean":
		mock_load.info.sketchy = True
		mock_load.tags = {}
	elif scenario == "tagless":
		mock_load.info.sketchy = False
		mock_load.tags = {}

	(data, ext) = mp3worker.MP3Worker.get_image_data(mock_logger, path)

	assert (data, ext) == (expected_cover, "png") if scenario == "good" else (None, None)

	if scenario == "unclean":
		mock_logger.warning.assert_called_once_with("Couldn't load file %s cleanly", path)
		mock_logger.info.assert_called_once_with("No tags in file %s, skipping", path)
	elif scenario == "tagless":
		mock_logger.info.assert_called_once_with("No tags in file %s, skipping", path)


@pytest.mark.parametrize("scenario", ["good", "missing", "unclean", "tagless", "forced"],
						 ids=["happy-path", "missing-metadata", "sketchy-load", "tagless-file", "forced"])
def test_can_insert_image(scenario):
	mp3worker.MP3Worker.load_file = mock_load = Mock()
	mock_logger = Mock()
	path = join(APIC_TOOL_DATA, "test_extract.mp3")
	force = scenario == "forced"

	if scenario == "good":
		reload(mp3worker)
	elif scenario == "missing" or scenario == "forced":
		mock_load.return_value = None
	else:
		mock_load.return_value = mock_load

	if scenario == "unclean":
		mock_load.info.sketchy = True
	elif scenario == "tagless":
		mock_load.info.sketchy = False
		mock_load.tags = {}

	result = mp3worker.MP3Worker.can_insert_image(mock_logger, path, force)

	assert result is (True if scenario == "good" or force else False)

	if scenario == "unclean":
		mock_logger.warning.assert_called_once_with("Couldn't load file %s cleanly, skipping", path)
	elif scenario == "tagless":
		mock_logger.info.assert_called_once_with("No tags in file %s, skipping", path)


@pytest.mark.parametrize("scenario", ["good", "bad"], ids=["happy-path", "unhappy-path"])
def test_write_to_metadata(scenario):
	mp3worker.MP3Worker.load_file = mock_load = Mock()
	mock_logger = Mock()
	music_path = join(APIC_TOOL_DATA, "test_extract.mp3")
	cover_path = join(APIC_TOOL_DATA, "test_cover.png")

	if scenario == "good":
		reload(mp3worker)
	elif scenario == "bad":
		mock_load.return_value = mock_load

	def _add_tags(mock):
		mock.tags = ID3()
		mock.tags.version = (2, 2, 7)
		mock.tags.save = Mock()
		mock.tags.save.side_effect = Exception("Test error")
		tag = APIC(
			   encoding=3,			# UTF-8
			   type=3,				# Cover image
			   mime="png",
			   )
		mock.tags.add(tag)

	mock_load.info.sketchy = True
	mock_load.tags = {}
	mock_load.add_tags.side_effect = partial(_add_tags, mock_load)

	if scenario == "good":
		assert mp3worker.MP3Worker.write_to_metadata(mock_logger, music_path, cover_path, False) is True
		mock_logger.info.assert_called_once_with("File %s already has embedded image, skipping", music_path)
	elif scenario == "bad":
		assert mp3worker.MP3Worker.write_to_metadata(mock_logger, music_path, cover_path, True) is False
		mock_logger.debug.assert_has_calls([
			call("Forced to continue with file %s despite unclean load", music_path),
			call("Forced to create metadata for file %s, which has none", music_path),
			call("Tags are version %d.%d", 2, 2),
			call("Upgrading tags for file %s to v2.3", music_path),
			call("Supposed mimetype for image: %s", "image/png"),
			call("Adding image to file")
			])
		mock_logger.info.assert_has_calls([
			call("Forced to remove pre-existing APIC tags for file %s", music_path),
			call('Saving updated tags'),
			call("Error saving tags for file %s: %s", music_path, "Test error")
			])