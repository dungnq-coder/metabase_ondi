from datetime import datetime
from pprint import pprint

import pandas as pd

from core.base_config import BaseConfig
from src.connector.manager import MetabaseAPIManager

# ======================================================
#  Helpers
# ======================================================


def build_bullets(description: str, max_len: int = 255) -> str:
    """Chuyển text nhiều dòng thành bullet list + cắt độ dài."""
    lines = [line.strip() for line in description.splitlines() if line.strip()]
    bullets = '\n'.join(f'- {line}' for line in lines)

    return bullets if len(bullets) <= max_len else bullets[:max_len -
                                                           3] + '...'


def parse_date(raw_time) -> str | None:
    """Chuyển ngày dạng str hoặc Timestamp về ISO UTC."""
    try:
        if isinstance(raw_time, pd.Timestamp):
            dt = raw_time.to_pydatetime()
        else:
            dt = datetime.strptime(str(raw_time), '%Y-%m-%d')

        return dt.strftime('%Y-%m-%dT00:00:00Z')

    except Exception:
        print(f'⚠️ Invalid date format: {raw_time}')
        return None


def load_patch_notes(patch_note_url: str) -> pd.DataFrame:
    """Đọc CSV + chuẩn hóa + validate cơ bản."""
    df = pd.read_csv(patch_note_url).iloc[:, :3]
    df.columns = ['name', 'time', 'detail']

    df = df.dropna(how='all')
    df = df[df['time'] != 'Update time']
    return df.reset_index(drop=True)


# ======================================================
#  Timeline Event Logic
# ======================================================


def create_single_event(row, timeline_id: int, manager: MetabaseAPIManager):
    """Tạo 1 timeline event từ 1 row CSV."""
    timestamp = parse_date(row['time'])
    if not timestamp:
        return

    payload = manager.timeline_event.get_create_timeline_event_payload(
        timezone='UTC+07:00',
        timestamp=timestamp,
        name=row['name'],
        archived=False,
        timeline_id=timeline_id,
        source='collections',
        time_matters=True,
        description=build_bullets(row['detail']),
        icon='star')

    manager.timeline_event.post_timeline_event_action(payload=payload)
    print(f"✅ Created event '{row['name']}' at {timestamp}")


def add_timeline_event(timeline_id: int, patch_note_url: str,
                       manager: MetabaseAPIManager):
    df = load_patch_notes(patch_note_url)
    for _, row in df.iterrows():
        create_single_event(row, timeline_id, manager)


def clear_and_add_events(events: list[dict], timeline_id: int,
                         patch_note_url: str, manager: MetabaseAPIManager):
    """Xóa event cũ rồi tạo mới."""
    for ev in events:
        manager.timeline_event.delete_specific_timeline_event(
            timeline_event_id=ev['id'])

    add_timeline_event(timeline_id, patch_note_url, manager)


# ======================================================
#  Timeline CRUD
# ======================================================


def create_new_timeline(manager: MetabaseAPIManager, collection_id: int,
                        name: str, icon: str, description: str):
    payload = manager.timeline.get_update_timeline_payload(
        collection_id=collection_id,
        description=description,
        name=name,
        icon=icon)

    res = manager.timeline.post_timeline_action(payload=payload).json()
    print(
        f"✅ Created new timeline '{name}' (ID={res.get('id')}) in collection {collection_id}"
    )
    return res


def get_timeline_events(existing_timelines: list[dict], timeline_id: int):
    """Trả về danh sách event bên trong timeline_id."""
    for timeline in existing_timelines:
        if timeline.get('id') == timeline_id:
            return timeline.get('events', [])
    return None


# ======================================================
#  Main APIs (FS / SR)
# ======================================================


def add_events(config_pair: tuple, manager: MetabaseAPIManager,
               timeline_label: str):
    timeline_id, patch_note_url = config_pair

    timelines = manager.timeline.list_all_timeline_with_events().json()
    events = get_timeline_events(timelines, timeline_id)

    if events is None:
        print(f'⚠️ No {timeline_label} timeline found.')
        return

    clear_and_add_events(events, timeline_id, patch_note_url, manager)


def add_event_4_FS(config: BaseConfig, manager: MetabaseAPIManager):
    add_events(config.fs_timline_event, manager, 'FS')


def add_event_4_SR(config: BaseConfig, manager: MetabaseAPIManager):
    add_events(config.sr_timeline_event, manager, 'SR')
