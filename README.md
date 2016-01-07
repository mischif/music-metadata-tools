music-metadata-tools
====================

A collection of tools for manipulating and interacting with music metadata

id3autosort - ID3-based MP3 sorting utility
-------------------------------------------

id3autosort is a Python script that organizes MP3 libraries based on each track's ID3 information. Supports ID3v1, ID3v1.1, ID3v2.2, ID3v2.3 and ID3v2.4.

apic-tool
---------

apic-tool is a Python script that allows the user to insert and extract image data from music files. Currently supports mp3 files, with FLAC support coming soon.

# Usage

General Options
---------------

    --dry-run, -d,                 Simulate the actions to be performed
    --force, -f,                   Make the program do things it either thinks unnecessary or is unsure of
    --verbose, -v                  Change the program's verbosity

Inserting Images Into Music Files
---------------------------------

Put an image into a file:

    $ python apic-tool.py insert --file /path/to/file.mp3 --pic /path/to/image.jpg

Put an image into a directory of files:

    $ python apic-tool.py insert --dir /path/to/dir --pic /path/to/image.jpg

Put an image already in the directory into a directory of files:

    $ python apic-tool.py insert --dir /path/to/dir

Do the same as above, but to all directories inside the given one as well:

    $ python apic-tool.py insert -r --dir /path/to/dir

Advanced Usage:

    $ python apic-tool.py insert -h

    -r, --recurse                  Recurse over input directories
    -k, --keep                     Don't delete image after inserting it
    --dir DIR [DIR ...]            Director(y|ies) containing files to manipulate
    --file INFILE                  Input file to manipulate
    --pic INPIC                    Image to insert

Extracting Images From Music Files
----------------------------------

Get an image from a file:

    $ python apic-tool.py extract /path/to/file.mp3 /path/for/outfile.jpg

Advanced Usage:

    $ python apic-tool.py insert -h

    -b, --bad-ext  Use given extension, even if it doesn't match image type

# TODO

FLAC support, followed by the ridiculous Apple formats, then Ogg.
