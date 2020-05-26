# encoding: utf-8

################################################################################
#                                  apic-tool                                   #
#       Insert cover images to and extract cover images from music files       #
#                           (C) 2015-16, 2019 Mischif                          #
#       Released under version 3.0 of the Non-Profit Open Source License       #
################################################################################

from errno import EACCES
from mock import Mock, patch
from os import name, sep
from os.path import abspath, dirname, exists, join

import pytest

from apic_tool.extraction import extract_image, fuzzy_match, get_image_path, write_to_disk


TEST_DATA = abspath(join(dirname(__file__), "data"))


@pytest.mark.parametrize("scenario", ["eacces", "ioerror", "good"],
						 ids=["permission-denied", "generic-ioerror", "good"])
def test_write_to_disk(tmpdir, scenario):
	mock_logger = Mock()

	if scenario == "good":
		out_path = join(str(tmpdir), "test_write_to_disk.png")
	elif scenario == "eacces":
		if name == "posix":
			out_path = join(sep, "sys", "test_write_to_disk.png")
		else:
			out_path = join("C:", sep, "Windows", "explorer.exe")
	elif scenario == "ioerror":
		out_path = join("/proc", "test_write_to_disk.png")

	with open(join(TEST_DATA, "test_cover.png"), "rb") as f:
		data = f.read()

	try:
		write_to_disk(mock_logger, out_path, data)
	except IOError as e:
		assert e.errno != EACCES
		assert scenario == "ioerror"
	else:
		if scenario == "good":
			mock_logger.info.assert_not_called()
		elif scenario == "eacces":
			mock_logger.info.assert_called_once_with("Permission denied attempting to write image %s", out_path) 


@pytest.mark.parametrize("user", ["gif", "jpg", "jpeg", "png"],
						 ids=["user-gif", "user-jpg", "user-jpeg", "user-png"])
@pytest.mark.parametrize("worker", ["gif", "jpg", "jpeg", "png"],
						 ids=["worker-gif", "worker-jpg", "worker-jpeg", "worker-png"])
def test_fuzzy_match(user, worker):
	if user == worker:
		result = True
	elif user == "jpg" and worker == "jpeg":
		result = True
	elif user == "jpeg" and worker == "jpg":
		result = True
	else:
		result = False

	assert fuzzy_match(user, worker) is result


@pytest.mark.parametrize("image_name", [None, "test_file.jpg", "test_file.png"],
						 ids=["no-path", "correct-ext", "incorrect-ext"])
@pytest.mark.parametrize("forced", [True, False], ids=["forced", "not-forced"])
@pytest.mark.parametrize("exists", [True, False], ids=["file-exists", "new-file"])
def test_get_image_path(tmpdir, image_name, forced, exists):
	music_path = join(str(tmpdir), "test_file.mp3")
	mock_logger = Mock()
	result = None
	if image_name is not None:
		user_path = join(str(tmpdir), image_name)
		real_path = user_path if forced else join(str(tmpdir), "test_file.jpg")
	else:
		user_path = None
		real_path = join(str(tmpdir), "test_file.jpg")

	if exists:
		open(real_path, "a").close()

	if (not exists) or (exists and forced):
		result = real_path

	assert get_image_path(mock_logger, music_path, user_path, "jpg", forced) == result


@pytest.mark.parametrize("supported_format", [True, False], ids=["supported-format", "unsupported-format"])
@patch("apic_tool.extraction.write_to_disk")
def test_extract_image(mock_write, supported_format, tmpdir):
	mock_logger = Mock()
	audio_path = join(TEST_DATA, "test_extract.mp3" if supported_format else "test_extract.xyz")
	cover_location = join(str(tmpdir), "test_extract.png")

	with open(join(TEST_DATA, "test_cover.png"), "rb") as f:
		expected_cover = f.read()

	extract_image(mock_logger, audio_path, cover_location, False, False)

	if supported_format:
		mock_write.assert_called_once_with(mock_logger, cover_location, expected_cover)
	else:
		mock_write.assert_not_called()
		mock_logger.info.assert_called_once_with("File %s is not a supported music file", audio_path)
