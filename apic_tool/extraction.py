# encoding: utf-8

################################################################################
#                                  apic-tool                                   #
#       Insert cover images to and extract cover images from music files       #
#                           (C) 2015-16, 2019 Mischif                          #
#       Released under version 3.0 of the Non-Profit Open Source License       #
################################################################################

from errno import EACCES
from os.path import isfile

from apic_tool.workers import get_format_worker


def write_to_disk(logger, path, data):
	try:
		with open(path, "wb") as image:
			image.write(data)
	except IOError as e:
		if e.errno == EACCES:
			logger.info("Permission denied attempting to write image %s", path)
		else:
			raise


def fuzzy_match(user_ext, worker_ext):
	extensions = {
		"gif": ["gif"],
		"jpg": ["jpg", "jpeg"],
		"jpeg": ["jpg", "jpeg"],
		"png": ["png"],
		}

	return worker_ext in extensions[user_ext]


def get_image_path(logger, music_path, image_path, worker_ext, forced):
	path = None

	# If the user didn't pass in a path for the extracted image,
	# use the name of the music file with the correct extension
	if image_path is None:
		image_path = ".".join([music_path.rsplit(".", 1)[0], worker_ext])
		logger.debug("User did not provide path for image of file %s", music_path)
		logger.debug("Setting image output path to %s", image_path)

	# Otherwise determine if changing what the user provided is necessary
	else:
		user_ext = image_path.rsplit(".", 1)[1]

		if not fuzzy_match(user_ext, worker_ext):
			logger.debug("Image extension provided by user: %s", user_ext)
			logger.debug("Image extension determined by worker: %s", worker_ext)

			if forced:
				logger.debug("Being forced to use user-provided path")
			else:
				image_path = ".".join([image_path.rsplit(".", 1)[0], worker_ext])
				logger.debug("Changing image output path to %s", image_path)

	# Next, determine if you are required to and allowed to overwrite existing files
	if isfile(image_path):
		logger.info("Image %s already exists", image_path)

		if forced:
			logger.info("Being forced to overwrite")
			path = image_path
		else:
			logger.info("Not overwriting existing file; skipping")
	else:
		path = image_path

	return path


def extract_image(logger, music_path, cover_path, dry_run, forced):
	worker = get_format_worker(music_path)

	if worker is None:
		logger.info("File %s is not a supported music file", music_path)
		return

	(image_data, worker_ext) = worker.get_image_data(logger, music_path)
	cover_path = get_image_path(logger, music_path, cover_path, worker_ext, forced)

	if cover_path is not None:
		logger.debug("Writing image data from %s to %s", music_path, cover_path)
		if not dry_run:
			write_to_disk(logger, cover_path, image_data)
