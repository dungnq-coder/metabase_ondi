from src.mapping.template_tags import (
    remap_field_ids,
    remap_template_tags_in,
    remap_template_tags_with_table_fallback,
    remove_unmapped_template_tags,
)


def test_remap_field_ids_simple():
    obj = ['field', 1, {'base-type': 'type/Integer'}]
    assert remap_field_ids(obj, {1: 100}) == ['field', 100, {'base-type': 'type/Integer'}]


def test_remap_field_ids_unknown_keeps_id():
    obj = ['field', 999, None]
    assert remap_field_ids(obj, {1: 100}) == ['field', 999, None]


def test_remap_field_ids_nested():
    obj = {'filter': ['=', ['field', 5, None], 1]}
    out = remap_field_ids(obj, {5: 500})
    assert out == {'filter': ['=', ['field', 500, None], 1]}


def test_remap_template_tags_in_replaces_dimensions():
    dq = {
        'native': {
            'template-tags': {
                'x': {'dimension': ['field', 7, None]},
            }
        }
    }
    remap_template_tags_in(dq, {7: 70})
    assert dq['native']['template-tags']['x']['dimension'] == ['field', 70, None]


def test_remove_unmapped_template_tags_keeps_unmapped(caplog):
    dq = {
        'native': {
            'template-tags': {
                'kept': {'dimension': ['field', 999, None]},
            }
        }
    }
    with caplog.at_level('WARNING'):
        remove_unmapped_template_tags(dq['native'], {})
    assert dq['native']['template-tags']['kept']['dimension'] == ['field', 999, None]
    assert any('unmapped field id 999' in r.message for r in caplog.records)


def test_table_fallback_resolves_by_name():
    dq = {
        'native': {
            'template-tags': {
                'dt': {
                    'name': 'event_date',
                    'dimension': ['field', 1, None],
                }
            }
        }
    }
    old_fields = [{'id': 1, 'name': 'event_date', 'table_id': 10}]
    new_fields = [{'id': 100, 'name': 'event_date', 'table_id': 20, 'base_type': 'type/Date'}]
    old_tables = [{'table_id': 10, 'table_name': 'a.b.t'}]
    new_tables = [{'table_id': 20, 'table_name': 'x.y.t'}]
    field_mapping: dict[int, int] = {}
    unresolved = remap_template_tags_with_table_fallback(
        dq,
        field_mapping,
        old_fields,
        new_fields,
        old_tables,
        new_tables,
        table_mapping={},
    )
    assert unresolved == []
    assert dq['native']['template-tags']['dt']['dimension'] == ['field', 100, None]
    assert field_mapping == {1: 100}


def test_date_field_heuristic_picks_when_no_direct_match():
    dq = {
        'native': {
            'template-tags': {
                'dt': {
                    'name': 'some_unknown',
                    'widget-type': 'date',
                    'dimension': ['field', 1, {'base-type': 'type/Date'}],
                }
            }
        }
    }
    old_fields = [{'id': 1, 'name': 'some_unknown', 'table_id': 10}]
    new_fields = [
        {'id': 50, 'name': 'something_else', 'table_id': 20, 'base_type': 'type/Text'},
        {'id': 100, 'name': 'event_date', 'table_id': 20, 'base_type': 'type/Date'},
    ]
    old_tables = [{'table_id': 10, 'table_name': 'a.b.t'}]
    new_tables = [{'table_id': 20, 'table_name': 'x.y.t'}]
    field_mapping: dict[int, int] = {}
    unresolved = remap_template_tags_with_table_fallback(
        dq, field_mapping, old_fields, new_fields, old_tables, new_tables, table_mapping={}
    )
    assert unresolved == []
    assert dq['native']['template-tags']['dt']['dimension'][1] == 100
