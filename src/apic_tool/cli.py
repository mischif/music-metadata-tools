# encoding: utf-8

################################################################################
#                                  apic-tool                                   #
#       Insert cover images to and extract cover images from music files       #
#                       (C)2015-16, 2019-20 Jeremy Brown                       #
#       Released under version 3.0 of the Non-Profit Open Source License       #
################################################################################

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
from os import access, walk, R_OK, W_OK
from os.path import abspath, dirname, expanduser, isdir, isfile
from sys import argv

from apic_tool import __version__, SUPPORTED_IMAGES, SUPPORTED_MUSIC
from apic_tool.extraction import extract_image
from apic_tool.insertion import insert_image


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


class AbsoluteAccessiblePaths(Action):
	def __call__(self, parser, namespace, values, option_string=None):
		if values != None:
			out = getattr(namespace, self.dest, [])
			if out is None:
				out = []

			# Remember each item in an option list is passed through the action individually
			if isinstance(values, list):
				values = values[0]
			expanded_path = abspath(expanduser(values))

			# Confirm file paths point to files and directory paths point to directories
			# Since the path pointed to by extract_pic may not currently exist, don't raise
			# if it doesn't
			if self.dest == "extract_pic":
				pass
			elif self.dest in ["insert_files", "insert_pic", "extract_music"]:
				if not isfile(expanded_path):
					raise ArgumentTypeError("The given path is not a file: {0}".format(expanded_path))
			else:
				if not isdir(expanded_path):
					raise ArgumentTypeError("The given path is not a directory: {0}".format(expanded_path))

			# Confirm this is a supported image
			if self.dest == "insert_pic":
				if expanded_path.rsplit(".", 1)[1].lower() not in SUPPORTED_IMAGES:
					raise ArgumentTypeError("Unsupported image type: {0}".format(expanded_path))

			# Confirm this is a supported music file
			if self.dest == "extract_music":
				if expanded_path.rsplit(".", 1)[1].lower() not in SUPPORTED_MUSIC:
					raise ArgumentTypeError("Unsupported music type: {0}".format(expanded_path))


			if self.dest in ["insert_dirs", "insert_files"]:
				out.append(expanded_path)
			else:
				out = expanded_path

			setattr(namespace, self.dest, out)


def parse_args(**kwargs):
	"""
	Read arguments from stdin while validating and performing any necessary conversions

	:returns: (Namespace) Tool arguments
	"""
	main_parser = ArgumentParser(
		prog = "apic-tool",
		description = "Inserts and extracts cover images to/from music files.",
		epilog = "(C) 2015-16, 2019-20 Jeremy Brown; released under Non-Profit Open Source License version 3.0"
		)

	main_parser.add_argument("-n", "--dry-run",
							 action="store_true",
							 help="Simulate the actions instead of actually doing them"
							 )

	main_parser.add_argument("-v", "--verbose",
							 action="store_true",
							 help="Increase logging verbosity")

	main_parser.add_argument("--force",
							 action="store_true",
							 dest="force",
							 help="Whether or not the tool should allow things to happen that may have complications")

	main_parser.add_argument("--version",
							 action="version",
							 version="%(prog)s {}".format(__version__))


	tool_actions = main_parser.add_subparsers(title="Actions", metavar="")
	extract_parser = tool_actions.add_parser("extract", help="Extract image from a music file")
	extract_parser.set_defaults(action="extract")
	insert_parser = tool_actions.add_parser("insert", help="Insert image into a music file")
	insert_parser.set_defaults(action="insert")
	insert_arg = insert_parser.add_mutually_exclusive_group(required=True)

	insert_arg.add_argument("-d", "--dir",
							action=AbsoluteAccessiblePaths,
							dest="insert_dirs",
							metavar="DIR",
							nargs="+",
							help="Director(y|ies) containing files to manipulate"
							)

	insert_arg.add_argument("-f", "--file",
							action=AbsoluteAccessiblePaths,
							dest="insert_files",
							nargs="+",
							help="Input file to manipulate"
							)

	insert_parser.add_argument("-p", "--pic",
							   action=AbsoluteAccessiblePaths,
							   dest="insert_pic",
							   help="Image to insert",
							   required=True
							   )

	insert_parser.add_argument("-k", "--keep",
							   action="store_true",
							   dest="keep_pic",
							   help="Don't delete image after inserting it"
							   )

	extract_parser.add_argument("extract_music",
								action=AbsoluteAccessiblePaths,
								help="File to extract image from"
								)

	extract_parser.add_argument("extract_pic",
								action=AbsoluteAccessiblePaths,
								default=None,
								nargs="?",
								help="Filename to send extracted image to"
								)

	return main_parser.parse_args(kwargs.get("argv", argv[1:]))


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
	logger.debug("Forcing: %s", args.force)

	if args.action == "extract":
		logger.debug("Extraction file: %s", args.extract_music)
		logger.debug("Extraction result: %s", args.extract_pic)
		extract_image(logger, args.extract_music, args.extract_pic, args.dry_run, args.force)
	else:
		logger.debug("Insertion files: %s", args.insert_files)
		logger.debug("Insertion directories: %s", args.insert_dirs)
		logger.debug("Cover to insert: %s", args.insert_pic)
		logger.debug("Keep covers after insertion: %s", args.keep_pic)
		insert_image(logger, args.insert_pic, args.insert_dirs, args.insert_files, args.keep_pic, args.dry_run, args.force)
