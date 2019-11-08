music-metadata-tools
====================

A collection of tools for manipulating and interacting with music metadata.


id3autosort - metadata-based music organization utility
-------------------------------------------------------

id3autosort organizes music libraries based on each track's metadata. Supports AAC, AIFF, FLAC, MP3, OGG and WMA formats.

# Usage

	$ id3autosort [-u] [-n] [-v] [-s <desired structure>] /path/to/music [/path/to/music ...] /path/music/should/go


## General Options

	--windows-unsafe, -u	Use all characters in metadata for new directories,
							including ones Windows filesystems normally choke on
	--dry-run, -n			Simulate the actions instead of actually doing them
	--verbose, -v			Increase logging verbosity


## Structure Option

The `-s` switch allows the user to define the way they wish their music to be structured, which will be obeyed so long as the user's music has the necessary tags.

Supported structure metatags: d (date), g (genre), l (album), r (artist)

For example, if a user specifies the structure "r/l (d)" with a destination directory of /tmp/music, results would be similar to these:

/tmp/music/Nirvana/Nevermind (1991)/Smells Like Teen Spirit.mp3
/tmp/music/The Eagles/Hotel California (1976)/Hotel California.flac
/tmp/music/Tupac/All Eyez On Me (1996)/California Love.ogg

Whereas if a user specifies the structure "g/d/r" with the same destination directory, results would be similar to these:

/tmp/music/House/2001/Daft Punk/Crescendolls.wma
/tmp/music/Pop/2014/Taylor Swift/Shake It Off.aiff
/tmp/music/Dubstep/2006/Skream/Midnight Request Line.m4a

Characters that are not already reserved for expansion are passed through to the generated structure, but no guarantee is made that other letters will not be used to expand other tags in the future.


apic-tool - music file image manipulation utility
-------------------------------------------------

apic-tool allows the user to insert and extract image data from music files. Currently supports mp3 files.

# Usage

General Options
---------------

	--dry-run, -d	Simulate the actions instead of actually doing them
	--verbose, -v	Change the program's verbosity
	--force			Whether or not the tool should allow things to happen that may have complications


Extracting Images From Music Files
----------------------------------

### Extract image from file to specified location:

	$ apic-tool extract /path/to/file.mp3 /path/for/outfile.jpg

Note that if not forced, the actual extension used may change depending on the image type in the file.


### Extract image from file with no specified location:

	$ apic-tool extract /path/to/file.mp3

Image will be saved to /path/to/file.xyz, with `xyz` changing depending on the image type in the file.


Inserting Images Into Music Files
---------------------------------

#### Insertion Options

	--pic, -p /path/to/image.jpg								Image to insert into music files
																(currently support GIF, JPEG, PNG)
	--dir, -d /path/to/music [/path/to/other/music ...],		Directory or directories containing files to insert image into
																NOTE: does not recurse
	--file, -f /path/to/file.mp3 [/path/to/other/file.mp3 ...]	Individual files to insert image into
	--keep, -k													Don't delete image after inserting it


### Put an image into a file:

	$ apic-tool insert --file /path/to/file.mp3 --pic /path/to/image.jpg

### Put an image into a directory of files:

	$ apic-tool insert --d /path/to/dir --p /path/to/image.jpg
