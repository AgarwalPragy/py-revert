#!/usr/bin/env python

"""Tests for `revert` package."""

import os
import shutil

import revert


def test_connect():
    directory = os.path.join(os.curdir, '../test_tmp_dir')
    shutil.rmtree(directory, ignore_errors=True)
    os.makedirs(directory, exist_ok=True)
    revert.connect(directory)


def test_make_transactions():
    for i in range(5):
        with revert.transaction('transaction 1'):
            revert.put('x', str(i))
            revert.put('x/y', str(i))
            revert.put('y', str(i))
            revert.put('z', str(i))
            revert.put('x/y/z', str(i))
            revert.put('z/x', str(i))

def _assert_values(i):
    expected = str(i) if i >= 0 else None
    assert revert.safe_get('x') == expected
    assert revert.safe_get('x/y') == expected
    assert revert.safe_get('y') == expected
    assert revert.safe_get('z') == expected
    assert revert.safe_get('x/y/z') == expected
    assert revert.safe_get('z/x') == expected


def test_undo_redo():
    for i in reversed(range(5)):
        revert.undo()
        _assert_values(i - 1)
    for i in range(5):
        revert.redo()
        _assert_values(i)
