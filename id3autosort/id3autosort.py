#!/usr/bin/env python

import argparse
from shutil import move
from hsaudiotag import auto
from os import access, makedirs, walk, R_OK, W_OK
from os.path import abspath, expanduser, isdir, join

from id3autosort import __version__


info = {}

def GetEndDir(track, structs, outDir):
    info["Artist"] = track.artist
    info["Album"] = track.album
    info["Year"] = track.year
    info ["Genre"] = track.genre

    for struct in structs: outDir = join(outDir, info[struct])
    return outDir

def Sort(inDirs, outDir, structs, formats, recurse):
    for inDir in inDirs:
        for path, subdirs, files in walk(inDir):
            for maybeMusic in files:
                if maybeMusic.endswith(formats):
                    music = auto.File(join(path, maybeMusic))
                    if music.valid != True: continue

                    endDir = GetEndDir(music, structs, outDir)

                    if not isdir(endDir):
                        if dryRun == True:
                            print "Creating {}".format(endDir)
                        else:
                            makedirs(endDir)

                    if dryRun == True:
                        print "Moving {} to {}".format(join(path, maybeMusic), endDir)
                    else: move(join(path, maybeMusic), endDir)

            if recurse == False: break

# Thanks to https://gist.github.com/brantfaircloth/1443543 for this argparse action
class FullPaths(argparse.Action):
    """Expand user- and relative-paths"""
    def __call__(self, parser, namespace, values, option_string=None):
        if values != None:
            paths = []
            for path in values: paths.append(abspath(expanduser(path)))
            setattr(namespace, self.dest, paths)

def validOrgStructure(maybeFormat):
    delims = {"r": "Artist", "l": "Album", "g": "Genre", "y": "Year"}
    structure = []

    for delim in maybeFormat:
        if delim not in delims: raise argparse.ArgumentTypeError("The given delimiter is not valid: {0}".format(delim))
        else: structure.append(delims[delim])

    return structure

def manipulableDir(maybeDir):
  if not isdir(maybeDir):
    raise argparse.ArgumentTypeError("The given path is not valid: {0}".format(maybeDir))
  if access(maybeDir, R_OK | W_OK):
    return maybeDir
  else:
    raise argparse.ArgumentTypeError("The given directory is not readable by the user: {0}".format(maybeDir))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog = "id3autosort",
        formatter_class = argparse.RawTextHelpFormatter,
        epilog = "Released under Non-Profit Open Source License version 3.0,\n(C) 2009, 2010, 2015 Mischif",
        description = "Organizes MP3 libraries based on each track's ID3 information.")

    parser.add_argument("-v", "--version", action = "version", version = "%(prog)s {}".format(__version__))

    parser.add_argument("inDirs",
        type = manipulableDir,
        action = FullPaths,
        nargs = "+",
        help = "Directory containing MP3s to organize")

    parser.add_argument("-n", "--dry-run",
        dest = "dryRun",
        action = "store_true",
        help = "Simulate the actions instead of actually doing them")

    parser.add_argument("-r", "--recurse",
        dest = "recursive",
        action = "store_true",
        help = "Enable recursion for input directories\n(default: false)\n\n")

    parser.add_argument("-s",
        dest = "structure",
        type = validOrgStructure,
        default = ["Artist", "Album"],
        help = "Specify structure used to organize sorted MP3s,\nevaluated from left to right\n(default: lr)\
        \n\n\tOptions\n\t=======\ng\t\tgenre\nl\t\talbum\nr\t\tartist\ny\t\tyear\n\n")

    parser.add_argument("outDir",
        type = manipulableDir,
        action = FullPaths,
        nargs = 1,
        help = "Directory to sort MP3s into")

    parser.add_argument("-f",
        dest = "formats",
        choices = ["mp3", "wma", "m4a", "m4p", "ogg", "flac", "aif", "aiff", "aifc"],
        nargs = "+",
        default = ["mp3"],
        metavar = ("mp3", "ogg"),
        help = "Music formats to sort\n(default: MP3 only)\
        \n\n\tFormats\n\t=======\nmp3, wma, m4a,\nm4p, ogg, flac,\naif, aiff, aifc")

    args = parser.parse_args()
    dryRun = args.dryRun
    Sort(args.inDirs, args.outDir[0], args.structure, tuple(args.formats), args.recursive)
