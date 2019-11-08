# encoding: utf-8

################################################################################
#                                  apic-tool                                   #
#       Insert cover images to and extract cover images from music files       #
#                           (C) 2015-16, 2019 Mischif                          #
#       Released under version 3.0 of the Non-Profit Open Source License       #
################################################################################

from os.path import join

import pytest

from apic_tool.workers import get_format_worker
from apic_tool.workers.mp3worker import MP3Worker


@pytest.mark.parametrize("filename, worker_type", [("test.mp3", MP3Worker), ("test.xyz", None)],
						 ids=["valid-type", "invalid-type"])
def test_get_format_worker(tmpdir, filename, worker_type):
	full_path = join(str(tmpdir), filename)
	assert get_format_worker(full_path) == worker_type
