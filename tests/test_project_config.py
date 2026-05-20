from pathlib import Path

import pytest

from src.config.project_config import ProjectConfigError, ProjectRegistry


def _make_registry(tmp_path: Path) -> ProjectRegistry:
    (tmp_path / '_global.yaml').write_text(
        'pivot_short_code: fs\nignored_tables: []\nspec_tables: []\n', encoding='utf-8'
    )
    (tmp_path / 'fs.yaml').write_text(
        'short_code: fs\ndisplay_name: FS\ntable_mapping: {}\nrename: {}\n',
        encoding='utf-8',
    )
    (tmp_path / 'sr.yaml').write_text(
        'short_code: sr\ndisplay_name: SR\n'
        "table_mapping: {fs.t.a: sr.t.a, fs.t.b: sr.t.b}\n"
        "rename: {\"'FS App'\": \"'SR App'\"}\n",
        encoding='utf-8',
    )
    (tmp_path / 'bl.yaml').write_text(
        'short_code: bl\ndisplay_name: BL\n'
        "table_mapping: {fs.t.a: bl.t.a}\n"
        "rename: {\"'FS App'\": \"'BL App'\"}\n",
        encoding='utf-8',
    )
    return ProjectRegistry.load(tmp_path)


def _write(tmp_path: Path, name: str, content: str) -> Path:
    p = tmp_path / name
    p.write_text(content, encoding='utf-8')
    return p


def test_load_real_repo_configs():
    projects_dir = Path(__file__).resolve().parent.parent / 'core' / 'projects'
    registry = ProjectRegistry.load(projects_dir)
    assert {p.short_code for p in registry.all()} == {'fs', 'sr', 'nw', 'bl'}
    assert registry.get('sr') is not None
    assert 'fortias-saga.singular.creative_data' in registry.spec_tables


def test_missing_dir_raises(tmp_path):
    with pytest.raises(ProjectConfigError):
        ProjectRegistry.load(tmp_path / 'nope')


def test_duplicate_short_code_raises(tmp_path):
    _write(tmp_path, 'a.yaml', 'short_code: dup\ndisplay_name: A\ntable_mapping: {}\n')
    _write(tmp_path, 'b.yaml', 'short_code: dup\ndisplay_name: B\ntable_mapping: {}\n')
    with pytest.raises(ProjectConfigError, match='Duplicate short_code'):
        ProjectRegistry.load(tmp_path)


def test_missing_required_key_raises(tmp_path):
    _write(tmp_path, 'x.yaml', 'short_code: x\n')
    with pytest.raises(ProjectConfigError, match='missing required keys'):
        ProjectRegistry.load(tmp_path)


def test_yaml_parse_error_raises(tmp_path):
    _write(tmp_path, 'broken.yaml', 'short_code: x\n  bad indent\n: ?\n')
    with pytest.raises(ProjectConfigError, match='YAML parse error'):
        ProjectRegistry.load(tmp_path)


def test_globals_default_when_missing(tmp_path):
    _write(
        tmp_path,
        'p.yaml',
        'short_code: p\ndisplay_name: P\ntable_mapping: {a: b}\nrename: {x: y}\n',
    )
    registry = ProjectRegistry.load(tmp_path)
    assert registry.ignored_tables == frozenset()
    assert registry.spec_tables == frozenset()
    p = registry.get('p')
    assert p is not None
    assert p.table_mapping == {'a': 'b'}
    assert p.rename == {'x': 'y'}


def test_global_file_loaded(tmp_path):
    _write(
        tmp_path,
        '_global.yaml',
        'ignored_tables: [a, b]\nspec_tables: [s1]\n',
    )
    _write(
        tmp_path,
        'p.yaml',
        'short_code: p\ndisplay_name: P\ntable_mapping: {}\n',
    )
    registry = ProjectRegistry.load(tmp_path)
    assert registry.ignored_tables == frozenset({'a', 'b'})
    assert registry.spec_tables == frozenset({'s1'})


def test_resolve_identity(tmp_path):
    r = _make_registry(tmp_path)
    res = r.resolve('sr', 'sr')
    assert res.table_mapping == {}
    assert res.rename == {}


def test_resolve_forward_from_pivot(tmp_path):
    r = _make_registry(tmp_path)
    res = r.resolve('fs', 'sr')
    assert res.table_mapping == {'fs.t.a': 'sr.t.a', 'fs.t.b': 'sr.t.b'}
    assert res.rename == {"'FS App'": "'SR App'"}


def test_resolve_reverse_to_pivot(tmp_path):
    r = _make_registry(tmp_path)
    res = r.resolve('sr', 'fs')
    assert res.table_mapping == {'sr.t.a': 'fs.t.a', 'sr.t.b': 'fs.t.b'}
    assert res.rename == {"'SR App'": "'FS App'"}


def test_resolve_cross_project_via_pivot(tmp_path):
    r = _make_registry(tmp_path)
    res = r.resolve('sr', 'bl')
    # sr.t.a <- fs.t.a -> bl.t.a chain
    assert res.table_mapping == {'sr.t.a': 'bl.t.a'}
    # sr.t.b has no bl counterpart -> dropped
    assert 'sr.t.b' not in res.table_mapping
    assert res.rename == {"'SR App'": "'BL App'"}


def test_resolve_unknown_short_code_raises(tmp_path):
    r = _make_registry(tmp_path)
    with pytest.raises(ProjectConfigError, match='Unknown source'):
        r.resolve('xx', 'fs')
    with pytest.raises(ProjectConfigError, match='Unknown target'):
        r.resolve('fs', 'xx')


def test_real_repo_fs_present():
    projects_dir = Path(__file__).resolve().parent.parent / 'core' / 'projects'
    r = ProjectRegistry.load(projects_dir)
    assert r.pivot_short_code == 'fs'
    assert r.get('fs') is not None
    # Inverse bl: 7 entries
    inv = r.resolve('bl', 'fs')
    assert len(inv.table_mapping) == 7
    assert 'pack-adventure.dashboard_table.bp_active_daily' in inv.table_mapping
    assert (
        inv.table_mapping['pack-adventure.dashboard_table.bp_active_daily']
        == 'fortias-saga.flattened_table.huynn_dh_active_daily'
    )


def test_resolve_short_code_direct_and_alias(tmp_path):
    _write(
        tmp_path,
        'fs.yaml',
        (
            'short_code: fs\ndisplay_name: FS\ntable_mapping: {}\n'
            'short_code_aliases: [fsd, fortiassaga]\n'
        ),
    )
    r = ProjectRegistry.load(tmp_path)
    assert r.resolve_short_code('fs') == 'fs'
    assert r.resolve_short_code('fsd') == 'fs'
    assert r.resolve_short_code('FSD') == 'fs'  # case-insensitive
    assert r.resolve_short_code('xx') is None


def test_duplicate_alias_across_projects_raises(tmp_path):
    _write(
        tmp_path,
        'a.yaml',
        'short_code: a\ndisplay_name: A\ntable_mapping: {}\nshort_code_aliases: [dup]\n',
    )
    _write(
        tmp_path,
        'b.yaml',
        'short_code: b\ndisplay_name: B\ntable_mapping: {}\nshort_code_aliases: [dup]\n',
    )
    with pytest.raises(ProjectConfigError, match='Alias'):
        ProjectRegistry.load(tmp_path)


def test_real_repo_fsd_alias_resolves():
    projects_dir = Path(__file__).resolve().parent.parent / 'core' / 'projects'
    r = ProjectRegistry.load(projects_dir)
    assert r.resolve_short_code('fsd') == 'fs'
