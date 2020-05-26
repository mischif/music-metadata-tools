# encoding: utf-8

################################################################################
#                                  apic-tool                                   #
#       Insert cover images to and extract cover images from music files       #
#                       (C)2015-16, 2019-20 Jeremy Brown                       #
#       Released under version 3.0 of the Non-Profit Open Source License       #
################################################################################

from os import listdir, remove
from os.path import isfile, join

from apic_tool.workers import get_format_worker


def get_music_files(logger, files, dirs, forced):
	"""
	Obtain a list of all music files among the provided files and directories
	that the tool is capable of adding images to.

	:param logger: (Logger) Logging object
	:param files: (list) Strings representing absolute paths to music files
	:param dirs: (list) Strings representing absulte paths to directories
						containing music files
	:param forced: (bool) Whether or not the tool should allow things to happen
						  that may have complications

	:returns: (list) Strings representing absolute paths to manipulable music files
	"""
	valid_files = []
	paths = []

	if files is not None:
		paths.extend(files)

	if dirs is not None:
		for dirfiles in [list(filter(isfile, map(lambda f: join(d, f), listdir(d)))) for d in dirs]:
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
	"""
	Dispatch function handling qualifying files to insert images into
	and actually performing insertion.

	:param logger: (Logger) Logging object
	:param cover_path: (str) Absolute path to cover to insert into music files
	:param insertion_dirs: (list) Strings representing absolute paths to dirs
								  possibly containing music files
	:param insertion_files: (list) Strings representing absolute paths to
								   music files for possible insertion
	:param keep_cover: (bool) Whether or not to keep the inserted cover in the
							  event of success
	:param dry_run: (bool) Whether or not to perform the actual insertion of
						   images into files and deletion of cover afterwards
	:param forced: (bool) Whether or not the tool should allow things to happen
						  that may have complications
	"""
	result = True

	music_files = get_music_files(logger, insertion_files, insertion_dirs, forced)

	if music_files:
		for track in music_files:
			logger.debug("Writing image %s to file %s", cover_path, track)
			if not dry_run:
				worker = get_format_worker(track)
				result &= worker.write_to_metadata(logger, track, cover_path, forced)

		if result and not keep_cover:
			logger.info("Deleting image file %s", cover_path)
			if not dry_run:
				remove(cover_path)
