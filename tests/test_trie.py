import random
import string

import pytest

from revert.trie import TrieDict, split_first


def test_split_first_no_separator():
    assert split_first('x') == ('x', '')


def test_split_first_one_separator():
    assert split_first('x/y') == ('x', 'y')


def test_split_first_multiple_separators():
    assert split_first('x/y/z') == ('x', 'y/z')


def test_split_first_trailing_separator():
    assert split_first('x/y/z/') == ('x', 'y/z/')


def test_trie_dict_truthiness_empty():
    t = TrieDict()
    assert not bool(t)


def test_trie_dict_truthiness_non_empty():
    t = TrieDict()
    t['x'] = 'value'
    assert bool(t)


def test_trie_dict_key_insert():
    t = TrieDict()
    t['x'] = 'value_x'
    assert t['x'] == 'value_x'


def test_trie_dict_get_missing_key():
    t = TrieDict()
    with pytest.raises(KeyError):
        value = t['x']


def test_trie_dict_get_missing_nested_key():
    t = TrieDict()
    t['x'] = 'value'
    with pytest.raises(KeyError):
        value = t['x/y']


def test_trie_dict_del_missing_key():
    t = TrieDict()
    with pytest.raises(KeyError):
        del t['x']


def test_trie_dict_del_missing_nested_key():
    t = TrieDict()
    t['x'] = 'value'
    with pytest.raises(KeyError):
        del t['x/y']


def test_trie_dict_nested_key_insert():
    t = TrieDict()
    t['x/y'] = 'value_x'
    assert t['x/y'] == 'value_x'


def test_trie_dict_key_insert_len():
    t = TrieDict()
    t['x'] = 'value_x'
    t['y'] = 'value_y'
    assert len(t) == 2


def test_trie_dict_nested_key_insert_len():
    t = TrieDict()
    t['x'] = 'value_x'
    t['x/y'] = 'value_y'
    assert len(t) == 2


def test_split_first_double_separators():
    assert split_first('x//y') == ('x', 'y')


def test_trie_dict_double_separators():
    t = TrieDict()
    t['x//y///w/a////b'] = 'value'
    assert t['x/y/w/a///b'] == 'value'


def test_trie_dict_keys():
    t = TrieDict()
    t['x//y///w/a////b'] = 'value'
    t['x'] = 'value'
    t['y'] = 'value'
    t['z/a/b'] = 'value4'
    assert set(t.keys()) == {'x/y/w/a/b', 'x', 'y', 'z/a/b'}


def test_trie_dict_items():
    t = TrieDict()
    t['x//y///w/a////b'] = 'value1'
    t['x'] = 'value2'
    t['y'] = 'value3'
    t['z/a/b'] = 'value4'
    assert set(t.items()) == {('x/y/w/a/b', 'value1'), ('x', 'value2'), ('y', 'value3'), ('z/a/b', 'value4')}


def test_to_json():
    t1 = TrieDict()
    t1['x'] = 'value1'
    t1['x/y'] = 'value2'
    assert t1.to_json() == {'x': ('value1', {'y': 'value2'})}


def test_from_json():
    t1 = TrieDict.from_json({'x': ('value1', {'y': 'value2'})})
    assert t1['x'] == 'value1'
    assert t1['x/y'] == 'value2'


def test_trie_dict_copy():
    t1 = TrieDict()
    t1['x'] = 'value'
    t1['x/y'] = 'value'
    t2 = t1.copy()
    assert set(t1.items()) == set(t2.items())


def test_trie_dict_copy_automated():
    t1 = TrieDict()
    random.seed(0)
    trials = 10000
    key_len = 1000

    for _ in range(trials):
        key = ''.join(random.choices(string.ascii_letters + string.digits + '/', k=random.randint(1, key_len)))
        value = str(random.randint(1, key_len))
        t1[key] = value

    t2 = t1.copy()
    assert set(t1.items()) == set(t2.items())
