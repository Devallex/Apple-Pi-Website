from datetime import datetime, timezone


def now() -> datetime:
    return datetime.now(timezone.utc)


def now_iso() -> str:
    return now().isoformat()
