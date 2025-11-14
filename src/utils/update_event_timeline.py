from pprint import pprint
from src.connector.manager import MetabaseAPIManager
from core.base_config import BaseConfig
import pandas as pd
from datetime import datetime

def build_bullets(description: str, max_len: int = 255) -> str:
    """
    Chuyển text nhiều dòng thành bullets.
    - Mỗi dòng là 1 bullet
    - Gom lại thành 1 string
    - Cắt toàn bộ description nếu > max_len
    """
    lines = [line.strip() for line in description.splitlines() if line.strip()]
    bullets = [f"- {line}" for line in lines]
    full_desc = "\n".join(bullets)
    if len(full_desc) > max_len:
        full_desc = full_desc[:max_len-3] + "..."
    return full_desc

def add_timeline_event(timeline_id: int, patch_note_url: str, manager: MetabaseAPIManager):
    df = pd.read_csv(patch_note_url)
    df = df.iloc[:, [0, 1, 2]]
    df.columns = ["name", "time", "detail"]
    df = df.dropna(how="all")
    df = df[df["time"] != "Update time"]
    df = df.reset_index(drop=True)

    for _, row in df.iterrows():
        raw_time = row["time"]

        try:
            if isinstance(raw_time, pd.Timestamp):
                timestamp = raw_time.strftime("%Y-%m-%dT00:00:00Z")
            else:
                timestamp = datetime.strptime(str(raw_time), "%Y-%m-%d").strftime("%Y-%m-%dT00:00:00Z")
        except ValueError:
            print(f"⚠️ Skipping row with invalid date: {raw_time}")
            continue
    
        description = build_bullets(row["detail"], max_len=255)

        # --- Payload ---
        payload = manager.timeline_event.get_create_timeline_event_payload(
            timezone="UTC+07:00",
            timestamp=timestamp,
            name=row["name"],
            archived=False,
            timeline_id=timeline_id,
            source="collections",
            time_matters=True,
            description=description,
            icon="star"
        )

        res = manager.timeline_event.post_timeline_event_action(payload=payload)
        print(f"✅ Created timeline event for '{row['name']}' at {timestamp}")

def add_timeline_event_with_old_deletion(list_event: list[dict], manager: MetabaseAPIManager, timeline_id: int, patch_note_url: str):
    for list_timeline_event in list_event:
        timeline_event_id = list_timeline_event.get('id')
        manager.timeline_event.delete_specific_timeline_event(timeline_event_id=timeline_event_id)
    
    add_timeline_event(timeline_id=timeline_id, patch_note_url=patch_note_url, manager=manager)


def create_new_timeline(manager: MetabaseAPIManager, collection_id: int, name:str, icon: str, description: str):
    payload = manager.timeline.get_update_timeline_payload(
        collection_id=collection_id,
        description=description,
        name=name,
        icon=icon
    )

    res = manager.timeline.post_timeline_action(payload=payload).json()
    print(f"✅ Created new timeline '{name}' with ID: {res.get('id')} inside collection ID: {collection_id}")
    return res

config = BaseConfig()
manager = MetabaseAPIManager(api_token=config.api_token, base_url=config.base_url)

timeline_id = config.get('metabase.time_line_dh_id')
patch_note_url = config.get('gcp.dh_patch_note')

# payload = manager.timeline.get_update_timeline_payload(collection_id=40, name= "Sword Rougelite", description="Timeline for Sword Rougelite updates", icon="bell")

# manager.timeline.update_specific_timeline(timeline_id=timeline_id, payload=payload)

existing_timeline_and_timeline_events = manager.timeline.list_all_timeline_with_events().json()
FS_event_timeline = None

print(timeline_id)
for timeline in existing_timeline_and_timeline_events:
    print(f'check {timeline.get("name")} with id: {timeline.get("id")}')
    if timeline.get('id') == int(timeline_id):
        FS_event_timeline = timeline['events']
        break


add_timeline_event_with_old_deletion(timeline_id=timeline_id, patch_note_url=patch_note_url, manager=manager, list_event=FS_event_timeline)
