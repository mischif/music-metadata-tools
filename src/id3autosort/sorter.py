# encoding: utf-8

################################################################################
#                                 id3autosort                                  #
#                      Sort audio files based on metadata                      #
#                    (C)2009-10, 2015, 2019-20 Jeremy Brown                    #
#       Released under version 3.0 of the Non-Profit Open Source License       #
################################################################################

import re

from os import makedirs, walk
from os.path import isdir, join
from shutil import move
from unicodedata import normalize

from mutagen import File


PATH_CHARS = re.compile("[/\\\\]")
WINDOWS_UNSAFE_CHARS = re.compile("[:<>\"\*\?\|]")


def normalize_tags(logger, md, windows_safe):
	"""
	Modify or remove characters in tags that would cause issues when stored on a filesystem.
	Additionally, handle formats Mutagen recognizes but does not have an easy-mode version for,
	creating one for use by downstream consumers.

	:param logger: (Logger) Logging object
	:param md: Mutagen metadata structure
	:param windows_safe: (bool) Whether or not to perform extra normalization for Windows platforms

	:returns: (dict) A normalized dict of tags
	"""
	normalized = {}

	def _structure_aiff_tags(tags):
		structured = {}

		mapping = {
			"TALB": "album",
			"TCON": "genre",
			"TDRC": "date",
			"TIT2": "title",
			"TPE1": "artist",
			"TRCK": "tracknumber",
			}

		for m in filter(lambda t: t in tags, mapping.keys()):
			structured[mapping[m]] = tags[m].text

		return structured

	def _structure_wma_tags(tags):
		structured = {}

		mapping = {
			"Author": "artist",
			"Title": "title",
			"WM/AlbumTitle": "album",
			"WM/Genre": "genre",
			"WM/TrackNumber": "tracknumber",
			"year": "date",
			}

		for m in filter(lambda t: t in tags, mapping.keys()):
			structured[mapping[m]] = tags[m][0].value

		return structured

	# Mutagen doesn't have easy mode for all audio formats,
	# convert those certain formats' tags to easy mode manually
	unstructured_mimes = {"audio/aiff": _structure_aiff_tags, "audio/x-wma": _structure_wma_tags}
	unstructured = list(filter(lambda m: m in md.mime, unstructured_mimes.keys()))
	if unstructured:
		raw_tags = unstructured_mimes[unstructured[0]](md.tags)
	else:
		raw_tags = md.tags


	logger.debug("Original tags: %s", raw_tags)

	# Since there can be multiple entries per tag,
	# tag values are lists instead of a simple string;
	# Just use the first value even if it is a multi-item tag
	# Encode/decode combo because date value might not be a string
	for (k, v) in raw_tags.items():
		if isinstance(v, list):
			this_value = v[0].encode("utf-8").decode("utf-8")
		else:
			this_value = v.encode("utf-8").decode("utf-8")

		# Skip empty tags
		if not this_value:
			logger.debug("Skipping empty tag %s", k)
			continue

		# Explicitly replace backslashes and forward slashes with underscores
		# regardless of platform
		this_value = PATH_CHARS.sub("_", this_value)

		if windows_safe:
			# Remove the other characters Windows doesn't like
			this_value = WINDOWS_UNSAFE_CHARS.sub("", this_value)

			# Convert characters the furriners use to good-ol' 'MURICAN letters
			# NTFS is probably fine, but FAT32 ruins everything good in this world
			this_value = normalize("NFD", this_value).encode("ascii", "ignore").decode("ascii")

			# Unix-based OSs are fine with an NTFS directory ending with a period,
			# but Windows will refuse to open them,
			# so make sure directories don't end in a period for Windows-safety
			if this_value[-1] == ".":
				this_value = this_value[:-1]

		normalized[k] = this_value

	logger.debug("Normalized tags: %s", normalized)
	return normalized


def get_music_files(logger, music_dir):
	"""
	Obtain a list of all music files Mutagen can read metadata for inside the given directory.

	:param logger: (logger) Logging object
	:param music_dir: (str) Absolute path to directory to check for music files

	:returns: (list) All music files Mutagen can read metadata for inside the given directory
	"""
	valid_files = []

	for (basedir, dirs, basenames) in walk(music_dir):
		maybe_valid = [join(basedir, name) for name in basenames]

		for path in maybe_valid:
			try:
				logger.debug("Attempting to parse %s", path)
				parsed_file = File(path, easy=True)
			except Exception as e:
				logger.info("Exception attempting to read file %s: %s", path, e)
			else:
				if parsed_file is None:
					logger.debug("File %s has no music metadata", path)
				else:
					valid_files.append((path, parsed_file))

	return valid_files


def get_new_path(logger, out_dir, structure, metadata, windows_safe):
	"""
	Determine the new location the given file should be located,
	based upon the file's metadata and the provided folder structure.

	:param logger: (Logger) Logging object
	:param out_dir: (str) Root directory the file should be moved to
	:param structure: (str) Desired structure for music files inside root directory
	:param metadata: Mutagen metadata structure for given file
	:param windows_safe: (bool) Whether or not to perform extra normalization for Windows platforms

	:returns: None if there was an error determining the new location,
			  a string representing an absolute path otherwise.
	"""
	new_path = None
	tags = normalize_tags(logger, metadata, windows_safe)

	try:
		new_path = join(out_dir, structure.format(**tags))
	except Exception as e:
		logger.debug("Error making new path: %s", e)
	else:
		logger.debug("Subdirectory structure for file: %s", new_path)

	return new_path


def sort(logger, in_dir, out_dir, structure, windows_safe, dry_run):
	"""
	Main function handling finding music, finding the location said music
	should be moved to, and moving it.

	:param logger: (Logger) Logging object
	:param in_dir: (str) Absolute path to music source directory
	:param out_dir: (str) Absolute path to music destination directory
	:param windows_safe: (bool) Whether or not to perform extra normalization for Windows platforms
	:param dry_run: (bool) Whether or not to perform actual movement of files
	"""
	files_with_metadata = get_music_files(logger, in_dir)

	if not len(files_with_metadata):
		logger.info("No music files in %s", in_dir)

	for (file_path, metadata) in files_with_metadata:
		new_path = get_new_path(logger, out_dir, structure, metadata, windows_safe)

		if new_path is None:
			logger.info("File %s does not have tags to fulfill specified structure, skipping",
					 file_path)
			continue
		else:
			logger.debug("Moving file %s to %s", file_path, new_path)

			if not dry_run:
				try:
					makedirs(new_path, 0o755)
				except Exception as e:
					# It's fine if the directory already exists
					if getattr(e, "errno", None) != 17:
						logger.info("Could not create destination folders for file %s: %s",
								 file_path, e)

				if isdir(new_path):
					try:
						move(file_path, new_path)
					except Exception as e:
						logger.info("Could not move file %s to new location: %s", file_path, e)
