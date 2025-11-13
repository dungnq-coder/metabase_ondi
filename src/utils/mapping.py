import re

# Full table name mapping
table_mapping_sr = {
    'fortias-saga.flattened_table.huynn_cs_character':
    'sword-rouge-lite.flattened_table.cs_character',
    'fortias-saga.flattened_table.huynn_cs_support':
    'sword-rouge-lite.flattened_table.cs_support',
    'fortias-saga.flattened_table.character':
    'sword-rouge-lite.flattened_table.character',
    'fortias-saga.flattened_table.equipment':
    'sword-rouge-lite.flattened_table.equipment',
    'fortias-saga.flattened_table.huynn_dh_active_daily':
    'sword-rouge-lite.dashboard_table.huynn_sr_active_daily',
    'fortias-saga.flattened_table.huynn_dh_campaign_progress':
    'sword-rouge-lite.dashboard_table.huynn_sr_campaign_progress',
    'fortias-saga.flattened_table.huynn_dh_resource_management_raw':
    'sword-rouge-lite.flattened_table.sr_resource_management_raw',
    'fortias-saga.flattened_table.huynn_dh_resource_top_earn':
    'sword-rouge-lite.flattened_table.sr_resource_top_earn',
    'fortias-saga.flattened_table.in_app_purchase':
    'sword-rouge-lite.flattened_table.in_app_purchase',
    'fortias-saga.flattened_table.user_engagement':
    'sword-rouge-lite.flattened_table.user_engagement',
    'fortias-saga.huynn_temp_table.dh_banned_user':
    'sword-rouge-lite.flattened_table.cheat_ban',
    'fortias-saga.huynn_temp_table.dh_feature_max_stage':
    'sword-rouge-lite.dashboard_table.sr_feature_max_stage',
    'fortias-saga.huynn_temp_table.dh_iaa_dashboard':
    'sword-rouge-lite.dashboard_table.dh_iaa_dashboard',
    'fortias-saga.huynn_temp_table.dh_product_exposure':
    'sword-rouge-lite.dashboard_table.sr_product_exposure',
    'fortias-saga.flattened_table.huynn_dh_tutorial':
    'sword-rouge-lite.dashboard_table.huynn_sr_tutorial',
    'fortias-saga.huynn_temp_table.level_mode_summary':
    'sword-rouge-lite.dashboard_table.game_mode_summary',
    'fortias-saga.flattened_table.huynn_dh_resource_management_by_source':
    'sword-rouge-lite.flattened_table.sr_resource_management_by_source',
}

table_mapping_nw = {
    'fortias-saga.flattened_table.huynn_cs_character':
    'island-battle.dashboard_table.huynn_cs_character',
    'fortias-saga.flattened_table.huynn_cs_support':
    'island-battle.dashboard_table.huynn_cs_support',
    'fortias-saga.flattened_table.character':
    'fortias-saga.dwh_north_war.frb_character_*',
    'fortias-saga.flattened_table.equipment':
    'fortias-saga.dwh_north_war.frb_equipment_*',
    'fortias-saga.flattened_table.huynn_dh_active_daily':
    'island-battle.dashboard_table.huynn_is_active_daily',
    'fortias-saga.flattened_table.huynn_dh_campaign_progress':
    'island-battle.dashboard_table.huynn_is_campaign_progress',
    'fortias-saga.flattened_table.huynn_dh_resource_management_raw':
    'island-battle.dashboard_table.huynn_is_resource_management_raw',
    'fortias-saga.flattened_table.huynn_dh_resource_top_earn':
    'island-battle.dashboard_table.huynn_is_resource_top_earn',
    'fortias-saga.flattened_table.in_app_purchase':
    'fortias-saga.dwh_north_war.frb_in_app_purchase_*',
    'fortias-saga.flattened_table.user_engagement':
    'fortias-saga.dwh_north_war.frb_user_engagement_*',
    'fortias-saga.huynn_temp_table.dh_feature_max_stage':
    'island-battle.dashboard_table.is_feature_max_stage',
    'fortias-saga.huynn_temp_table.dh_iaa_dashboard':
    'island-battle.dashboard_table.is_iaa_dashboard',
    'fortias-saga.huynn_temp_table.dh_product_exposure':
    'island-battle.dashboard_table.is_product_exposure',
    'fortias-saga.flattened_table.huynn_dh_tutorial':
    'island-battle.dashboard_table.huynn_is_tutorial',
    'fortias-saga.huynn_temp_table.level_mode_summary':
    'island-battle.dashboard_table.is_level_mode_summary',
    'fortias-saga.huynn_temp_table.dh_iaa_placement_dashboard':
    'island-battle.dashboard_table.is_iaa_placement_dashboard',
    'fortias-saga.flattened_table.huynn_dh_resource_management_by_source':
    'island-battle.dashboard_table.huynn_is_resource_management_by_source',
}

ignored_tables = {
    'data_billing.gcp_billing_export_v1_01D065_6EF44D_70BCA6',
    'flattened_table.test_dh_ads',
    'huynn_temp_table.dh_user_flow',
}

