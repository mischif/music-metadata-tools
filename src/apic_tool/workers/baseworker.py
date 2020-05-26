# encoding: utf-8

################################################################################
#                                  apic-tool                                   #
#       Insert cover images to and extract cover images from music files       #
#                       (C)2015-16, 2019-20 Jeremy Brown                       #
#       Released under version 3.0 of the Non-Profit Open Source License       #
################################################################################

from abc import ABCMeta, abstractmethod

ABC = ABCMeta('ABC', (object,), {})

class BaseWorker(ABC):
	@staticmethod
	@abstractmethod
	def supported_extensions():
		"""
		All the extensions relating to the music this worker can manipulate.

		:returns: (list) Strings representing file extensions
						 this worker can handle
		"""
		raise NotImplementedError("Implement me")

	@staticmethod
	@abstractmethod
	def get_image_data(logger, path):
		"""
		Extract the image data from the given file.

		:param logger: (Logger) Logging object
		:param path: (str) Absolute path to music file

		:returns: (tuple) (None, None) if no image data in file,
						  (bytes, str) Image data from file,
						  			   determined extension of data
		"""
		raise NotImplementedError("Implement me")

	@staticmethod
	@abstractmethod
	def can_insert_image(logger, path, forced):
		"""
		Determine if it is possible to insert an image into the given file.

		:param logger: (Logger) Logging object
		:param path: (str) Absolute path to music file
		:param forced: (bool) Whether issues should be overlooked when trying to insert image

		:returns: (bool) True if it is possible to insert image, False otherwise
		"""
		raise NotImplementedError("Implement me")

	@staticmethod
	@abstractmethod
	def write_to_metadata(logger, music_path, cover_path, forced):
		"""
		Write a given image to a given music file.

		:param logger: (Logger) Logging object
		:param music_path: (str) Absolute path to music file
		:param cover_path: (str) Absolute path to image to write to music file
		:param forced: (bool) Whether issues should be overlooked when trying to insert image
		"""
		raise NotImplementedError("Implement me")
