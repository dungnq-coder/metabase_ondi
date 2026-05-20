def print_permissions_list(data: dict):
    if not data or 'groups' not in data:
        print('No permission data found.')
        return

    revision = data.get('revision', 'N/A')
    groups = data['groups']

    print(f'\nData Permissions (Revision: {revision})\n{"=" * 80}')

    for g_idx, (group_id, dbs) in enumerate(groups.items()):
        print(f'Group {group_id} [ID: {group_id}]')
        if not dbs:
            print('  No databases assigned.')
            continue

        db_keys = list(dbs.keys())
        for idx_db, db_id in enumerate(db_keys):
            perms = dbs[db_id]
            is_last_db = idx_db == len(db_keys) - 1
            db_branch = '└─' if is_last_db else '├─'
            sub_branch = '   ' if is_last_db else '│  '

            print(f'{db_branch} Database {db_id} [ID: {db_id}]')

            # Extract permissions
            can_query = 'query-builder-and-native' in perms.get('create-queries', '')
            view_data = perms.get('view-data', '')
            download = perms.get('download', {}).get('schemas', '')
            data_model = perms.get('data-model', {}).get('schemas', '')
            details = perms.get('details', '')

            # Map permissions to readable text
            query_text = 'Query + Native' if can_query else 'Query Builder Only'
            view_text = 'Full' if view_data == 'unrestricted' else 'Blocked / Sandboxed'
            download_text = 'Full' if download == 'full' else 'Limited / No'
            model_text = 'All' if data_model == 'all' else 'No'
            details_text = 'Yes' if details == 'yes' else 'No'

            # Print permission details under database
            print(f'{sub_branch}├─ Query Permission: {query_text}')
            print(f'{sub_branch}├─ View Data:       {view_text}')
            print(f'{sub_branch}├─ Download:        {download_text}')
            print(f'{sub_branch}├─ Edit Model:      {model_text}')
            print(f'{sub_branch}└─ DB Details:      {details_text}')

        if g_idx < len(groups) - 1:
            print('=' * 40)
    print('=' * 80)


def print_group_members_tree(group_data: dict):
    """
    Print group members in a tree structure with full details.

    Args:
        group_data (dict): Dictionary containing group info and member list.
                           Expected keys: 'name', 'id', 'members'
    """
    if not group_data:
        print('No group data provided.')
        return

    group_name = group_data.get('name', 'Unnamed Group')
    group_id = group_data.get('id', 'N/A')
    members = group_data.get('members', [])

    print(f'Group: {group_name} [ID: {group_id}]')

    if not members:
        print('  No members in this group.')
        return

    for idx, member in enumerate(members):
        # Determine tree branch symbols
        is_last = idx == len(members) - 1
        branch = '└─' if is_last else '├─'
        sub_branch = '   ' if is_last else '│  '

        # Member basic info
        name = f'{member.get("first_name", "")} {member.get("last_name", "")}'.strip()
        if not name:
            name = member.get('common_name', 'Unknown')
        email = member.get('email', 'N/A')
        superuser = 'Yes' if member.get('is_superuser', False) else 'No'
        manager = 'Yes' if member.get('is_group_manager', False) else 'No'
        user_id = member.get('user_id', 'N/A')

        print(f'{branch} {name}')
        print(f'{sub_branch} Email: {email}')
        print(f'{sub_branch} Superuser: {superuser}')
        print(f'{sub_branch} Manager: {manager}')
        print(f'{sub_branch} User ID: {user_id}')


def print_groups_list(groups: list):
    """
    Print a tree-style list of Metabase groups with detailed information.

    This function formats group information in a readable CLI-friendly way,
    consistent with other `print_*` functions.

    Each group includes:
        - Group name
        - Group ID
        - Member count
        - Group type (magic type)
        - Tenant flag
        - Entity ID (if available)

    Args:
        groups (list): A list of dictionaries, each representing a group.
                       Expected keys:
                           - id (int)
                           - name (str)
                           - member_count (int)
                           - magic_group_type (str or None)
                           - is_tenant_group (bool)
                           - entity_id (str or None)

    Example:
        [
            {"id": 1, "name": "All Users", "member_count": 6, "magic_group_type": "all-internal-users", ...},
            {"id": 2, "name": "Administrators", "member_count": 3, "magic_group_type": "admin", ...},
            {"id": 3, "name": "Data Team", "member_count": 2, ...}
        ]
    """
    if not groups:
        print('No group data available.')
        return

    print('\nUser Groups Overview')
    print('=' * 60)

    for idx, group in enumerate(groups):
        is_last = idx == len(groups) - 1
        branch = '└─' if is_last else '├─'
        sub_branch = '   ' if is_last else '│  '

        name = group.get('name', 'Unnamed Group')
        gid = group.get('id', 'N/A')
        members = group.get('member_count', 0)
        magic_type = group.get('magic_group_type', 'None')
        tenant = 'Yes' if group.get('is_tenant_group') else 'No'
        entity_id = group.get('entity_id', None)

        print(f'{branch} {name} [ID: {gid}]')
        print(f'{sub_branch} Members:        {members}')
        print(f'{sub_branch} Magic Type:     {magic_type}')
        print(f'{sub_branch} Tenant Group:   {tenant}')
        if entity_id:
            print(f'{sub_branch} Entity ID:      {entity_id}')

    print('=' * 60)


def print_db_permission_detail(data: dict):
    """
    Display detailed database permissions for all groups in a formatted and readable way.

    Args:
        data (dict): The permissions data returned from the Metabase API.

    Example structure:
        {
            "revision": 2,
            "groups": {
                "1": {
                    "1": {
                        "view-data": "unrestricted",
                        "download": {"schemas": "full"},
                        "create-queries": "query-builder-and-native"
                    }
                }
            }
        }
    """
    print('🔐 === DATABASE PERMISSIONS DETAIL ===\n')

    if not data or 'groups' not in data:
        print('⚠️  No permission data found.')
        return

    groups = data.get('groups', {})
    print(f'🧾 Revision: {data.get("revision", "N/A")}\n')

    # --- Iterate through groups ---
    for group_id, dbs in groups.items():
        print(f'👥 Group ID: {group_id}')
        print('   ├── Databases:')

        # --- Iterate through databases under this group ---
        for db_id, perms in dbs.items():
            print(f'   │   🗄️  Database ID: {db_id}')

            # --- Print each permission key and its value ---
            for key, value in perms.items():
                if isinstance(value, dict):
                    # Example: "download": {"schemas": "full"}
                    nested = ', '.join(f'{k}: {v}' for k, v in value.items())
                    print(f'   │       - {key}: {nested}')
                else:
                    print(f'   │       - {key}: {value}')

            print('   │')  # visual separator between databases

        print('   └── End of group\n')

    print('✅ End of permissions list.\n')
