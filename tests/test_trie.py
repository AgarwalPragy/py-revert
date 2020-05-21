import random

import pytest

import revert.config
from revert.trie import TrieDict, split_first


def test_key_separator():
    assert revert.config.key_separator == '/', 'these tests assume that the key-separator is `/`'


def test_split_first_no_separator():
    assert split_first('x') == ('x', '')


def test_split_first_one_separator():
    assert split_first('x/y') == ('x', 'y')


def test_split_first_multiple_separators():
    assert split_first('x/y/z') == ('x', 'y/z')


def test_split_first_trailing_separator():
    assert split_first('x/y/z/') == ('x', 'y/z/')


def test_split_first_leading_separator():
    assert split_first('/x/y/z/') == ('x', 'y/z/')


def test_split_first_double_separators():
    assert split_first('x//y') == ('x', '/y')


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


def test_trie_dict_del_key():
    t = TrieDict()
    t['x'] = 'value'
    del t['x']
    assert t.flatten() == {}


def test_trie_dict_del_missing_key():
    t = TrieDict()
    with pytest.raises(KeyError):
        del t['x']


def test_trie_dict_del_nested_key():
    t = TrieDict()
    t['x'] = 'value1'
    t['x/y'] = 'value2'
    del t['x/y']
    assert t.flatten() == {'x': 'value1'}


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


def test_trie_dict_double_separators():
    t = TrieDict()
    t['x//y///w/a////b'] = 'value'
    assert t['x/y/w/a///b'] == 'value'


def test_trie_dict_keys_empty():
    t = TrieDict()
    assert set(t.keys()) == set()


def test_trie_dict_keys():
    t = TrieDict()
    t['x//y///w/a////b'] = 'value1'
    t['x'] = 'value2'
    t['y'] = 'value3'
    t['z/a/b'] = 'value4'
    assert set(t.keys()) == {'x/y/w/a/b', 'x', 'y', 'z/a/b'}


def test_trie_dict_keys_with_prefix():
    t = TrieDict()
    t['x//y///w/a////b'] = 'value1'
    t['x/y'] = 'value2'
    t['x'] = 'value3'
    t['y'] = 'value4'
    t['z/a/b'] = 'value5'
    assert set(t.keys('x')) == {'x/y/w/a/b', 'x', 'x/y'}


def test_trie_dict_items_empty():
    t = TrieDict()
    assert set(t.items()) == set()


def test_trie_dict_items():
    t = TrieDict()
    t['x//y///w/a////b'] = 'value1'
    t['x'] = 'value2'
    t['y'] = 'value3'
    t['z/a/b'] = 'value4'
    assert set(t.items()) == {('x/y/w/a/b', 'value1'), ('x', 'value2'), ('y', 'value3'), ('z/a/b', 'value4')}


def test_trie_dict_items_with_prefix():
    t = TrieDict()
    t['x//y///w/a////b'] = 'value1'
    t['x/y'] = 'value2'
    t['x'] = 'value3'
    t['y'] = 'value4'
    t['z/a/b'] = 'value5'
    assert set(t.items('x')) == {('x/y/w/a/b', 'value1'), ('x', 'value3'), ('x/y', 'value2')}


def test_to_json_empty():
    t = TrieDict()
    assert t.to_json() == {}


def test_to_json_single():
    t = TrieDict()
    t['x'] = 'value'
    assert t.to_json() == {'x': 'value'}


def test_to_json_multiple():
    t = TrieDict()
    t['x'] = 'value1'
    t['x/y'] = 'value2'
    t['z'] = 'value3'
    assert t.to_json() == {'x': ('value1', {'y': 'value2'}), 'z': 'value3'}


def test_from_json_empty():
    t = TrieDict.from_json({})
    assert t.flatten() == {}


def test_from_json_single():
    t = TrieDict.from_json({'x': 'value'})
    assert t.flatten() == {'x': 'value'}


def test_from_json_multiple():
    t = TrieDict.from_json({'x': ('value1', {'y': 'value2'}), 'z': 'value3'})
    assert t.flatten() == {'x': 'value1', 'x/y': 'value2', 'z': 'value3'}


def test_trie_dict_copy():
    t = TrieDict()
    t['x'] = 'value'
    t['x/y'] = 'value'
    clone = t.clone()
    assert t.flatten() == clone.flatten()
    assert t.to_json() == clone.to_json()
    assert set(t.keys()) == set(clone.keys())
    assert set(t.items()) == set(clone.items())


def test_trie_dict_hypothesis():
    random.seed(0)
    trials = 10000
    size = 8
    key_len = 8
    for _ in range(trials):
        t = TrieDict()
        normal_dict = {}
        # insert
        num_keys = random.randint(0, size)
        for _ in range(num_keys):
            key = ''.join(random.choices('a0!///', k=random.randint(1, key_len)))
            print(key)
            value = str(random.randint(1, key_len))
            clean_key = key
            while clean_key and '//' in clean_key:
                clean_key = clean_key.replace('//', '/')
            if clean_key.startswith('/'):
                clean_key = clean_key[1:]
            if clean_key.endswith('/'):
                clean_key = clean_key[:-1]
            if not clean_key:
                continue
            t[key] = value
            normal_dict[clean_key] = value
            assert key in t
            assert t.flatten() == normal_dict
            assert set(t.items()) == set(normal_dict.items())
            assert set(t.keys()) == set(normal_dict.keys())
            assert len(t) == len(normal_dict)
        # clone
        clone = t.clone()
        assert t.flatten() == clone.flatten()
        assert t.to_json() == clone.to_json()
        assert set(t.keys()) == set(clone.keys())
        assert set(t.items()) == set(clone.items())
        # delete
        for key in list(normal_dict.keys()):
            del normal_dict[key]
            del t[key]
            assert key not in t
            assert t.flatten() == normal_dict
            assert set(t.items()) == set(normal_dict.items())
            assert set(t.keys()) == set(normal_dict.keys())
            assert len(t) == len(normal_dict)
