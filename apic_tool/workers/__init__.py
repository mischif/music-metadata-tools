# encoding: utf-8

################################################################################
#                                  apic-tool                                   #
#       Insert cover images to and extract cover images from music files       #
#                           (C) 2015-16, 2019 Mischif                          #
#       Released under version 3.0 of the Non-Profit Open Source License       #
################################################################################

from apic_tool.workers.mp3worker import MP3Worker

VALID_WORKERS = [MP3Worker]

EXTENSION_WORKER_MAPPING = {
	ext: worker
	for worker in VALID_WORKERS
	for ext in worker.supported_extensions()
	}

SUPPORTED_MUSIC = [ext for worker in VALID_WORKERS for ext in worker.supported_extensions()]

def get_format_worker(path):
	extension = path.rsplit(".", 1)[1]
	return EXTENSION_WORKER_MAPPING.get(extension)
