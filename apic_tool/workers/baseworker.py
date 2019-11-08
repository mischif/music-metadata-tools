# encoding: utf-8

################################################################################
#                                  apic-tool                                   #
#       Insert cover images to and extract cover images from music files       #
#                           (C) 2015-16, 2019 Mischif                          #
#       Released under version 3.0 of the Non-Profit Open Source License       #
################################################################################

from abc import ABCMeta, abstractmethod

ABC = ABCMeta('ABC', (object,), {})

class BaseWorker(ABC):
	@staticmethod
	@abstractmethod
	def supported_extensions():
		raise NotImplementedError("Implement me")

	@staticmethod
	@abstractmethod
	def get_image_data(logger, path):
		raise NotImplementedError("Implement me")

	@staticmethod
	@abstractmethod
	def can_insert_image(logger, path, forced):
		raise NotImplementedError("Implement me")

	@staticmethod
	@abstractmethod
	def write_to_metadata(logger, music_path, cover_path, forced):
		raise NotImplementedError("Implement me")
