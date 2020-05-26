# encoding: utf-8

################################################################################
#                                  apic-tool                                   #
#       Insert cover images to and extract cover images from music files       #
#                       (C)2015-16, 2019-20 Jeremy Brown                       #
#       Released under version 3.0 of the Non-Profit Open Source License       #
################################################################################

from errno import EACCES
from os.path import isfile

from apic_tool.workers import get_format_worker


def write_to_disk(logger, path, data):
	"""
	Write the given data to the given location.

	:param logger: (Logger) Logging object
	:param path: (str) Absolute path to write data to
	:param data: (bytes) Data to write to a file
	"""
	try:
		with open(path, "wb") as image:
			image.write(data)
	except IOError as e:
		if e.errno == EACCES:
			logger.info("Permission denied attempting to write image %s", path)
		else:
			raise


def fuzzy_match(user_ext, worker_ext):
	"""
	Check if the extensions the user provided and the worker determined
	refer to the same format, even if they aren't the same.

	:param user_ext: (str) User-provided extension for output picture
	:param worker_ext: (str) Extension determined by worker for picture

	:returns: True if extensions refer to the same format, False otherwise
	"""
	extensions = {
		"gif": ["gif"],
		"jpg": ["jpg", "jpeg"],
		"jpeg": ["jpg", "jpeg"],
		"png": ["png"],
		}

	return worker_ext in extensions[user_ext]


def get_image_path(logger, music_path, image_path, worker_ext, forced):
	"""
	Determine the path to store the extracted image to if one was not provided,
	Confirm the user's provided extension matches the one determined to represent
	the picture is a path was provided.

	:param logger: (Logger) Logging object
	:param music_path: (str) Absolute path to music file
	:param image_path: (str/None) Absolute path to store extracted image
	:param worker_ext: (str) Extension worker believes matches the picture
	:param forced: (bool) Whether or not to force using the user's extension,
						  even if it does not match the image format

	:returns: None if there was an error confirming the desired location,
			  String representing absolute path to store image otherwise
	"""
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
	"""
	Dispatch function handling extracting cover image from music files.

	:param logger: (Logger) Logging object
	:param music_path: (str) Absolute path to music file
	:param cover_path: (str/None) Desired path to store extracted image
	:param dry_run: (bool) Whether or not to actually write images to disk
	:param forced: (bool) Whether or not the tool should do things it doesn't
						  believe are beneficial
	"""
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
