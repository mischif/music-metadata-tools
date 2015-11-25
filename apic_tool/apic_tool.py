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
 
import argparse
from sys import exit
from imghdr import what
from random import randrange
from functools import partial
from mimetypes import guess_type
from os import access, listdir, remove, walk, R_OK, W_OK
from os.path import abspath, expanduser, isdir, isfile, join

from apic_tool import __version__

def GetCover(path, dryRun, verbose, forced):
	goodFilenames = ["album", "cover", "folder"]
	images = [f for f in listdir(path) if f.endswith(imageExts)]
	if verbose:
		if len(images) == 1: print "using sole image for cover: {}".format(join(path, images[0]))
		else: print "Found images in folder: {}".format(images)
	# We should have at least one image to get here, but let's make sure
	if len(images) == 0: exit("I don't know how you managed to get here, good for you?")
	elif len(images) == 1: return join(path, images[0])
	else:
		goodImages = [join(path, f) for f in images if any(s in f for s in goodFilenames)]
		if verbose:
			if len(goodImages) == 0: print "No preferred images found; too many normal ones to choose from"
			elif len(goodImages) == 1: print "Using sole preferred image: {}".format(goodImages[0])
			else: print "Too many preferred images to choose from: {}".format(goodImages)
		# There aren't any preferred images; we'll have to choose from one of the normal ones
		if len(goodImages) == 0: chooseFrom = images
		# There's only one, which is the best option
		elif len(goodImages) == 1: return goodImages[0]
		# There's more than one preferred image; we'll have to make a choice
		else: chooseFrom = goodImages
		if not forced: return None
		else:
			if verbose: print "But we're being forced, so we'll pick one at random"
			return chooseFrom[randrange(len(chooseFrom))]
	
def ExtractImage(args, dryRun, verbose, forced):
	badExt = args.badExt
	inFile = args.inFile
	outFile = args.outFile
	if verbose:
		print "Input: {}".format(inFile)
		print "Output: {}".format(outFile)
		print "Use bad extensions: {}".format(badExt)
		print "Dry run: {}".format(dryRun)
		print "Forcing: {}".format(forced)
		print "Verbose: {}".format(verbose)

	if inFile.endswith(".mp3"):
		music = MP3(inFile)
		# Did the file load right?
		if music.info.sketchy:
			exit("Don't know why file didn't load clean; exiting")
		else:
			if not music.tags: exit("File has no ID3 tags; exiting")
			if verbose: print music.tags.pprint()
			# Does the file have an image to extract?
			if len(music.tags.getall("APIC")) == 0:
				exit("File has no image to extract; exiting")
			imageData = music.tags.getall("APIC")[0].data
			ext = what(outFile, imageData)
			# What if the user uses the wrong extension for the image data?
			if verbose:
				if outFile[-3:] != ext:
					print "Given extension is {}".format(outFile[-3:])
					print "Determined extension is {}".format(ext)
					if badExt:
						print "Saving as .{} since we should use bad extensions".format(outFile[-3:])
					else: print "Saving as .{} instead".format(ext)
			if outFile[-3:] != ext:
				if not badExt: outFile = outFile.replace(outFile[-3:], ext)
				if verbose: print "New output file: {}".format(outFile)
			# Does the image we want to write to already exist?
			if isfile(outFile):
				if verbose:
					print "Output file {} already exists".format(outFile)
					if not forced:
						print "Not forced, so not overwriting existing file"
					else:
						print "But we're being forced, so we'll overwrite it"
				if not forced: exit(1)
			if dryRun:
				print "Extracting image data from file..."
				print "Writing image data to file {}...".format(outFile)
			else:
				with open(outFile, "wb") as f:
					f.write(imageData)
			print "All done!"
		exit(0)

def InsertImage(inFile, inPic, dryRun, verbose, forced):
	print "File: {}\nImage: {}\n".format(inFile, inPic)
	if inFile.endswith(".mp3"):
		music = MP3(inFile)
		# Did the file load right?
		if music.info.sketchy:
			print "File didn't load clean; skipping\n"
			return False
		else:
			# Does the file have any ID3 tags at all?
			if not music.tags:
				if verbose: print "File has no pre-existing ID3 tags, adding empty one"
				if not dryRun: music.add_tags()
			else:
				if verbose: print "Existing image tags: {}".format(music.tags.getall("APIC"))
				# Is there a pre-existing image tag?
				if len(music.tags.getall("APIC")) > 0:
					# If so, leave if we aren't being forced
					print "File already has embedded image"
					if not forced: print "Not being forced, so skipping.\n"
					else: print "But we're being forced, so we'll overwrite it"
					if not forced: return True
					# If we are being forced, remove pre-existing image tag
					else:
						if dryRun or verbose: print "Removing pre-existing APIC tag"
						if not dryRun: music.tags.delall("APIC")
			# Create the picture tag and insert it
			mimetype = guess_type(inPic)[0]
			if verbose: print "Guessed mimetype for image: {}".format(mimetype)
			with open(inPic, "rb") as f:
				pic = APIC(
					encoding = 3,		# Sets UTF-8
					type = 3,				# Signifies cover image
					mime = mimetype,
					data = f.read())
				if dryRun: print "Adding APIC tag to file"
				else: music.tags.add(pic)
				# Convert tags to ID3 v2.3 if necessary
				if music.tags:
					if music.tags.version[0] < 2 or music.tags.version[1] < 3:
						if verbose: print "Tags are version {}.{}; converting to ID3v2.3".format(
							music.tags.version[0], music.tags.version[1])
						if dryRun: print "Converting tags to ID3v2.3"
						else: music.tags.update_to_v23()
				# Save updated tags
				if dryRun or verbose: print "Saving updated tags\n"
				if dryRun: return True
				else:
					try:
						music.tags.save(v2_version = music.tags.version[1])
					except error:
						print "Error saving updated tags for file {}: {}\n".format(path, error)
						return False
					return True

