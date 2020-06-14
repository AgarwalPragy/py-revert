import random

import revert.config
from revert.trie import Trie, split


def _trie():
    t = Trie()
    t.put(['x', 'y', 'w', 'a', 'b'], 'value1')
    t.put(['x', 'y'], 'value2')
    t.put(['x'], 'value3')
    t.put(['y'], 'value4')
    t.put(['z', 'a', 'b'], 'value5')
    return t


def _join_keys(keys):
    return ['/'.join(k) for k in keys]


def _join_items(items):
    return [('/'.join(k), value) for k, value in items]


def test_key_separator():
    assert revert.config.key_separator == '/', 'these tests assume that the key-separator is `/`'


def test_split_no_separator():
    assert split('x') == ['x']


def test_split_one_separator():
    assert split('x/y') == ['x', 'y']


def test_split_multiple_separators():
    assert split('x/y/z') == ['x', 'y', 'z']


def test_split_trailing_separator():
    assert split('x/y/z/') == ['x', 'y', 'z']


def test_split_leading_separator():
    assert split('/x/y/z/') == ['x', 'y', 'z']


def test_split_double_separators():
    assert split('x//y') == ['x', 'y']


def test_split_all():
    assert split('///x/////y////////z/a////////////c////////') == ['x', 'y', 'z', 'a', 'c']


def test_trie_dict_truthiness_empty():
    t = Trie()
    assert not bool(t)


def test_trie_dict_truthiness_non_empty():
    t = Trie()
    t.put(['x'], 'value')
    assert bool(t)


def test_trie_dict_key_insert():
    t = Trie()
    assert t.put(['x'], 'value_x') is None
    assert t[['x']] == 'value_x'


def test_trie_dict_get_missing_key():
    t = Trie()
    assert t[['x']] is None


def test_trie_dict_get_missing_nested_key():
    t = Trie()
    assert t.put(['x'], 'value') is None
    assert t[['x', 'y']] is None


def test_trie_dict_del_key():
    t = Trie()
    t.put(['x'], 'value')
    assert t.discard(['x']) == 'value'
    assert t.flatten() == {}


def test_trie_dict_del_missing_key():
    t = Trie()
    assert t.discard(['x']) is None


def test_trie_dict_del_nested_key():
    t = Trie()
    t.put(['x'], 'value1')
    t.put(['x', 'y'], 'value2')
    assert t.discard(['x', 'y']) == 'value2'
    assert t.flatten() == {'x': 'value1'}


def test_trie_dict_del_missing_nested_key():
    t = Trie()
    t.put(['x'], 'value')
    assert t.discard(['x', 'y']) is None


def test_trie_dict_nested_key_insert():
    t = Trie()
    t.put(['x', 'y'], 'value_x')
    assert t[['x', 'y']] == 'value_x'


def test_trie_dict_key_insert_len():
    t = Trie()
    t.put(['x'], 'value_x')
    t.put(['y'], 'value_y')
    assert len(t) == 2


def test_trie_dict_nested_key_insert_len():
    t = Trie()
    t.put(['x'], 'value_x')
    t.put(['x', 'y'], 'value_y')
    assert len(t) == 2


def test_trie_dict_keys_empty():
    t = Trie()
    assert set(t.keys([])) == set()


def test_trie_dict_keys():
    assert _join_keys(_trie().keys([])) == ['x', 'x/y', 'x/y/w/a/b', 'y', 'z/a/b']


def test_trie_dict_keys_with_prefix():
    assert _join_keys(_trie().keys(['x'])) == ['x', 'x/y', 'x/y/w/a/b']


def test_trie_dict_items_empty():
    assert _join_items(Trie().items([])) == []


def test_trie_dict_items():
    assert _join_items(_trie().items([])) == [('x', 'value3'), ('x/y', 'value2'), ('x/y/w/a/b', 'value1'),
                                              ('y', 'value4'), ('z/a/b', 'value5')]


def test_trie_dict_items_with_prefix():
    assert _join_items(_trie().items(['x'])) == [('x', 'value3'), ('x/y', 'value2'), ('x/y/w/a/b', 'value1')]


def test_to_json_empty():
    t = Trie()
    assert t.to_json() == {}


def test_to_json_single():
    t = Trie()
    t.put(['x'], 'value')
    assert t.to_json() == {'x': 'value'}


def test_to_json_multiple():
    t = Trie()
    t.put(['x'], 'value1')
    t.put(['x', 'y'], 'value2')
    t.put(['z'], 'value3')
    assert t.to_json() == {'x': ('value1', {'y': 'value2'}), 'z': 'value3'}


def test_from_json_empty():
    t = Trie.from_json({})
    assert t.flatten() == {}


def test_from_json_single():
    t = Trie.from_json({'x': 'value'})
    assert t.flatten() == {'x': 'value'}


def test_from_json_multiple():
    t = Trie.from_json({'x': ('value1', {'y': 'value2'}), 'z': 'value3'})
    assert t.flatten() == {'x': 'value1', 'x/y': 'value2', 'z': 'value3'}


def test_trie_dict_copy():
    t = Trie()
    t.put(['x'], 'value')
    t.put(['x', 'y'], 'value')
    clone = t.clone()
    assert t.flatten() == clone.flatten()
    assert t.to_json() == clone.to_json()
    assert _join_keys(t.keys([])) == _join_keys(clone.keys([]))
    assert _join_items(t.items([])) == _join_items(clone.items([]))


def test_trie_dict_hypothesis():
    random.seed(0)
    trials = 10000
    size = 8
    key_len = 8
    for _ in range(trials):
        t = Trie()
        normal_dict = {}
        # insert
        num_keys = random.randint(0, size)
        for _ in range(num_keys):
            key = ''.join(random.choices('a0!///', k=random.randint(1, key_len)))
            print(key)
            value = str(random.randint(1, key_len))
            clean_key = '/'.join(split(key))
            t.put(split(key), value)
            normal_dict[clean_key] = value
            assert split(key) in t
            assert t.flatten() == normal_dict
            assert set(_join_items(t.items([]))) == set(normal_dict.items())
            assert set(_join_keys(t.keys([]))) == set(normal_dict.keys())
            assert len(t) == len(normal_dict)
        # clone
        clone = t.clone()
        assert t.flatten() == clone.flatten()
        assert t.to_json() == clone.to_json()
        assert _join_keys(t.keys([])) == _join_keys(clone.keys([]))
        assert _join_items(t.items([])) == _join_items(clone.items([]))
        # delete
        for key in list(normal_dict.keys()):
            del normal_dict[key]
            t.discard(split(key))
            assert split(key) not in t
            assert t.flatten() == normal_dict
            assert set(_join_items(t.items([]))) == set(normal_dict.items())
            assert set(_join_keys(t.keys([]))) == set(normal_dict.keys())
            assert len(t) == len(normal_dict)
