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


def test_make_single_transaction():
    with revert.transaction('transaction 1'):
        revert.put('x', 'x')
        revert.put('x/y', 'x/y')
        revert.put('y', 'y')
        revert.put('z', 'z')
        revert.put('x/y/z', 'x/y/z')
        revert.put('z/x', 'z/x')
    assert revert.get('x') == 'x'
    assert revert.get('x/y') == 'x/y'
    assert revert.get('x/y/z') == 'x/y/z'
    assert revert.get('y') == 'y'
    assert revert.get('z') == 'z'
    assert revert.get('z/x') == 'z/x'


def test_undo_one():
    revert.undo()
    assert revert.safe_get('x') is None
    assert revert.safe_get('x/y') is None
    assert revert.safe_get('y') is None
    assert revert.safe_get('z') is None
    assert revert.safe_get('x/y/z') is None
    assert revert.safe_get('z/x') is None


def test_redo_one():
    revert.redo()
    assert revert.get('x') == 'x'
    assert revert.get('x/y') == 'x/y'
    assert revert.get('x/y/z') == 'x/y/z'
    assert revert.get('y') == 'y'
    assert revert.get('z') == 'z'
    assert revert.get('z/x') == 'z/x'
