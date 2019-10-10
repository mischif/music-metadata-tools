# encoding: utf-8

################################################################################
#                                 id3autosort                                  #
#  A collection of tools for manipulating and interacting with music metadata  #
#                     (C) 2009-10, 2015, 2019 Jeremy Brown                     #
#       Released under version 3.0 of the Non-Profit Open Source License       #
################################################################################

from __future__ import unicode_literals

import re

from argparse import ArgumentParser, ArgumentTypeError
from logging import (
	DEBUG,
	ERROR,
	Formatter,
	getLogger,
	INFO,
	StreamHandler,
	WARNING,
	)
from os import access, makedirs, walk, R_OK, sep, W_OK
from os.path import abspath, expanduser, isdir, join
from shutil import move
from sys import argv
from unicodedata import normalize

from mutagen import File

from id3autosort import __version__


log = getLogger(__file__)
PATH_CHARS = re.compile("[/\\\\]")
WINDOWS_UNSAFE_CHARS = re.compile("[:<>\"\*\?\|]")


class CustomLogs(Formatter):
	FORMATS = {
		ERROR:		"[-] %(message)s",
		WARNING:	"[~] %(message)s",
		INFO:		"[*] %(message)s",
		DEBUG:		"[.] %(message)s",
		}

	def __init__(self):
		super(CustomLogs, self).__init__()

	def format(self, record):
		log_style = getattr(self, "_style", self)
		log_style._fmt = self.FORMATS.get(record.levelno, self.FORMATS[DEBUG])
		return super(CustomLogs, self).format(record)


def normalize_tags(md, windows_safe):
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


	log.debug("Original tags: %s", raw_tags)

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
			log.debug("Skipping empty tag %s", k)
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

	log.debug("Normalized tags: %s", normalized)
	return normalized


def get_music_files(music_dir):
	valid_files = []

	for (basedir, dirs, basenames) in walk(music_dir):
		maybe_valid = [join(basedir, name) for name in basenames]

		for path in maybe_valid:
			try:
				log.debug("Attempting to parse %s", path)
				parsed_file = File(path, easy=True)
			except Exception as e:
				log.info("Exception attempting to read file %s: %s", path, e)
			else:
				if parsed_file is None:
					log.debug("File %s has no music metadata", path)
				else:
					valid_files.append((path, parsed_file))

	return valid_files


def get_new_path(out_dir, structure, metadata, windows_safe):
	new_path = None
	tags = normalize_tags(metadata, windows_safe)

	try:
		new_path = join(out_dir, structure.format(**tags))
	except Exception as e:
		log.debug("Error making new path: %s", e)
	else:
		log.debug("Subdirectory structure for file: %s", new_path)

	return new_path


def sort(in_dir, out_dir, structure, windows_safe, dry_run):
	files_with_metadata = get_music_files(in_dir)

	if not len(files_with_metadata):
		log.info("No music files in %s", in_dir)

	for (file_path, metadata) in files_with_metadata:
		new_path = get_new_path(out_dir, structure, metadata, windows_safe)

		if new_path is None:
			log.info("File %s does not have tags to fulfill specified structure, skipping",
					 file_path)
			continue
		else:
			log.debug("Moving file %s to %s", file_path, new_path)

			if not dry_run:
				try:
					makedirs(new_path, 0o755)
				except Exception as e:
					# It's fine if the directory already exists
					if getattr(e, "errno", None) != 17:
						log.info("Could not create destination folders for file %s: %s",
								 file_path, e)

				if isdir(new_path):
					try:
						move(file_path, new_path)
					except Exception as e:
						log.info("Could not move file %s to new location: %s", file_path, e)


def parse_args(arg_list):
	def _absolute_writable_path(path):
		expanded_path = abspath(expanduser(path))

		if not isdir(expanded_path):
			raise ArgumentTypeError("The given path is not a directory: {0}".format(expanded_path))

		if not access(expanded_path, R_OK | W_OK):
			raise ArgumentTypeError("User cannot read/write to the directory: {0}".format(expanded_path))

		return expanded_path


	def _directory_structure(raw_structure):
		expanded_structure = []
		subs = {"r": "{artist}", "l": "{album}", "d": "{date}", "g": "{genre}"}
		split_structure = [level for level in raw_structure.split(sep) if level != ""]

		for level in split_structure:
			pattern = re.compile("|".join(subs.keys()))
			expanded_structure.append(pattern.sub(lambda x: subs[x.group(0)], level))

		return sep.join(expanded_structure)


	parser = ArgumentParser(
		prog = "id3autosort",
		epilog = "(C) 2009-10, 2015, 2019 Mischif; Released under Non-Profit Open Source License version 3.0",
		description = "Organizes MP3 libraries based on each track's ID3 information."
		)

	parser.add_argument("src_paths",
						type=_absolute_writable_path,
						metavar="input_path",
						nargs="+",
						help="Directory containing audio files to organize"
						)

	parser.add_argument("dest_path",
						type=_absolute_writable_path,
						metavar="output_path",
						help="Directory audio files should be sorted into"
						)

	parser.add_argument("-s", "--structure",
						type=_directory_structure,
						default=sep.join(["r", "l"]),
						help = "Specify structure used to organize sorted MP3s")

	parser.add_argument("-u", "--windows-unsafe",
						dest="windows_safe",
						action="store_false",
						help=("Use all characters in metadata for new directories, "
							  "including ones Windows filesystems normally choke on")
						)

	parser.add_argument("-v", "--verbose",
						action="store_true",
						help="Increase logging verbosity")

	parser.add_argument("-n", "--dry-run",
						action="store_true",
						help="Simulate the actions instead of actually doing them"
						)

	parser.add_argument("--version",
						action="version",
						version="%(prog)s {}".format(__version__))

	args = parser.parse_args(arg_list)
	
	return args


def main():
	args = parse_args(argv[1:])

	log.setLevel(DEBUG if args.verbose else INFO)
	log_hdlr = StreamHandler()
	log_hdlr.setFormatter(CustomLogs())
	log.addHandler(log_hdlr)

	log.debug("Dry run: %s", args.dry_run)
	for path in args.src_paths:
		log.debug("Source path: %s", path)
	log.debug("Destination structure: %s%s%s", args.dest_path, sep, args.structure)
	log.debug("Windows-safe directories: %s", args.windows_safe)

	for path in args.src_paths:
		sort(path, args.dest_path, args.structure, args.windows_safe, args.dry_run)