def InsertDispatch(args, dryRun, verbose, forced):
	# Is the user trying to recurse on a single file?
	if args.inDirs == None and args.recursive:
		exit("Cannot recurse on a single file; exiting")

	# Did the user forget to select the image to insert into the file?
	if args.inDirs == None and args.inPic == None:
		exit("Cannot select single file without selecting image; exiting")

	# Is the user trying to recurse on a dir with a single image?
	if args.inFile == None and args.inPic != None and args.recursive and not forced:
		exit("You'll have to use force to recursively add an image to a directory; exiting")

	# Is the user trying to add a single image to files in multiple directories?
	if args.inFile == None and args.inPic != None and len(args.inDirs) > 1 and not forced:
		exit("You'll have to use force to add an image to multiple directories; exiting")

	inFile = args.inFile
	inDirs = args.inDirs
	inPic = args.inPic
	keepPic = args.keepPic
	recursive = args.recursive

	if verbose:
		if inDirs: print "Input Directory List: {}".format(inDirs)
		else: print "Input file: {}".format(inFile)
		if inPic: print "Input picture: {}".format(inPic)
		print "Keep picture: {}".format(keepPic)
		print "Recursive: {}".format(recursive)
		print "Dry run: {}".format(dryRun)
		print "Forcing: {}".format(forced)
		print "Verbose: {}".format(verbose)

	# Insert image into single file
	if inFile:
		if InsertImage(inFile, inPic, dryRun, verbose, forced):
			if verbose: print "Inserting image successful"
			if not keepPic:
				if verbose or dryRun: print "Removing picture"
				if not dryRun: remove(inPic)
			exit(0)
		else:
			if verbose: print "Inserting image unsuccessful"
			exit(1)
	# Insert image into all files in directory
	else:
		for inDir in inDirs:
			for path, subdirs, files in walk(inDir):
				if verbose: print "\nWorking directory: {}".format(path)
				# Does the folder have an image to insert?
				if any(f.endswith(imageExts) for f in files):
					image = GetCover(path, dryRun, verbose, forced)
					if image == None:
						print "Explicitly choose image for folder or remove all non-cover images: {}".format(path)
						continue
					# Does the folder have files we can insert the image into?
					toInsert = [join(path, f) for f in files if f.endswith(musicExts)]
					if len(toInsert) > 0:
						# Only delete cover image if all insertions successful
						ip = partial(InsertImage, inPic = image, dryRun = dryRun,
							verbose = verbose, forced = forced)
						if all(map(ip, toInsert)):
							print "Image successfully inserted into all files\n"
							if dryRun or verbose: print "Removing image {}\n".format(image)
							if not dryRun: remove(image)
						else:
							exit("Image not successfully inserted into all files")
					else:
						if verbose: print "Directory has no files to insert image into; skipping"
				else:
					if verbose: print "Directory has no images to insert into files; skipping"
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

	parser = argparse.ArgumentParser(
		prog = "apic-tool",
		epilog = "Released under Non-Profit Open Source License version 3.0,\n(C) 2015 Mischif",
		description = "Inserts and extracts images to/from music files.")

	parser.add_argument("-d", "--dry-run",
		dest = "dryRun",
		action = "store_true",
		help = "Simulate the actions to be performed")

	parser.add_argument("-f", "--force",
		dest = "force",
		action = "store_true",
		help = "Make the program do things it either thinks unnecessary or is unsure on")

	parser.add_argument("-v", "--verbose",
		action = "store_true",
		help="Make the program tell you more about what it's doing")

	parser.add_argument("--version",
		action = "version",
		version = "%(prog)s {}".format(__version__))

	sp = parser.add_subparsers(title = "Actions", metavar = "")
	insertParser = sp.add_parser("insert", help = "Insert image into a music file")
	insertParser.set_defaults(func = InsertDispatch)
	extractParser = sp.add_parser("extract", help = "Extract image from a music file",
		formatter_class = argparse.ArgumentDefaultsHelpFormatter)
	extractParser.set_defaults(func = ExtractImage)

	# Arguments when using --insert
	insertParser.add_argument("-r", "--recurse",
		dest = "recursive",
		action = "store_true",
		help = "Recurse over input directories")

	insertParser.add_argument("-k", "--keep",
		dest = "keepPic",
		action = "store_true",
		help = "Don't delete image after embedding it")

	inArg = insertParser.add_mutually_exclusive_group(required = True)
	inArg.add_argument("--dir",
		type = ManipulableDir,
		action = FullPaths,
		dest = "inDirs",
		metavar = "DIR",
		nargs = "+",
		help = "Directory/Directories containing files to manipulate")

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

	# Arguments when using --extract
	extractParser.add_argument("-b", "--bad-ext",
		dest = "badExt",
		action = "store_true",
		help = "Use given extension, even if it doesn't match image type")

	extractParser.add_argument("inFile",
		action = FullPaths,
		type = MaybeMusic,
		help = "File to extract image from")

	extractParser.add_argument("outFile",
		action = FullPaths,
		nargs = "?",
		default = "cover.jpg",
		help = "Filename to send extracted image to")

	args = parser.parse_args()
	args.func(args, args.dryRun, args.verbose, args.force)
