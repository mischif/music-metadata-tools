# encoding: utf-8

################################################################################
#                                  apic-tool                                   #
#       Insert cover images to and extract cover images from music files       #
#                           (C) 2015-16, 2019 Mischif                          #
#       Released under version 3.0 of the Non-Profit Open Source License       #
################################################################################

from errno import EACCES
from imghdr import what
from mimetypes import guess_type

from mutagen import MutagenError
from mutagen.id3 import ID3, APIC
from mutagen.mp3 import MP3

from apic_tool.workers.baseworker import BaseWorker


SUPPORTED_EXTENSIONS = ["mp3"]


class MP3Worker(BaseWorker):
	@staticmethod
	def supported_extensions():
		return SUPPORTED_EXTENSIONS

	@staticmethod
	def load_file(logger, path):
		music = None

		try:
			music = MP3(path)
		except MutagenError as e:
			if isinstance(e.message, IOError) and e.message.errno == EACCES:
				logger.info("Permission denied attempting to access file %s", path)
			else:
				logger.info("Error trying to load %s as MP3 file: %s", path, str(e))

		return music

	@staticmethod
	def get_image_data(logger, path):
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