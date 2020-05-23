import random

import revert.config
from revert.trie import Trie, safe_split


def test_key_separator():
    assert revert.config.KEY_SEPARATOR == '/', 'these tests assume that the key-separator is `/`'


def test_safe_split_no_separator():
    assert safe_split('x') == ['x']


def test_safe_split_one_separator():
    assert safe_split('x/y') == ['x', 'y']


def test_safe_split_multiple_separators():
    assert safe_split('x/y/z') == ['x', 'y', 'z']


def test_safe_split_trailing_separator():
    assert safe_split('x/y/z/') == ['x', 'y', 'z']


def test_safe_split_leading_separator():
    assert safe_split('/x/y/z/') == ['x', 'y', 'z']


def test_safe_split_double_separators():
    assert safe_split('x//y') == ['x', 'y']


def test_safe_split_all():
    assert safe_split('///x//y/////z//////////////') == ['x', 'y', 'z']


def test_trie_truthiness_empty():
    t = Trie()
    assert not bool(t)


def test_trie_truthiness_non_empty():
    t = Trie()
    t.set(['x'], 'value')
    assert bool(t)


def test_trie_get_missing_key():
    t = Trie()
    assert t[['x']] is None


def test_trie_get_missing_nested_key():
    t = Trie()
    t.set(['x'], 'value')
    assert t[['x', 'y']] is None


def test_trie_del_key():
    t = Trie()
    t.set(['x'], 'value')
    assert t.discard(['x'])
    assert t[['x']] is None


def test_trie_del_missing_key():
    t = Trie()
    assert not t.discard(['x'])


def test_trie_del_nested_key():
    t = Trie()
    t.set(['x'], 'value1')
    t.set(['x', 'y'], 'value2')
    assert t.discard(['x', 'y'])
    assert t.flatten() == {'x': 'value1'}


def test_trie_del_missing_nested_key():
    t = Trie()
    t.set(['x'], 'value')
    assert not t.discard(['x', 'y'])


def test_trie_key_insert():
    t = Trie()
    t.set(['x'], 'value_x')
    assert t[['x']] == 'value_x'


def test_trie_key_overwrite():
    t = Trie()
    t.set(['x'], 'value_x')
    t.set(['x'], 'value_y')
    assert t[['x']] == 'value_y'


def test_trie_nested_key_insert():
    t = Trie()
    t.set(['x', 'y'], 'value_1')
    assert t[['x', 'y']] == 'value_1'


def test_trie_nested_key_overwrite():
    t = Trie()
    t.set(['x', 'y'], 'value_1')
    t.set(['x', 'y'], 'value_2')
    assert t[['x', 'y']] == 'value_2'


def test_trie_len_empty():
    t = Trie()
    assert len(t) == 0


def test_trie_len():
    t = Trie()
    t.set(['x'], 'value_x')
    t.set(['y'], 'value_y')
    assert len(t) == 2


def test_trie_nested_len():
    t = Trie()
    t.set(['x'], 'value_x')
    t.set(['x', 'y'], 'value_y')
    assert len(t) == 2


def test_trie_match_count_empty():
    t = Trie()
    assert t.match_count([]) == 0


def test_trie_match_count_empty_2():
    t = Trie()
    assert t.match_count(['x', 'y']) == 0


def test_trie_match_count():
    t = Trie()
    t.set(['x'], 'value_x')
    t.set(['y'], 'value_y')
    assert t.match_count(['x']) == 1
    assert t.match_count(['y']) == 1
    assert t.match_count([]) == 2


def test_trie_nested_match_count():
    t = Trie()
    t.set(['x'], 'value_x')
    t.set(['x', 'y'], 'value_y')
    assert t.match_count(['x', 'y']) == 1
    assert t.match_count(['x']) == 2
    assert t.match_count([]) == 2


def test_trie_keys_empty():
    t = Trie()
    assert sorted(t.keys([])) == []


def test_trie_keys():
    t = Trie()
    t.set(['x', 'y', 'w', 'a', 'b'], 'value1')
    t.set(['x'], 'value2')
    t.set(['y'], 'value3')
    t.set(['z', 'a', 'b'], 'value4')
    assert sorted(t.keys([])) == sorted(['x/y/w/a/b', 'x', 'y', 'z/a/b'])


def test_trie_keys_with_prefix():
    t = Trie()
    t.set(['x', 'y', 'w', 'a', 'b'], 'value1')
    t.set(['x'], 'value2')
    t.set(['y'], 'value3')
    t.set(['z', 'a', 'b'], 'value4')
    t.set(['x', 'y'], 'value5')
    assert sorted(t.keys(['x'])) == sorted(['x/y/w/a/b', 'x', 'x/y'])


def test_trie_keys_with_bad_prefix():
    t = Trie()
    t.set(['x', 'y', 'w', 'a', 'b'], 'value1')
    t.set(['x'], 'value2')
    t.set(['y'], 'value3')
    t.set(['z', 'a', 'b'], 'value4')
    t.set(['x', 'y'], 'value5')
    assert sorted(t.keys(['c'])) == []


def test_trie_items_empty():
    t = Trie()
    assert sorted(t.items([])) == []


def test_trie_items():
    t = Trie()
    t.set(['x', 'y', 'w', 'a', 'b'], 'value1')
    t.set(['x'], 'value2')
    t.set(['y'], 'value3')
    t.set(['z', 'a', 'b'], 'value4')
    assert sorted(t.items([])) == sorted([('x/y/w/a/b', 'value1'), ('x', 'value2'), ('y', 'value3'), ('z/a/b', 'value4')])


def test_trie_items_with_prefix():
    t = Trie()
    t.set(['x', 'y', 'w', 'a', 'b'], 'value1')
    t.set(['x'], 'value2')
    t.set(['y'], 'value3')
    t.set(['z', 'a', 'b'], 'value4')
    t.set(['x', 'y'], 'value5')
    assert sorted(t.items(['x'])) == sorted([('x/y/w/a/b', 'value1'), ('x', 'value2'), ('x/y', 'value5')])


def test_trie_items_with_bad_prefix():
    t = Trie()
    t.set(['x', 'y', 'w', 'a', 'b'], 'value1')
    t.set(['x'], 'value2')
    t.set(['y'], 'value3')
    t.set(['z', 'a', 'b'], 'value4')
    t.set(['x', 'y'], 'value5')
    assert sorted(t.items(['c'])) == []


def test_trie_hypothesis():
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
            key = safe_split(''.join(random.choices('a0!///', k=random.randint(1, key_len))))
            value = str(random.randint(1, key_len))
            if not key:
                continue
            t.set(key, value)
            normal_dict['/'.join(key)] = value
            assert key in t
            assert t.flatten() == normal_dict
            assert sorted(t.items([])) == sorted(normal_dict.items())
            assert sorted(t.keys([])) == sorted(normal_dict.keys())
            assert len(t) == len(normal_dict)
        assert sorted(Trie.from_json(t.to_json()).items([])) == sorted(t.items([]))
        # delete
        for key in list(normal_dict.keys()):
            del normal_dict[key]
            assert t.discard(safe_split(key))
            assert safe_split(key) not in t
            assert t.flatten() == normal_dict
            assert sorted(t.items([])) == sorted(normal_dict.items())
            assert sorted(t.keys([])) == sorted(normal_dict.keys())
            assert len(t) == len(normal_dict)
