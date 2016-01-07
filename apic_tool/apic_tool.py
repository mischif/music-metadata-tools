#!/usr/bin/env python
# encoding: utf-8

################################################################################
#                                  apic-tool                                   #
#       Insert cover images to and extract cover images from music files       #
#                               (C) 2015 Mischif                               #
#       Released under version 3.0 of the Non-Profit Open Source License       #
################################################################################

# Support for manipulating FLAC/Ogg images
import base64
from mutagen.oggvorbis import OggVorbis
from mutagen.flac import Picture, error as FLACError

# Support for manipulating ID3 images
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC, error

import logging
import argparse
from sys import exit
from imghdr import what
from random import randrange
from functools import partial
from mimetypes import guess_type
from os import access, listdir, remove, walk, R_OK, W_OK
from os.path import abspath, expanduser, isdir, isfile, join

from apic_tool import __version__

class CustomLogs(logging.Formatter):
	FORMATS = {
	logging.DEBUG    : "[*] %(message)s",
	logging.INFO     : "[+] %(message)s",
	logging.WARNING    : "[!] %(message)s",
	logging.ERROR : "[-] %(message)s"
	}

	def format(self, record):
		self._fmt = self.FORMATS.get(record.levelno,
			self.FORMATS[logging.DEBUG])
		return logging.Formatter.format(self, record)

def GetCover(path, forced):
	goodFilenames = ["album", "cover", "folder"]

	# How many images are we working with?
	images = [f for f in listdir(path) if f.endswith(imageExts)]
	if len(images) == 1: log.debug("using sole image for cover: {}".format(join(path, images[0])))
	else: log.debug("Found images in folder: {}".format(images))

	# We should have at least one image to get here, but let's make sure
	if len(images) == 0: exit(log.error("I don't know how you managed to get here, good for you?"))
	elif len(images) == 1: return join(path, images[0])
	else:
		# Any images w/ filenames that suggest we should use them?
		goodImages = [join(path, f) for f in images if any(s in f for s in goodFilenames)]

		# Nope; we'll have to choose from one of the normal ones
		if len(goodImages) == 0:
			log.debug("No preferred images found; too many normal ones to choose from")
			chooseFrom = images

		# Just one, which is the best option
		elif len(goodImages) == 1:
			log.debug("Using sole preferred image: {}".format(goodImages[0]))
			return goodImages[0]

		# There's a bunch; we'll have to make a choice
		else:
			log.debug("Too many preferred images to choose from: {}".format(goodImages))
			chooseFrom = goodImages

		if not forced: return None
		else:
			log.debug("But we're being forced, so we'll pick one at random")
			return chooseFrom[randrange(len(chooseFrom))]
	
def ExtractImage(args):
	outFile = args.outFile

	log.debug("Input: {}".format(args.inFile))
	log.debug("Output: {}".format(outFile))
	log.debug("Use bad extensions: {}".format(args.badExt))
	log.debug("Dry run: {}".format(args.dryRun))
	log.debug("Forcing: {}".format(args.forced))

	if args.inFile.endswith(".mp3"):
		music = MP3(args.inFile)

		# Did the file load right?
		if music.info.sketchy:
			exit(log.error("Don't know why file didn't load clean; exiting"))
		else:
			# Does the file have ID3 tags?
			if not music.tags: exit(log.error("File has no ID3 tags; exiting"))
			log.debug(music.tags.pprint())

			# Does the file have an image to extract?
			if len(music.tags.getall("APIC")) == 0:
				exit(log.error("File has no image to extract; exiting"))
			imageData = music.tags.getall("APIC")[0].data
			ext = what(outFile, imageData)

			# What if the user uses the wrong extension for the image data?
			if outFile[-3:] != ext:
				log.warning("Given extension is {}".format(outFile[-3:]))
				log.debug("Determined extension is {}".format(ext))

				# If the user says it's okay...
				if not args.badExt:
					outFile = outFile.replace(outFile[-3:], ext)
					log.warning("Saving as .{} instead".format(outFile))
				else:
					log.warning("Saving as .{} since we should use bad extensions".format(outFile[-3:]))

			# Does the image we want to write to already exist?
			if isfile(outFile):
				log.info("Output file {} already exists".format(outFile))
				if args.forced:
					log.warning("But we're being forced, so we'll overwrite it")
				else:
					exit(log.error("Not being forced, so not overwriting existing file"))

			# Do the thing
			if not args.dryRun:
				with open(outFile, "wb") as f:
					f.write(imageData)

			log.info("Done!")
		exit(0)

