from pybloom_live import BloomFilter

from src.connector.manager import MetabaseAPIManager
from core.base_config import BaseConfig

table_mapping = {
    "huynn_cs_character": "cs_character",
    "huynn_cs_support": "cs_support",
    "huynn_dh_active_daily": "huynn_sr_active_daily",
    "huynn_dh_campaign_progress": "huynn_sr_campaign_progress",
    "huynn_dh_resource_management_raw": "sr_resource_management_raw",
    "huynn_dh_resource_top_earn": "sr_resource_top_earn",
    "dh_banned_user": "cheat_ban",
    "dh_feature_max_stage": "sr_feature_max_stage",
}

ignored_tables = {
    "data_billing.gcp_billing_export_v1_01D065_6EF44D_70BCA6",
    "flattened_table.test_dh_ads",
    "huynn_temp_table.dh_user_flow",
}

def map_field_ids(old_fields: list[dict], new_fields: list[dict], error_rate=0.01) -> dict:
    """
    Map field IDs from old database to new database based on table_mapping or table_name.

    Args:
        old_fields (list[dict]): List of field objects from old DB.
        new_fields (list[dict]): List of field objects from new DB.
        error_rate (float): Bloom filter error rate.

    Returns:
        dict: Mapping of old_field_id -> new_field_id
    """
    # 1. Build bloom filter on new_fields using table_mapping + name
    bf = BloomFilter(capacity=len(new_fields), error_rate=error_rate)
    new_field_map = {}  # key = "mapped_table_name:name", value = new_id
    for f in new_fields:
        table_last = f['table_name']
        # áp dụng table_mapping nếu có
        mapped_table = {v: v for v in table_mapping.values()}.get(table_last, table_last)
        key = f"{mapped_table}:{f['name']}"
        bf.add(key)
        new_field_map[key] = f['id']

    # 2. Map old_field_id -> new_field_id
    mapping = {}
    for old in old_fields:
        old_table_last = old['table_name'].split('.')[-1]
        if old_table_last in ignored_tables:
            continue

        # Lấy tên bảng tương ứng trong SR
        mapped_table = table_mapping.get(old_table_last, old_table_last)
        key = f"{mapped_table}:{old['name']}"

        if key in bf:
            new_id = new_field_map.get(key)
            if new_id is not None:
                mapping[old['id']] = new_id

    return mapping

if __name__ == '__main__':
    config = BaseConfig()
    manager = MetabaseAPIManager(api_token=config.api_token, base_url=config.base_url)

    # Lấy field từ old DB và new DB
    old_fields = manager.database.get_fields_in_specific_db(3)
    new_fields = manager.database.get_fields_in_specific_db(105)

    # Kiểm tra field cụ thể theo ID
    found = [f for f in new_fields if f['id'] == 23901]
    if found:
        print("Found field ID 23901:", found[0])
    else:
        print("Field ID 23901 not found in DB 105.")

    # Kiểm tra field cụ thể theo name
    field_name_to_find = "value_iaa"
    found_by_name = [f for f in new_fields if f['name'] == field_name_to_find]
    if found_by_name:
        for f in found_by_name:
            print(f"Found by name: table={f['table_name']}, id={f['id']}, name={f['name']}")
    else:
        print(f"Field '{field_name_to_find}' not found in DB 105.")

    # Map field IDs dựa trên table_mapping + bloom filter
    mapping = map_field_ids(old_fields, new_fields)

    # Debug: in ra một số kết quả mapping
    print("\n=== Sample field mapping ===")
    for old_id, new_id in list(mapping.items()):
        old_field = next((f for f in old_fields if f['id'] == old_id), None)
        new_field = next((f for f in new_fields if f['id'] == new_id), None)
        if old_field and new_field:
            print(f"{old_field['table_name']}:{old_field['name']} -> {new_field['table_name']}:{new_field['name']}")
