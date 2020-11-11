# This file is part of the Data Cleaning Library (openclean).
#
# Copyright (C) 2018-2020 New York University.
#
# openclean is released under the Revised BSD License. See file LICENSE for
# full license details.

"""Unit test to access version information."""


def test_package_version():
    """Unit test to access the package code version identifier (for completeness)."""
    from openclean_jupyter.version import __version__
    assert __version__ is not None