def InsertImage(inFile, inPic, dryRun, forced):
	log.info("File: {}".format(inFile))
	log.info("Image: {}".format(inPic))

	if inFile.endswith(".mp3"):
		music = MP3(inFile)

		# Did the file load right?
		if music.info.sketchy:
			log.error("File didn't load clean; skipping")
			return False
		else:

			# Does the file have any ID3 tags at all?
			if not music.tags:
				log.info("File has no pre-existing ID3 tags, adding empty one")
				if not dryRun: music.add_tags()
			else:
				log.debug("Existing image tags: {}".format(music.tags.getall("APIC")))

				# Is there a pre-existing image tag?
				if len(music.tags.getall("APIC")) > 0:
					log.warning("File already has embedded image")

					# If so, leave if we aren't being forced
					if not forced:
						log.info("Not being forced, so skipping.")
						return True

					# If we are being forced, remove pre-existing image tag
					else:
						log.warning("But we're being forced, so we'll overwrite it")
						if not dryRun:
							log.info("Removing pre-existing APIC tag")
							music.tags.delall("APIC")

			# Create the picture tag and insert it
			mimetype = guess_type(inPic)[0]
			log.debug("Guessed mimetype for image: {}".format(mimetype))
			with open(inPic, "rb") as f:
				pic = APIC(
					encoding = 3,		# Sets UTF-8
					type = 3,				# Signifies cover image
					mime = mimetype,
					data = f.read())

				if not dryRun:
					log.info("Adding APIC tag to file")
					music.tags.add(pic)

				# Convert tags to ID3 v2.3 if necessary
				if music.tags and not dryRun:
					if music.tags.version[0] < 2 or music.tags.version[1] < 3:
						log.info("Tags are version {}.{}; converting to ID3v2.3".format(
							music.tags.version[0], music.tags.version[1]))
						music.tags.update_to_v23()

				# Save updated tags
				if dryRun: return True
				else:
					log.info("Saving updated tags")
					try:
						music.tags.save(v2_version = music.tags.version[1])
					except error:
						log.error("Error saving updated tags for file {}: {}".format(path, error))
						return False
					return True

def InsertDispatch(args):
	# Is the user trying to recurse on a single file?
	if args.inFile and args.recursive:
		exit(log.error("Cannot recurse on a single file; exiting"))

	# Did the user forget to select the image to insert into the file?
	if args.inFile and args.inPic == None:
		exit(log.error("Cannot select single file without selecting image; exiting"))

	# Is the user trying to recurse on a dir with a single image?
	if args.recursive and args.inDirs and args.inPic and not args.forced:
		exit(log.error("You'll have to use force to recursively add an image to a directory; exiting"))

	# Is the user trying to add a single image to files in multiple directories?
	if args.inDirs and len(args.inDirs) > 1 and args.inPic and not args.forced:
		exit(log.error("You'll have to use force to add an image to multiple directories; exiting"))

	inFile = args.inFile
	inDirs = args.inDirs
	inPic = args.inPic
	keepPic = args.keepPic
	recursive = args.recursive

	if inDirs: log.debug("Input Directory List: {}".format(inDirs))
	else: log.debug("Input file: {}".format(inFile))

	if inPic: log.debug("Input picture: {}".format(inPic))
	log.debug("Keep picture: {}".format(keepPic))
	log.debug("Recursive: {}".format(recursive))
	log.debug("Dry run: {}".format(args.dryRun))
	log.debug("Forcing: {}".format(args.forced))

	# Insert image into single file
	if inFile:
		if InsertImage(inFile, inPic, args.dryRun, args.forced):
			log.info("Inserting image successful")
			if not keepPic and not args.dryRun:
				log.info("Removing picture")
				remove(inPic)
			exit(0)

		else: exit(log.error("Inserting image unsuccessful"))

	# Insert image into all files in directory
	else:
		for inDir in inDirs:
			for path, subdirs, files in walk(inDir):

				# Add the newline back to the beginning of this statement maybe?
				log.debug("Working directory: {}".format(path))

				# Do we have an image to insert?
				if args.inPic or any(f.endswith(imageExts) for f in files):

					# What image are we using?
					image = args.inPic if args.inPic else GetCover(path, args.forced)
					if image == None:
						log.error("Remove all non-cover images or explicitly choose cover image for folder: {}".format(path))
						continue

					# Does the folder have files we can insert the image into?
					toInsert = [join(path, f) for f in files if f.endswith(musicExts)]
					if len(toInsert) > 0:

						# Only delete cover image if all insertions successful
						ip = partial(InsertImage, inPic = image, dryRun = args.dryRun, forced = args.forced)
						if all(map(ip, toInsert)):
							log.info("Image successfully inserted into all files")
							if not args.dryRun:
								log.info("Removing image {}".format(image))
								remove(image)

						# Couldn't insert image into files in directory
						else:
							exit(log.error("Image not successfully inserted into all files in directory: {}".format(path)))

					# No images in folder to insert into files
					else:
						log.debug("Skipping directory with no images: {}".format(path))

				# No files in folder to insert image into
				else:
					log.debug("Skipping directory with no music files: {}".format(path))

				if not recursive: break
	exit(0)

