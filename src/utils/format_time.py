# src/utils/format_time.py
from datetime import datetime


def format_time(timestr):
    if not timestr:
        return '—'
    return datetime.fromisoformat(timestr.replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M:%S')
