import pytest
import iotile.core.utilities.typedargs.docparse as docparse


def test_parse_arg():
	"""Make sure we can parse name and type information from arguments."""

	info = docparse.parse_argument('arg (object): hello world this is an arugment')
	print info
	assert False