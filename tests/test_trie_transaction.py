from revert.transaction import Transaction
from revert.trie import Trie
from revert.trie_transaction import discard_with_transaction, set_with_transaction


def test_trie_del_new_key_with_transaction():
    t = Trie()
    tr = Transaction()
    set_with_transaction(t, ['x'], 'value', tr)
    assert ['x'] in tr.new_keys
    assert discard_with_transaction(t, ['x'], tr)
    assert t[['x']] is None
    assert ['x'] not in tr.old_values
    assert ['x'] not in tr.new_keys


def test_trie_del_missing_new_key_with_transaction():
    t = Trie()
    tr = Transaction()
    assert not discard_with_transaction(t, ['x'], tr)
    assert t[['x']] is None
    assert ['x'] not in tr.old_values
    assert ['x'] not in tr.new_keys


def test_trie_del_nested_new_key_with_transaction():
    t = Trie()
    tr = Transaction()
    set_with_transaction(t, ['x'], 'value1', tr)
    set_with_transaction(t, ['x', 'y'], 'value2', tr)
    assert discard_with_transaction(t, ['x', 'y'], tr)
    assert t.flatten() == {'x': 'value1'}
    assert ['x'] in tr.new_keys
    assert ['x'] not in tr.old_values
    assert ['x', 'y'] not in tr.new_keys
    assert ['x', 'y'] not in tr.old_values


def test_trie_del_missing_nested_new_key_with_transaction():
    t = Trie()
    tr = Transaction()
    set_with_transaction(t, ['x'], 'value', tr)
    assert not discard_with_transaction(t, ['x', 'y'], tr)
    assert ['x'] in tr.new_keys
    assert ['x'] not in tr.old_values
    assert ['x', 'y'] not in tr.new_keys
    assert ['x', 'y'] not in tr.old_values


def test_trie_del_existing_key_with_transaction():
    t = Trie()
    tr = Transaction()
    t.set(['x'], 'value')
    assert discard_with_transaction(t, ['x'], tr)
    assert t[['x']] is None
    assert tr.old_values[['x']] == 'value'
    assert ['x'] not in tr.new_keys


def test_trie_del_missing_existing_key_with_transaction():
    t = Trie()
    tr = Transaction()
    assert not discard_with_transaction(t, ['x'], tr)
    assert t[['x']] is None
    assert ['x'] not in tr.old_values
    assert ['x'] not in tr.new_keys


def test_trie_del_nested_existing_key_with_transaction():
    t = Trie()
    tr = Transaction()
    t.set(['x'], 'value1')
    t.set(['x', 'y'], 'value2')
    assert discard_with_transaction(t, ['x', 'y'], tr)
    assert t.flatten() == {'x': 'value1'}
    assert ['x'] not in tr.new_keys
    assert ['x'] not in tr.old_values
    assert ['x', 'y'] not in tr.new_keys
    assert tr.old_values[['x', 'y']] == 'value2'


def test_trie_del_missing_nested_existing_key_with_transaction():
    t = Trie()
    tr = Transaction()
    t.set(['x'], 'value')
    assert not discard_with_transaction(t, ['x', 'y'], tr)
    assert ['x'] not in tr.new_keys
    assert ['x'] not in tr.old_values
    assert ['x', 'y'] not in tr.new_keys
    assert ['x', 'y'] not in tr.old_values


def test_trie_insert_del_new_key_with_transaction():
    t = Trie()
    tr = Transaction()
    t.set(['x'], 'value1')
    t.set(['x', 'y'], 'value2')

    set_with_transaction(t, ['z'], 'value3', tr)
    set_with_transaction(t, ['z', 'x'], 'value4', tr)
    assert t[['z']] == 'value3'
    assert t[['z', 'x']] == 'value4'
    assert ['z'] in tr.new_keys
    assert ['z'] not in tr.old_values
    assert ['z', 'x'] in tr.new_keys
    assert ['z', 'x'] not in tr.old_values
    discard_with_transaction(t, ['z'], tr)
    discard_with_transaction(t, ['z', 'x'], tr)
    assert t[['z']] is None
    assert t[['z', 'x']] is None
    assert ['z'] not in tr.new_keys
    assert ['z'] not in tr.old_values
    assert ['z', 'x'] not in tr.new_keys
    assert ['z', 'x'] not in tr.old_values


def test_trie_insert_del_insert_same_existing_key_with_transaction():
    t = Trie()
    tr = Transaction()
    t.set(['x'], 'value1')
    t.set(['x', 'y'], 'value2')
    t.set(['z'], 'value3')
    t.set(['z', 'x'], 'value4')
    assert t[['z']] == 'value3'
    assert t[['z', 'x']] == 'value4'
    assert ['z'] not in tr.new_keys
    assert ['z'] not in tr.old_values
    assert ['z', 'x'] not in tr.new_keys
    assert ['z', 'x'] not in tr.old_values
    discard_with_transaction(t, ['z'], tr)
    discard_with_transaction(t, ['z', 'x'], tr)
    assert t[['z']] is None
    assert t[['z', 'x']] is None
    assert ['z'] not in tr.new_keys
    assert tr.old_values[['z']] == 'value3'
    assert ['z', 'x'] not in tr.new_keys
    assert tr.old_values[['z', 'x']] == 'value4'
    set_with_transaction(t, ['z'], 'value3', tr)
    set_with_transaction(t, ['z', 'x'], 'value4', tr)
    assert t[['z']] == 'value3'
    assert t[['z', 'x']] == 'value4'
    assert ['z'] not in tr.new_keys
    assert tr.old_values[['z']] == 'value3'
    assert ['z', 'x'] not in tr.new_keys
    assert tr.old_values[['z', 'x']] == 'value4'


