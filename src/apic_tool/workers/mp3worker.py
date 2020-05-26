# encoding: utf-8

################################################################################
#                                  apic-tool                                   #
#       Insert cover images to and extract cover images from music files       #
#                       (C)2015-16, 2019-20 Jeremy Brown                       #
#       Released under version 3.0 of the Non-Profit Open Source License       #
################################################################################

from errno import EACCES
from imghdr import what
from mimetypes import guess_type

import builtins

from mutagen import MutagenError
from mutagen.id3 import ID3, APIC
from mutagen.mp3 import MP3

from apic_tool.workers.baseworker import BaseWorker


SUPPORTED_EXTENSIONS = ["mp3"]


class MP3Worker(BaseWorker):
	@staticmethod
	def supported_extensions():
		"""
		All the extensions relating to the music this worker can manipulate.

		:returns: (list) Strings representing file extensions
						 this worker can handle
		"""
		return SUPPORTED_EXTENSIONS

	@staticmethod
	def load_file(logger, path):
		"""
		Obtain ID3 data for the given file.

		:param logger: (Logger) Logging object
		:param path: (str) Absolute path to MP3 file

		:returns: (MP3/None) None if there was a major issue loading metadata,
							 MP3 object otherwise
		"""
		music = None

		try:
			music = MP3(path)
		except MutagenError as e:
			orig_e = e.args[0]
			if isinstance(orig_e, getattr(builtins, "PermissionError", IOError)) and orig_e.errno == EACCES:
				logger.info("Permission denied attempting to access file %s", path)
			else:
				logger.info("Error trying to load %s as MP3 file: %s", path, str(orig_e))

		return music

	@staticmethod
	def get_image_data(logger, path):
		"""
		Extract the image data from the given file.

		:param logger: (Logger) Logging object
		:param path: (str) Absolute path to music file

		:returns: (tuple) (None, None) if no image data in file,
						  (bytes, str) Image data from file,
						  			   determined extension of data
		"""
		data = None
		ext = None
		music = MP3Worker.load_file(logger, path)

		if music is not None:
			if music.info.sketchy:
				logger.warning("Couldn't load file %s cleanly", path)

			if not music.tags:
				logger.info("No tags in file %s, skipping", path)
			else:
				images = music.tags.getall("APIC")

				if images:
					data = images[0].data
					ext = what(path, data)

		return (data, ext)

	@staticmethod
	def can_insert_image(logger, path, forced):
		"""
		Determine if it is possible to insert an image into the given file.

		:param logger: (Logger) Logging object
		:param path: (str) Absolute path to music file
		:param forced: (bool) Whether issues should be overlooked when trying to insert image

		:returns: (bool) True if it is possible to insert image, False otherwise
		"""
		result = forced
		music = MP3Worker.load_file(logger, path)

		if music is not None and not forced:
			if music.info.sketchy:
				logger.warning("Couldn't load file %s cleanly, skipping", path)

			elif not music.tags:
				logger.info("No tags in file %s, skipping", path)

			else:
				result = True

		return result

	@staticmethod
	def write_to_metadata(logger, music_path, cover_path, forced):
		"""
		Write a given image to a given music file.

		:param logger: (Logger) Logging object
		:param music_path: (str) Absolute path to music file
		:param cover_path: (str) Absolute path to image to write to music file
		:param forced: (bool) Whether issues should be overlooked when trying to insert image
		"""
		result = False
		music = MP3Worker.load_file(logger, music_path)

		if music is not None:
			if music.info.sketchy:
				if not forced:
					return result
				else:
					logger.debug("Forced to continue with file %s despite unclean load", music_path)

			if not music.tags:
				if not forced:
					return result
				else:
					logger.debug("Forced to create metadata for file %s, which has none", music_path)
					music.add_tags()

			images = music.tags.getall("APIC")

			if images and not forced:
				logger.info("File %s already has embedded image, skipping", music_path)
				result = True

			else:
				if images:
					logger.info("Forced to remove pre-existing APIC tags for file %s", music_path)
					music.tags.delall("APIC")

				tag_version = (music.tags.version[0], music.tags.version[1])
				old_tags = True if tag_version < (2, 3) else False
				logger.debug("Tags are version %d.%d", *tag_version)

				if old_tags:
					logger.debug("Upgrading tags for file %s to v2.3", music_path)
					music.tags.update_to_v23()

				mimetype = guess_type(cover_path)[0]
				logger.debug("Supposed mimetype for image: %s", mimetype)

				with open(cover_path, "rb") as cover:
					tag = APIC(
							   encoding=3,			# UTF-8
							   type=3,				# Cover image
							   mime=mimetype,
							   data=cover.read(),
							   )

					logger.debug("Adding image to file")
					music.tags.add(tag)

				logger.info("Saving updated tags")
				try:
					music.tags.save(music_path, v2_version=3 if old_tags else tag_version[1])
				except Exception as e:
					logger.info("Error saving tags for file %s: %s", music_path, str(e))
				else:
					result = True

			return result
