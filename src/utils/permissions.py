def format_permissions(item):
    return ' | '.join(
        [
            '📝 Write' if item.get('can_write') else '✏️ Read-only',
            '🗑️ Delete' if item.get('can_delete') else '🚫 Delete',
            '♻️ Restore' if item.get('can_restore') else '🚫 Restore',
        ]
    )