def test_trie_insert_del_insert_different_existing_key_with_transaction():
    t = Trie()
    tr = Transaction()
    t.set(['x'], 'value1')
    t.set(['x', 'y'], 'value2')
    t.set(['z'], 'value3')
    t.set(['z', 'x'], 'value4')
    assert t[['z']] == 'value3'
    assert t[['z', 'x']] == 'value4'
    assert ['z'] not in tr.new_keys
    assert ['z'] not in tr.old_values
    assert ['z', 'x'] not in tr.new_keys
    assert ['z', 'x'] not in tr.old_values
    discard_with_transaction(t, ['z'], tr)
    discard_with_transaction(t, ['z', 'x'], tr)
    assert t[['z']] is None
    assert t[['z', 'x']] is None
    assert ['z'] not in tr.new_keys
    assert tr.old_values[['z']] == 'value3'
    assert ['z', 'x'] not in tr.new_keys
    assert tr.old_values[['z', 'x']] == 'value4'
    set_with_transaction(t, ['z'], 'value_change1', tr)
    set_with_transaction(t, ['z', 'x'], 'value_change2', tr)
    assert t[['z']] == 'value_change1'
    assert t[['z', 'x']] == 'value_change2'
    assert ['z'] not in tr.new_keys
    assert tr.old_values[['z']] == 'value3'
    assert ['z', 'x'] not in tr.new_keys
    assert tr.old_values[['z', 'x']] == 'value4'


def test_trie_key_insert_new_key_with_transaction():
    t = Trie()
    tr = Transaction()
    set_with_transaction(t, ['x'], 'value_x', tr)
    assert t[['x']] == 'value_x'
    assert ['x'] in tr.new_keys
    assert ['x'] not in tr.old_values


def test_trie_key_overwrite_new_key_with_transaction():
    t = Trie()
    tr = Transaction()
    set_with_transaction(t, ['x'], 'value_x', tr)
    set_with_transaction(t, ['x'], 'value_y', tr)
    assert t[['x']] == 'value_y'
    assert ['x'] in tr.new_keys
    assert ['x'] not in tr.old_values


def test_trie_nested_key_insert_new_key_with_transaction():
    t = Trie()
    tr = Transaction()
    set_with_transaction(t, ['x', 'y'], 'value_1', tr)
    assert t[['x', 'y']] == 'value_1'
    assert ['x', 'y'] in tr.new_keys
    assert ['x', 'y'] not in tr.old_values


def test_trie_nested_key_overwrite_new_key_with_transaction():
    t = Trie()
    tr = Transaction()
    set_with_transaction(t, ['x', 'y'], 'value_1', tr)
    set_with_transaction(t, ['x', 'y'], 'value_2', tr)
    assert t[['x', 'y']] == 'value_2'
    assert ['x', 'y'] in tr.new_keys
    assert ['x', 'y'] not in tr.old_values


def test_trie_key_insert_existing_key_with_transaction():
    t = Trie()
    t.set(['x'], 'value1')
    tr = Transaction()
    set_with_transaction(t, ['x'], 'value2', tr)
    assert t[['x']] == 'value2'
    assert ['x'] not in tr.new_keys
    assert tr.old_values[['x']] == 'value1'


def test_trie_key_overwrite_existing_key_with_transaction():
    t = Trie()
    t.set(['x'], 'value1')
    tr = Transaction()
    set_with_transaction(t, ['x'], 'value2', tr)
    set_with_transaction(t, ['x'], 'value3', tr)
    assert t[['x']] == 'value3'
    assert ['x'] not in tr.new_keys
    assert tr.old_values[['x']] == 'value1'


def test_trie_nested_key_insert_existing_key_with_transaction():
    t = Trie()
    t.set(['x', 'y'], 'value_1')
    tr = Transaction()
    set_with_transaction(t, ['x', 'y'], 'value_1', tr)
    assert t[['x', 'y']] == 'value_1'
    assert ['x', 'y'] not in tr.new_keys
    assert tr.old_values[['x', 'y']] == 'value_1'


def test_trie_nested_key_overwrite_existing_key_with_transaction():
    t = Trie()
    t.set(['x', 'y'], 'value1')
    tr = Transaction()
    set_with_transaction(t, ['x', 'y'], 'value2', tr)
    set_with_transaction(t, ['x', 'y'], 'value3', tr)
    assert t[['x', 'y']] == 'value3'
    assert ['x', 'y'] not in tr.new_keys
    assert tr.old_values[['x', 'y']] == 'value1'