spec_table = {
    'fortias-saga.singular.creative_data',
    'fortias-saga.singular.marketing_data'
}

rename_sr = {
    "('Fortias Saga Android', 'Fortias Saga iOS', 'Fortias Saga: Action Adventure')":
    "('AND_Hero Blitz','Hero Blitz_AOS','Hero Blitz_iOS')"
}

rename_nw = {
    "('Fortias Saga Android', 'Fortias Saga iOS', 'Fortias Saga: Action Adventure')":
    "('North War Android','com.bgg.island.battle')"
}


def map_field_ids_by_table_id(old_fields: list[dict], new_fields: list[dict],
                              old_table_id: int, new_table_id: int) -> dict:
    """
    Map field_id giữa 2 bảng có table_id cũ và mới.
    - So khớp dựa trên field name (không phân biệt hoa/thường)
    - Ghi log nếu có field không tìm thấy ở bảng mới
    """

    def log(msg):
        print(msg)

    # --- Lọc field thuộc về 2 bảng cụ thể ---
    old_fields_in_table = [
        f for f in old_fields if f['table_id'] == old_table_id
    ]
    new_fields_in_table = [
        f for f in new_fields if f['table_id'] == new_table_id
    ]

    # --- Tạo map tên → ID cho bảng mới ---
    new_field_name_map = {
        f['name'].lower(): f['id']
        for f in new_fields_in_table
    }

    mapping = {}
    not_found = []

    # --- Duyệt qua từng field ở bảng cũ ---
    for old in old_fields_in_table:
        old_name = old['name'].lower()
        new_id = new_field_name_map.get(old_name)

        if new_id:
            mapping[old['id']] = new_id
        else:
            not_found.append(old['name'])

    # --- Logging kết quả ---
    log(f'\n=== 🧩 Mapping fields for table_id {old_table_id}→ {new_table_id} ==='
        )
    log(f'✅ Mapped {len(mapping)} / {len(old_fields_in_table)} fields')

    if not_found:
        log(f"⚠️ Fields not found in new table ({len(not_found)}): {', '.join(not_found)}"
            )

    return mapping


def replace_table_names_in_query(query: str,
                                 table_mapping: dict,
                                 spec_table: set = spec_table,
                                 rename: dict = rename_sr) -> str:
    """
    Replace table names in a SQL query based on a full mapping dictionary.
    If the query contains any table names listed in `spec_table`, apply additional
    string replacements defined in the `rename` dictionary.
    Also removes alias patterns like: AS 'alias' or AS "alias".

    Args:
        query (str): The original SQL query string.
        table_mapping (dict): Mapping of old full table names → new full table names.
        spec_table (set): Set of special table names that trigger additional replacements.
        rename (dict): Mapping of old substrings → new substrings to replace in the query.

    Returns:
        str: The updated SQL query with replaced table names and renamed substrings.
    """

    def log(msg):
        print(msg)

    new_query = query
    change_db = False

    pattern_subquery = re.compile(
        r'FROM\s*\(\s*SELECT\s*\*\s*FROM\s*(`[^`]+`)\s*\)',
        re.IGNORECASE | re.DOTALL  # DOTALL để . khớp cả newline
    )

    matches = pattern_subquery.findall(new_query)
    for match in matches:
        # Dùng regex để replace trực tiếp, tránh lỗi khoảng trắng/newline
        new_query = re.sub(r'FROM\s*\(\s*SELECT\s*\*\s*FROM\s*' +
                           re.escape(match) + r'\s*\)',
                           f'FROM {match}',
                           new_query,
                           flags=re.IGNORECASE | re.DOTALL)
        log(f'✂️ Simplified redundant subquery: {match}')

    # --- Step 1: Replace table names ---
    for old_full, new_full in table_mapping.items():
        pattern = re.escape(
            f'`{old_full}`')  # Match exact table name inside backticks
        if re.search(pattern, new_query):
            new_query = re.sub(pattern, f'`{new_full}`', new_query)
            log(f'🔄 Replaced `{old_full}` → `{new_full}`')

    # --- Step 2: Apply rename mapping if contains special table ---
    if any(spec in new_query for spec in spec_table):
        log('✨ Query contains a spec_table — applying rename mapping...')
        for old_str, new_str in rename.items():
            if old_str in new_query:
                new_query = new_query.replace(old_str, new_str)
                change_db = True
                log(f'📝 Renamed text: {old_str} → {new_str} and change db {change_db}'
                    )

    # --- Step 3: Remove alias patterns like AS 'alias' or AS "alias" ---
    alias_pattern = r'\bAS\s+([`])[A-Za-z0-9_.]+?\1'
    if re.search(alias_pattern, new_query, re.IGNORECASE):
        new_query = re.sub(alias_pattern, '', new_query, flags=re.IGNORECASE)
        log('🚮 Removed alias patterns like AS `alias`')

    return new_query, change_db