# Thanks to https://gist.github.com/brantfaircloth/1443543 for this argparse action
class FullPaths(argparse.Action):
	"""Expand user- and relative-paths"""
	def __call__(self, parser, namespace, values, option_string = None):
		if values != None:
			# values should only be either a string or list of strings
			if type(values) == type("str"): out = abspath(expanduser(values))
			else:
				out = []
				for path in values: out.append(abspath(expanduser(path)))
			setattr(namespace, self.dest, out)

def ManipulableDir(maybeDir):
	if not isdir(maybeDir):
		raise argparse.ArgumentTypeError("The given path is not valid: {}".format(maybeDir))
	if access(maybeDir, R_OK | W_OK): return maybeDir
	else:
		raise argparse.ArgumentTypeError("The given directory is not readable by the user: {}".format(maybeDir))

def MaybeImage(maybeFile):
	if maybeFile.endswith(imageExts): return maybeFile
	else: raise argparse.ArgumentTypeError("Incorrect filetype: {}".format(maybeFile))

def MaybeMusic(maybeFile):
	if maybeFile.endswith(musicExts): return maybeFile
	else: raise argparse.ArgumentTypeError("Incorrect filetype: {}".format(maybeFile))

if __name__ == "__main__":
	imageExts = (".jpg", ".jpeg", ".png", ".gif")
	musicExts = (".mp3", ".ogg", ".flac")

	log = logging.getLogger(__name__)
	ch = logging.StreamHandler()
	ch.setFormatter(CustomLogs())
	log.addHandler(ch)

	parser = argparse.ArgumentParser(
		prog = "apic-tool",
		description = "Inserts and extracts cover images to/from music files.",
		epilog = "(C) 2015 Mischif; released under Non-Profit Open Source License version 3.0")

	parser.add_argument("-d", "--dry-run",
		action = "store_true",
		dest = "dryRun",
		help = "Simulate the actions to be performed")

	parser.add_argument("-f", "--force",
		action = "store_true",
		dest = "force",
		help = "Make the program do things it either thinks unnecessary or is unsure on")

	parser.add_argument("-v", "--verbose",
		action = "store_true",
		help = "Change the program's verbosity")

	parser.add_argument("--version",
		action = "version",
		version = "%(prog)s {}".format(__version__))

	sp = parser.add_subparsers(
		title = "Actions",
		metavar = "")

	insertParser = sp.add_parser("insert",
		help = "Insert image into a music file")
	insertParser.set_defaults(func = InsertDispatch)

	insertParser.add_argument("-r", "--recurse",
		action = "store_true",
		dest = "recursive",
		help = "Recurse over input directories")

	insertParser.add_argument("-k", "--keep",
		action = "store_true",
		dest = "keepPic",
		help = "Don't delete image after inserting it")

	inArg = insertParser.add_mutually_exclusive_group(required = True)
	inArg.add_argument("--dir",
		action = FullPaths,
		type = ManipulableDir,
		dest = "inDirs",
		metavar = "DIR",
		nargs = "+",
		help = "Director(y|ies) containing files to manipulate")

	inArg.add_argument("--file",
		action = FullPaths,
		type = MaybeMusic,
		dest = "inFile",
		help = "Input file to manipulate")


	insertParser.add_argument("--pic",
		action = FullPaths,
		type = MaybeImage,
		dest = "inPic",
		help = "Image to insert")


	extractParser = sp.add_parser("extract",
		help = "Extract image from a music file")
	extractParser.set_defaults(func = ExtractImage)

	extractParser.add_argument("-b", "--bad-ext",
		action = "store_true",
		dest = "badExt",
		help = "Use given extension, even if it doesn't match image type")

	extractParser.add_argument("inFile",
		action = FullPaths,
		type = MaybeMusic,
		help = "File to extract image from")

	extractParser.add_argument("outFile",
		action = FullPaths,
		default = "cover.jpg",
		nargs = "?",
		help = "Filename to send extracted image to")

	args = parser.parse_args()

	if args.verbose: log.setLevel(logging.DEBUG)
	else: log.setLevel(logging.INFO)

	args.func(args)
