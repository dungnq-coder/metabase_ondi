from src.mapping.field_mapper import (
    build_global_field_mapping,
    find_new_table_id,
    map_field_ids_by_table,
)


def test_map_field_ids_case_insensitive():
    old = [
        {'id': 1, 'name': 'UserId', 'table_id': 10},
        {'id': 2, 'name': 'EventDate', 'table_id': 10},
    ]
    new = [
        {'id': 100, 'name': 'userid', 'table_id': 20},
        {'id': 101, 'name': 'eventdate', 'table_id': 20},
    ]
    result = map_field_ids_by_table(old, new, 10, 20)
    assert result == {1: 100, 2: 101}


def test_map_field_ids_filters_by_table_id():
    old = [
        {'id': 1, 'name': 'a', 'table_id': 10},
        {'id': 2, 'name': 'a', 'table_id': 99},  # different table -> ignored
    ]
    new = [{'id': 100, 'name': 'a', 'table_id': 20}]
    result = map_field_ids_by_table(old, new, 10, 20)
    assert result == {1: 100}


def test_map_field_ids_missing_field_omitted():
    old = [
        {'id': 1, 'name': 'kept', 'table_id': 10},
        {'id': 2, 'name': 'missing', 'table_id': 10},
    ]
    new = [{'id': 100, 'name': 'kept', 'table_id': 20}]
    result = map_field_ids_by_table(old, new, 10, 20)
    assert result == {1: 100}


def test_find_new_table_id_exact_full_name():
    old_tables = [{'table_id': 10, 'table_name': 'proj1.schema.tbl'}]
    new_tables = [{'table_id': 20, 'table_name': 'proj2.schema.tbl'}]
    assert (
        find_new_table_id(10, old_tables, new_tables, {'proj1.schema.tbl': 'proj2.schema.tbl'})
        == 20
    )


def test_find_new_table_id_short_name_fallback():
    old_tables = [{'table_id': 10, 'table_name': 'proj1.schema.foo'}]
    new_tables = [{'table_id': 20, 'table_name': 'proj2.schema.bar'}]
    # mapping entry shares short name "foo" -> remaps to "bar"
    mapping = {'other.path.foo': 'proj2.schema.bar'}
    assert find_new_table_id(10, old_tables, new_tables, mapping) == 20


def test_find_new_table_id_no_mapping_uses_old_short_name():
    old_tables = [{'table_id': 10, 'table_name': 'proj1.schema.tbl'}]
    new_tables = [{'table_id': 20, 'table_name': 'proj2.other.tbl'}]
    assert find_new_table_id(10, old_tables, new_tables, {}) == 20


def test_find_new_table_id_cache_round_trip():
    old_tables = [{'table_id': 10, 'table_name': 'a.b.c'}]
    new_tables = [{'table_id': 20, 'table_name': 'x.y.c'}]
    cache: dict[int, int | None] = {}
    assert find_new_table_id(10, old_tables, new_tables, {}, cache=cache) == 20
    assert cache == {10: 20}
    # mutate cache -> next call honors cache, not source data
    cache[10] = 999
    assert find_new_table_id(10, old_tables, new_tables, {}, cache=cache) == 999


def test_find_new_table_id_unknown_old_id():
    assert find_new_table_id(404, [], [], {}) is None


def test_build_global_field_mapping_skips_unmappable_tables():
    old_tables = [
        {'table_id': 10, 'table_name': 'a.b.users'},
        {'table_id': 11, 'table_name': 'a.b.orphan'},
    ]
    new_tables = [{'table_id': 20, 'table_name': 'x.y.users'}]
    old_fields = [
        {'id': 1, 'name': 'col', 'table_id': 10},
        {'id': 2, 'name': 'col', 'table_id': 11},
    ]
    new_fields = [{'id': 100, 'name': 'col', 'table_id': 20}]
    result = build_global_field_mapping(old_tables, new_tables, old_fields, new_fields, {})
    assert result == {1: 100}
