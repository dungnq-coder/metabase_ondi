from src.mapping.sql_rewriter import rewrite_query


def test_table_name_replaced_when_backticked():
    query = 'SELECT * FROM `old.tbl.a` WHERE 1=1'
    new_query, changed = rewrite_query(
        query,
        {'old.tbl.a': 'new.tbl.a'},
        rename={},
        spec_tables=set(),
    )
    assert '`new.tbl.a`' in new_query
    assert '`old.tbl.a`' not in new_query
    assert changed is False


def test_redundant_subquery_flattened():
    query = 'SELECT x FROM (SELECT * FROM `a.b.c`) t'
    new_query, _ = rewrite_query(query, {}, rename={}, spec_tables=set())
    assert 'FROM `a.b.c`' in new_query
    assert 'SELECT * FROM' not in new_query


def test_spec_table_triggers_rename_and_sets_changed_flag():
    query = (
        "SELECT * FROM `fortias-saga.singular.creative_data` WHERE app IN ('Fortias Saga Android')"
    )
    new_query, changed = rewrite_query(
        query,
        {},
        rename={"'Fortias Saga Android'": "'AND_Hero Blitz'"},
        spec_tables={'fortias-saga.singular.creative_data'},
    )
    assert "'AND_Hero Blitz'" in new_query
    assert changed is True


def test_rename_not_triggered_without_spec_table():
    query = "SELECT * FROM `other.t` WHERE x = 'Fortias Saga Android'"
    new_query, changed = rewrite_query(
        query,
        {},
        rename={"'Fortias Saga Android'": "'AND_Hero Blitz'"},
        spec_tables={'fortias-saga.singular.creative_data'},
    )
    assert 'Fortias Saga Android' in new_query
    assert changed is False


def test_aliases_stripped_except_dd():
    query = 'SELECT x AS `foo`, y AS `dd` FROM `t`'
    new_query, _ = rewrite_query(query, {}, rename={}, spec_tables=set())
    assert 'AS `foo`' not in new_query
    assert 'AS `dd`' in new_query


def test_unrelated_table_left_alone():
    query = 'SELECT * FROM `keep.me`'
    new_query, _ = rewrite_query(query, {'other.tbl': 'new.tbl'}, rename={}, spec_tables=set())
    assert new_query == 'SELECT * FROM `keep.me`'


def test_table_replacement_does_not_match_partial_substring():
    query = 'SELECT * FROM `prefix.old.tbl.a.suffix`'
    new_query, _ = rewrite_query(query, {'old.tbl.a': 'new.tbl.a'}, rename={}, spec_tables=set())
    assert new_query == 'SELECT * FROM `prefix.old.tbl.a.suffix`'
