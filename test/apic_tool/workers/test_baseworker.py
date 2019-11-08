# encoding: utf-8

################################################################################
#                                  apic-tool                                   #
#       Insert cover images to and extract cover images from music files       #
#                           (C) 2015-16, 2019 Mischif                          #
#       Released under version 3.0 of the Non-Profit Open Source License       #
################################################################################

import pytest

from apic_tool.workers.baseworker import BaseWorker

def test_baseworker():
	with pytest.raises(NotImplementedError):
		BaseWorker.supported_extensions()

	with pytest.raises(NotImplementedError):
		BaseWorker.get_image_data(None, None)

	with pytest.raises(NotImplementedError):
		BaseWorker.can_insert_image(None, None, None)

	with pytest.raises(NotImplementedError):
		BaseWorker.write_to_metadata(None, None, None, None)
