"""Parse type information from numpy style docstrings."""

# This file is copyright Arch Systems, Inc.
# Except as otherwise provided in the relevant LICENSE file, all rights are reserved.

import inspect
import re

arg_re = re.compile(r'^(?P<arg>[a-zA-Z_][a-zA-Z_0-9]*)\s*\((?P<typespec>[^\)]+)\):')


def parse_numpy_docstring(obj):
    """Parse information from a numpy docstring into structured data.

    Returns information on arguments, return type, and exceptions raised.

    Args:
        obj (object): The object that we wish to parse the docstring from

    Returns:
        dict: A dictionary containing keys for 'args', 'returns', 'raises'
            and other information parsed from the docstring.
    """

    doc = inspect.getdoc(obj)

    parsed = {}

    lines = doc.split('\n')

    curr_section = None

    for line in lines:
        stripped = line.strip()
        canon = stripped.lower()

        # Try to parse out what section we're in
        if canon == 'args:' or canon == 'arguments' or canon == 'parameters' or canon == 'params':
            curr_section = 'args'
            continue


def parse_argument(arg):
    """Parse an argument declaration from a numpy style docstring.

    Args:
        arg (string): The argument declaration that we wish to parse

    Returns:
        dict: A dictionary with keys for 'type', 'name', 'description'.
    """

    match = arg_re.match(arg)

    if match is None:
        raise ValueError("Could not parse argument")

    return {'name': match.group('arg'), 'typespec': match.group('typespec')}
