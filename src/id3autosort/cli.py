# encoding: utf-8

################################################################################
#                                 id3autosort                                  #
#                      Sort audio files based on metadata                      #
#                    (C)2009-10, 2015, 2019-20 Jeremy Brown                    #
#       Released under version 3.0 of the Non-Profit Open Source License       #
################################################################################

import re

from argparse import Action, ArgumentParser, ArgumentTypeError
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
from sys import argv

from id3autosort import __version__
from id3autosort.sorter import sort


logger = getLogger(__file__)


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


def parse_args(**kwargs):
	"""
	Read arguments from stdin while validating and performing any necessary conversions

	:returns: (Namespace) Tool arguments
	"""
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
		epilog = "(C) 2009-10, 2015, 2019-20 Jeremy Brown; Released under Non-Profit Open Source License version 3.0",
		description = "Organize music libraries based on each track's metadata."
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
						help="Don't actually move music files"
						)

	parser.add_argument("--version",
						action="version",
						version="%(prog)s {}".format(__version__))

	args = parser.parse_args(kwargs.get("argv", argv[1:]))
	
	return args


def main():
	"""
	Tool entry point
	"""
	args = parse_args()

	logger.setLevel(DEBUG if args.verbose else INFO)
	log_hdlr = StreamHandler()
	log_hdlr.setFormatter(CustomLogs())
	logger.addHandler(log_hdlr)

	logger.debug("Dry run: %s", args.dry_run)
	for path in args.src_paths:
		logger.debug("Source path: %s", path)
	logger.debug("Destination structure: %s%s%s", args.dest_path, sep, args.structure)
	logger.debug("Windows-safe directories: %s", args.windows_safe)

	for path in args.src_paths:
		sort(logger, path, args.dest_path, args.structure, args.windows_safe, args.dry_run)
