# encoding: utf-8

################################################################################
#                                  apic-tool                                   #
#       Insert cover images to and extract cover images from music files       #
#                           (C) 2015-16, 2019 Mischif                          #
#       Released under version 3.0 of the Non-Profit Open Source License       #
################################################################################

from os import listdir, remove
from os.path import join

from apic_tool.workers import get_format_worker


def get_music_files(logger, files, dirs, forced):
	valid_files = []
	paths = []

	if files is not None:
		paths.extend(files)

	if dirs is not None:
		for dirfiles in [list(map(lambda f: join(d, f), listdir(d))) for d in dirs]:
			paths.extend(dirfiles)

	for path in paths:
		worker = get_format_worker(path)

		if worker is None:
			logger.debug("File %s is not a supported music file, skipping", path)
			continue

		if worker.can_insert_image(logger, path, forced):
			valid_files.append(path)

	return valid_files


def insert_image(logger, cover_path, insertion_dirs, insertion_files, keep_cover, dry_run, forced):
		result = True

		music_files = get_music_files(logger, insertion_files, insertion_dirs, forced)

		if music_files:
			for track in music_files:
				logger.info("Writing image %s to file %s", cover_path, track)
				if not dry_run:
					worker = get_format_worker(track)
					result &= worker.write_to_metadata(logger, track, cover_path, forced)

			if result and not keep_cover:
				logger.info("Deleting image file %s", cover_path)
				if not dry_run:
					remove(cover_path)
