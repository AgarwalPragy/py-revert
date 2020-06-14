#!/usr/bin/env python

"""Tests for `revert` package."""

import os

import pytest

import revert


@pytest.fixture
def connect():
    directory = os.path.join(os.curdir, 'key_value_test')
    os.makedirs(directory, exist_ok=True)
    revert.connect(directory)

