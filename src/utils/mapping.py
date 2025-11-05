from pybloom_live import BloomFilter

# Full table name mapping
table_mapping = {
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

ignored_tables = {
    'data_billing.gcp_billing_export_v1_01D065_6EF44D_70BCA6',
    'flattened_table.test_dh_ads',
    'huynn_temp_table.dh_user_flow',
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


import re


def replace_table_names_in_query(query: str, table_mapping: dict) -> str:
    """
    Thay tên bảng trong query SQL dựa trên mapping đầy đủ.
    Ghi log các bảng được thay.
    """

    def log(msg):
        print(msg)

    new_query = query
    for old_full, new_full in table_mapping.items():
        # Chỉ thay đúng cụm `old_full` (giữa dấu `backtick`)
        pattern = re.escape(f'`{old_full}`')
        if re.search(pattern, new_query):
            new_query = re.sub(pattern, f'`{new_full}`', new_query)
            log(f'🔄 Replaced `{old_full}` → `{new_full}`')

    return new_query
